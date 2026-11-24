"""Request orchestration for /v1 (COMP-API): auth -> limits -> idempotency -> quota ->
provider adapter -> usage. Pure checks first; DB work runs in a worker thread.

Never logs request content: only enums, counts and ids (hard rule 3).
"""

from __future__ import annotations

import logging
import secrets
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import sqlalchemy as sa
from fastapi.responses import JSONResponse, Response
from penciled_contracts.generated import ExtractRequest, Tier

from app.auth.tokens import TokenRecord, bearer_from_header, lookup_token, register
from app.config import TierLimits
from app.db.engine import Database
from app.db.schema import metadata
from app.errors import error_response
from app.idemp import store as idem
from app.proxy.adapter import Extractor, ProviderError
from app.quota import service as quota
from app.settings import Settings, parse_version

logger = logging.getLogger("penciled.api")

IDEM_MEMORY_MISS = "idem_memory_miss"


def utcnow() -> datetime:
    return datetime.now(UTC)


def ocr_text_bytes(req: ExtractRequest) -> int:
    return sum(len(line.t.encode("utf-8")) for line in req.ocr.lines)


def precheck_raw(data: Any, settings: Settings) -> JSONResponse | None:
    """426 before full validation, so an old client gets ST-UPGRADE, not a 422."""
    if not isinstance(data, dict):
        return None
    cv = data.get("client_version")
    minimum = parse_version(settings.min_app_version)
    if isinstance(cv, str) and minimum is not None:
        got = parse_version(cv)
        if got is not None and got < minimum:
            return error_response("upgrade_required", min_app_version=settings.min_app_version)
    return None


def precheck(req: ExtractRequest, settings: Settings) -> JSONResponse | None:
    if req.image_b64 is not None and (req.is_chat or not req.image_allowed):
        # SEC-CHAT / SEC-MIN-IMAGE, enforced server-side too (DESIGN 3.7).
        return error_response(
            "invalid_request", issues=[{"loc": ["body", "image_b64"], "type": "image_not_allowed"}]
        )
    if ocr_text_bytes(req) > settings.max_text_bytes:
        return error_response("payload_too_large")
    if req.image_b64 is not None and len(req.image_b64) > settings.max_image_b64_chars:
        return error_response("payload_too_large")
    if req.image_b64 is not None and key_mode(req.idempotency_key) != "img":
        # An image call must carry the img key segment (D20), so it can never be stored
        # under, or served from, the text-only key.
        return error_response(
            "invalid_request", issues=[{"loc": ["body", "idempotency_key"], "type": "key_mode"}]
        )
    return None


def key_mode(idempotency_key: str) -> str:
    """The mode segment (text|img) of HMAC:mode:prompt_version:schema_version:rerun."""
    parts = idempotency_key.split(":")
    return parts[1] if len(parts) == 5 else ""


class Services:
    def __init__(
        self,
        settings: Settings,
        db: Database,
        limits: TierLimits,
        extractor: Extractor,
        clock: Callable[[], datetime] = utcnow,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.db = db
        self.limits = limits
        self.extractor = extractor
        self.clock = clock
        self.monotonic = monotonic
        self.cache = idem.ResultCache(
            timedelta(seconds=settings.idem_result_ttl_s), settings.idem_cache_max_entries
        )
        self.limiter = quota.BurstLimiter(settings.burst_per_minute)
        self._result_ttl = timedelta(seconds=settings.idem_result_ttl_s)
        self._lease = timedelta(seconds=settings.idem_inflight_lease_s)
        self._last_sweep: datetime | None = None

    # --- auth -----------------------------------------------------------------

    def authenticate(self, authorization: str | None) -> TokenRecord | None:
        raw = bearer_from_header(authorization)
        if raw is None:
            return None
        with self.db.engine.connect() as conn:
            return lookup_token(conn, raw)

    def register(self, invite_code: str) -> tuple[str, Tier] | None:
        with self.db.engine.begin() as conn:
            return register(conn, invite_code, self.clock())

    def delete_me(self, record: TokenRecord) -> None:
        """DELETE /v1/me: every row keyed by this token_hash, in every table, plus memory."""
        with self.db.engine.begin() as conn:
            for table in metadata.sorted_tables:
                if "token_hash" in table.c:
                    conn.execute(sa.delete(table).where(table.c.token_hash == record.token_hash))
        self.cache.purge_token(record.token_hash)
        self.limiter.forget(record.token_hash)
        logger.info("delete_me", extra={"event": "delete_me", "outcome": "ok"})

    # --- extract --------------------------------------------------------------

    def _maybe_sweep(self, now: datetime) -> None:
        interval = timedelta(seconds=self.settings.idem_sweep_interval_s)
        if self._last_sweep is not None and now - self._last_sweep < interval:
            return
        self._last_sweep = now
        with self.db.engine.begin() as conn:
            idem.sweep(conn, now)
        self.cache.sweep(now)

    def _ok(self, body: dict[str, Any], record: TokenRecord, count: int) -> JSONResponse:
        out = dict(body)
        state = quota.quota_state(count, record.tier, self.limits)
        out["quota"] = {"tier": record.tier, "state": state}
        return JSONResponse(status_code=200, content=out)

    def _log(self, outcome: str, record: TokenRecord, req: ExtractRequest) -> None:
        logger.info(
            "extract",
            extra={"event": "extract", "outcome": outcome, "tier": record.tier, "mode": req.mode},
        )

    def extract(self, record: TokenRecord, req: ExtractRequest) -> JSONResponse:
        retry = self.limiter.check(record.token_hash, self.monotonic())
        if retry is not None:
            self._log("rate_limited", record, req)
            return error_response("rate_limited", retry_after=retry)

        now = self.clock()
        day = now.date()
        self._maybe_sweep(now)
        kh = idem.key_hash(record.token_hash, req.idempotency_key)
        cap_micro = int(self.settings.global_daily_usd_cap * 1_000_000)

        with self.db.engine.begin() as conn:
            if self.settings.paused or quota.global_spend_micro_usd(conn, day) >= cap_micro:
                self._log("paused", record, req)
                return error_response("service_paused", basic=True)
            c = idem.claim(conn, self.cache, kh, record.token_hash, now, self._lease)
            if c.kind == "in_flight":
                self._log("in_flight", record, req)
                return error_response("in_flight", retry_after=self.settings.idem_retry_after_s)
            count = quota.extractions_today(conn, record.token_hash, day)
            if c.kind == "cached" and c.cached is not None:
                self._log("cached", record, req)
                return self._ok(c.cached, record, count)
            if req.mode == "extract" and quota.at_cap(count, record.tier, self.limits):
                idem.release(conn, kh)
                self._log("daily_cap", record, req)
                return error_response("service_paused", basic=True)
            if c.memory_miss:
                quota.bump_metric(conn, day, IDEM_MEMORY_MISS, "all")

        request_id = "req-" + secrets.token_hex(8)
        try:
            outcome = self.extractor.run(req, request_id, self.settings.min_app_version)
            body = outcome.response.to_json_dict()
        except Exception as exc:
            logger.error(
                "extract_failed",
                extra={
                    "event": "extract_failed",
                    "exc_type": type(exc).__name__,
                    "code": exc.kind if isinstance(exc, ProviderError) else "unexpected",
                },
            )
            with self.db.engine.begin() as conn:
                idem.finish(conn, kh, "failed", self.clock(), self._result_ttl)
            return provider_error_response(exc)
        body.pop("quota", None)  # quota is recomputed on every serve

        done_at = self.clock()
        self.cache.put(kh, record.token_hash, body, done_at)
        with self.db.engine.begin() as conn:
            idem.finish(conn, kh, "done", done_at, self._result_ttl)
            if req.mode == "extract":
                count = quota.record_extraction(
                    conn, record.token_hash, record.tier, day, outcome.usage, self.limits
                )
        self._log("ok", record, req)
        return self._ok(body, record, count)


def provider_error_response(exc: Exception) -> JSONResponse:
    """Provider failures (COMP-LLMPROXY). The key is already marked failed, so the
    client's next automatic attempt re-runs it; the proxy itself never retries."""
    if isinstance(exc, ProviderError):
        if exc.kind == "rate_limited":
            # Pass the provider's Retry-After through; the client honours it.
            return error_response("rate_limited", retry_after=exc.retry_after or 30)
        if exc.kind == "spend_cap":
            # Provider monthly cap (the $25 backstop): same as our own cap, ST-PAUSED.
            return error_response("service_paused", basic=True)
        if exc.kind == "bad_input":
            return error_response(
                "invalid_request",
                issues=[{"loc": ["body", "image_b64"], "type": "image_invalid"}],
            )
    return error_response("internal")


def no_content() -> Response:
    return Response(status_code=204)
