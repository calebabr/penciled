"""COMP-LLMPROXY (AI-EXTRACT, AI-ESCALATE): one structured Claude Haiku 5.5 call
per /v1/extract request, behind the `Extractor` protocol.

- Frozen system prompt prompts/<version>/system.txt with cache_control on its
  (only, last) block; the volatile OCR text and image come after it.
- Structured output via output_config.format (the frozen model-facing schema) and
  output_config.effort (default "low"); thinking adaptive (model default) or
  disabled per config (SP-11 arm). No temperature/top_p/top_k, no prefill.
- 0 proxy retries (SDK max_retries=0): the device owns the <= 3 automatic calls
  per item (hard rule 8) and honours the Retry-After we pass through.
- Model output is untrusted: re-validated in full; anything invalid, truncated or
  refused becomes a "Needs a look" result and is never passed through.
- Usage: token counts, estimated micro-USD and latency only. Nothing here logs
  or stores prompt, OCR, image or model text.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections.abc import Callable
from typing import Any

import anthropic
from penciled_contracts.generated import ExtractRequest

from app.logs import quiet_provider_loggers
from app.proxy.adapter import ExtractOutcome, ProviderError, ProviderUsage
from app.proxy.config import ProviderConfig, TokenCounts, cost_micro_usd
from app.proxy.image import ImageInputError, preprocess_image_b64
from app.proxy.model_output import ExtractResult, ModelOutputInvalid, parse_model_text
from app.proxy.prompts import PromptBundle, load_prompt
from app.proxy.request_build import system_blocks, user_content
from app.proxy.shape import Versions, from_result, needs_look

logger = logging.getLogger("penciled.proxy")

DEFAULT_RETRY_AFTER_S = 30
SPEND_LIMIT_CODE = "enforced_spend_limit_reached"


def _retry_after_s(exc: anthropic.APIStatusError) -> int:
    headers = exc.response.headers
    for name, scale in (("retry-after-ms", 0.001), ("retry-after", 1.0)):
        raw = headers.get(name)
        if raw:
            try:
                return max(1, math.ceil(float(raw) * scale))
            except ValueError:
                continue
    return DEFAULT_RETRY_AFTER_S


def _is_spend_cap(exc: anthropic.APIStatusError) -> bool:
    body = exc.body
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            details = err.get("details")
            if isinstance(details, dict) and details.get("error_code") == SPEND_LIMIT_CODE:
                return True
    return False


def _usage_counts(msg: Any) -> TokenCounts:
    u = msg.usage
    return TokenCounts(
        input_tokens=int(u.input_tokens or 0),
        output_tokens=int(u.output_tokens or 0),
        cache_read_input_tokens=int(u.cache_read_input_tokens or 0),
        cache_creation_input_tokens=int(u.cache_creation_input_tokens or 0),
    )


class AnthropicExtractor:
    def __init__(
        self,
        cfg: ProviderConfig,
        client: anthropic.Anthropic | None = None,
        prompt: PromptBundle | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        quiet_provider_loggers()  # hard rule 3, whatever ANTHROPIC_LOG says
        self.cfg = cfg
        self.prompt = prompt or load_prompt(cfg.prompt_version)
        base = client if client is not None else anthropic.Anthropic()
        # Hard rule 8: the proxy never retries on its own.
        self._client = base.with_options(max_retries=0, timeout=cfg.timeout_s)
        self._timer = timer
        self._lock = threading.Lock()
        self.provider_calls = 0
        self.model = cfg.model
        self.prompt_version = self.prompt.version
        self.thresholds_version = cfg.thresholds_version
        self._system = system_blocks(self.prompt.system, cfg.cache_ttl)
        self._output_config: dict[str, Any] = {
            "effort": cfg.effort,
            "format": {"type": "json_schema", "schema": self.prompt.output_schema},
        }

    def _versions(self, min_app_version: str) -> Versions:
        return Versions(self.model, self.prompt_version, self.thresholds_version, min_app_version)

    def request_kwargs(self, req: ExtractRequest, image_jpeg_b64: str | None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.cfg.model,
            "max_tokens": self.cfg.max_tokens,
            "system": self._system,
            "messages": [{"role": "user", "content": user_content(req, image_jpeg_b64)}],
            "output_config": self._output_config,
        }
        if self.cfg.thinking == "disabled":
            kwargs["thinking"] = {"type": "disabled"}
        return kwargs

    def _log_call(self, outcome: str, mode: str, latency_ms: int, t: TokenCounts | None) -> None:
        extra: dict[str, Any] = {
            "event": "provider_call",
            "outcome": outcome,
            "mode": mode,
            "latency_ms": latency_ms,
        }
        if t is not None:
            extra.update(
                {
                    "input_tokens": t.input_tokens,
                    "output_tokens": t.output_tokens,
                    "cache_read_tokens": t.cache_read_input_tokens,
                    "cache_write_tokens": t.cache_creation_input_tokens,
                }
            )
        logger.info("provider_call", extra=extra)

    def _resolve_only(self, req: ExtractRequest, request_id: str, v: Versions) -> ExtractOutcome:
        # No LLM call (DESIGN 3.7). The echoed raw is untrusted too: re-validated.
        if req.raw is None:
            return ExtractOutcome(response=needs_look(req, request_id, v, hint=False))
        try:
            result = ExtractResult.model_validate(req.raw)
        except ValueError:
            return ExtractOutcome(response=needs_look(req, request_id, v, hint=False))
        return ExtractOutcome(response=from_result(req, result, request_id, v))

    def run(self, req: ExtractRequest, request_id: str, min_app_version: str) -> ExtractOutcome:
        v = self._versions(min_app_version)
        if req.mode == "resolve_only":
            return self._resolve_only(req, request_id, v)

        image: str | None = None
        if req.image_b64 is not None:
            try:
                image = preprocess_image_b64(req.image_b64, self.cfg.image)
            except ImageInputError:
                raise ProviderError("bad_input") from None
        mode = "img" if image is not None else "text"
        kwargs = self.request_kwargs(req, image)

        with self._lock:
            self.provider_calls += 1
        t0 = self._timer()
        try:
            msg = self._client.messages.create(**kwargs)
        except anthropic.RateLimitError as exc:
            outcome = "spend_cap" if _is_spend_cap(exc) else "rate_limited"
            self._log_call(outcome, mode, self._ms(t0), None)
            if outcome == "spend_cap":
                raise ProviderError("spend_cap") from None
            raise ProviderError("rate_limited", retry_after=_retry_after_s(exc)) from None
        except anthropic.APIStatusError as exc:
            if exc.status_code == 529 or isinstance(exc, anthropic.OverloadedError):
                kind: Any = "overloaded"
            elif exc.status_code >= 500:
                kind = "upstream"
            else:
                kind = "rejected"
            self._log_call(kind, mode, self._ms(t0), None)
            raise ProviderError(kind) from None
        except anthropic.APITimeoutError:
            self._log_call("timeout", mode, self._ms(t0), None)
            raise ProviderError("timeout") from None
        except anthropic.APIConnectionError:
            self._log_call("connection", mode, self._ms(t0), None)
            raise ProviderError("connection") from None
        latency = self._ms(t0)

        counts = _usage_counts(msg)
        usage = ProviderUsage(
            provider_calls=1,
            image_calls=int(image is not None),
            input_tokens=counts.prompt_tokens,
            output_tokens=counts.output_tokens,
            est_micro_usd=cost_micro_usd(counts, self.cfg.pricing, self.cfg.cache_ttl),
            cache_read_input_tokens=counts.cache_read_input_tokens,
            cache_creation_input_tokens=counts.cache_creation_input_tokens,
            latency_ms=latency,
        )

        if msg.stop_reason == "refusal":
            # Haiku 5.5 has no server-side fallback: a refusal is a "Needs a look" card.
            self._log_call("refusal", mode, latency, counts)
            return ExtractOutcome(needs_look(req, request_id, v, hint=False), usage)
        if msg.stop_reason == "max_tokens":
            self._log_call("truncated", mode, latency, counts)
            return ExtractOutcome(needs_look(req, request_id, v, hint=True), usage)
        # Read blocks by type: a response can begin with thinking blocks.
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        try:
            result = parse_model_text(text)
        except ModelOutputInvalid as exc:
            self._log_call(exc.reason, mode, latency, counts)
            return ExtractOutcome(needs_look(req, request_id, v, hint=True), usage)
        self._log_call("ok", mode, latency, counts)
        return ExtractOutcome(from_result(req, result, request_id, v), usage)

    def _ms(self, t0: float) -> int:
        return max(0, round((self._timer() - t0) * 1000))
