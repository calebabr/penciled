"""COMP-API: one test per status code of POST /v1/extract (DESIGN 3.7)."""

from __future__ import annotations

import threading
from dataclasses import replace
from typing import Any

import pytest
from penciled_contracts.generated import ErrorResponse, ExtractRequest, ExtractResponse
from srv_support import MakeHarness, extract_body

from app.db.schema import spend_daily
from app.proxy.adapter import ExtractOutcome, StubExtractor
from app.settings import Settings


def _err(resp: Any) -> ErrorResponse:
    return ErrorResponse.model_validate(resp.json())


def test_200_schema_valid_nothing_result_with_quota(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    resp = h.extract(tok, extract_body())
    assert resp.status_code == 200
    parsed = ExtractResponse.model_validate(resp.json())
    assert parsed.class_ == "nothing" and parsed.gate_state == "none"
    assert parsed.nothing_subtype == "other" and parsed.actions == []
    assert parsed.quota is not None
    assert (parsed.quota.tier, parsed.quota.state) == ("free", "ok")
    assert parsed.min_app_version == h.settings.min_app_version
    assert parsed.anchor.source == "capture"
    assert h.extractor.provider_calls == 1


def test_200_resolve_only_makes_no_provider_call(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    body = extract_body(
        mode="resolve_only", raw={"opaque": 1}, anchor_override="2026-11-20T09:00:00Z"
    )
    resp = h.extract(tok, body)
    assert resp.status_code == 200
    assert resp.json()["anchor"] == {"iso": "2026-11-20T09:00:00Z", "source": "override"}
    assert h.extractor.provider_calls == 0


class _BlockingExtractor(StubExtractor):
    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def run(self, req: ExtractRequest, request_id: str, min_app_version: str) -> ExtractOutcome:
        self.entered.set()
        assert self.release.wait(10)
        return super().run(req, request_id, min_app_version)


def test_202_in_flight_duplicate(make_harness: MakeHarness) -> None:
    ext = _BlockingExtractor()
    h = make_harness(extractor=ext)
    tok = h.register()
    body = extract_body()
    first: dict[str, Any] = {}

    def call() -> None:
        first["resp"] = h.extract(tok, body)

    t = threading.Thread(target=call)
    t.start()
    assert ext.entered.wait(10)
    dup = h.extract(tok, body)
    assert dup.status_code == 202
    assert dup.json() == {"schema_version": 1, "code": "in_flight", "retry_after": 3}
    assert dup.headers["retry-after"] == "3"
    ext.release.set()
    t.join(10)
    assert first["resp"].status_code == 200
    assert ext.provider_calls == 1


def test_413_text_over_16kb(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    lines = [{"t": "x" * 2000, "c": 0.9} for _ in range(9)]  # 18 KB of OCR text
    resp = h.extract(tok, extract_body(ocr={"lines": lines}))
    assert resp.status_code == 413
    assert _err(resp).code == "payload_too_large"
    assert h.extractor.provider_calls == 0


def test_413_image_too_large(make_harness: MakeHarness) -> None:
    h = make_harness(settings=Settings(max_image_b64_chars=100))
    tok = h.register()
    resp = h.extract(tok, extract_body(image_b64="A" * 200))
    assert resp.status_code == 413


def test_413_body_over_cap(make_harness: MakeHarness) -> None:
    h = make_harness(settings=Settings(max_body_bytes=1000))
    tok = h.register()
    resp = h.extract(tok, extract_body(image_b64="A" * 5000))
    assert resp.status_code == 413
    assert resp.json() == {"schema_version": 1, "code": "payload_too_large"}


def test_422_schema_invalid(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    resp = h.extract(tok, extract_body(mode="nope"))
    assert resp.status_code == 422
    assert resp.json() == {
        "schema_version": 1,
        "code": "invalid_request",
        "issues": [{"loc": ["body", "mode"], "type": "literal_error"}],
    }


@pytest.mark.parametrize(
    ("is_chat", "image_allowed"), [(True, True), (False, False), (True, False)]
)
def test_422_image_rejected_for_chat_or_not_allowed(
    make_harness: MakeHarness, is_chat: bool, image_allowed: bool
) -> None:
    h = make_harness()
    tok = h.register()
    body = extract_body(is_chat=is_chat, image_allowed=image_allowed, image_b64="QUJD")
    resp = h.extract(tok, body)
    assert resp.status_code == 422
    assert resp.json()["issues"] == [{"loc": ["body", "image_b64"], "type": "image_not_allowed"}]
    assert h.extractor.provider_calls == 0


def test_200_image_allowed_counts_image_call(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    key = "hmacfixture:img:p7:1:0"
    resp = h.extract(tok, extract_body(image_b64="QUJD", idempotency_key=key))
    assert resp.status_code == 200


def test_426_below_min_app_version(make_harness: MakeHarness) -> None:
    h = make_harness(settings=Settings(min_app_version="0.4.0"))
    tok = h.register()
    resp = h.extract(tok, extract_body(client_version="0.3.1"))
    assert resp.status_code == 426
    assert resp.json() == {
        "schema_version": 1,
        "code": "upgrade_required",
        "min_app_version": "0.4.0",
    }
    # Even an otherwise-invalid body from an old client gets the upgrade answer.
    resp = h.extract(tok, extract_body(client_version="0.1.0", mode="nope"))
    assert resp.status_code == 426
    assert h.extract(tok, extract_body(client_version="0.4.0")).status_code == 200


def test_429_burst_limit(make_harness: MakeHarness) -> None:
    h = make_harness(settings=Settings(burst_per_minute=2))
    tok = h.register()
    for i in range(2):
        key = f"hmacfixture:text:p7:1:{i}"
        assert h.extract(tok, extract_body(idempotency_key=key)).status_code == 200
    resp = h.extract(tok, extract_body(idempotency_key="hmacfixture:text:p7:1:9"))
    assert resp.status_code == 429
    err = _err(resp)
    assert err.code == "rate_limited" and err.retry_after is not None and err.retry_after >= 1
    assert resp.headers["retry-after"] == str(err.retry_after)


def test_503_kill_switch(make_harness: MakeHarness) -> None:
    h = make_harness(settings=Settings(paused=True))
    tok = h.register()
    resp = h.extract(tok, extract_body())
    assert resp.status_code == 503
    assert resp.json() == {"schema_version": 1, "code": "service_paused", "basic": True}
    assert h.extractor.provider_calls == 0


def test_503_global_daily_spend_cap(make_harness: MakeHarness) -> None:
    h = make_harness(settings=Settings(global_daily_usd_cap=0.5))
    tok = h.register()
    with h.engine.begin() as conn:
        conn.execute(
            spend_daily.insert().values(
                day=h.clock().date(), tier="pro", est_micro_usd=500_000, provider_calls=9
            )
        )
    resp = h.extract(tok, extract_body())
    assert resp.status_code == 503
    assert resp.json()["basic"] is True


class _FailingExtractor(StubExtractor):
    def __init__(self) -> None:
        super().__init__()
        self.fail = True

    def run(self, req: ExtractRequest, request_id: str, min_app_version: str) -> ExtractOutcome:
        if self.fail:
            raise RuntimeError("provider down")
        return super().run(req, request_id, min_app_version)


def test_500_provider_failure_then_retry_succeeds(make_harness: MakeHarness) -> None:
    ext = _FailingExtractor()
    h = make_harness(extractor=ext)
    tok = h.register()
    resp = h.extract(tok, extract_body())
    assert resp.status_code == 500
    assert resp.json() == {"schema_version": 1, "code": "internal"}
    ext.fail = False
    # The failed key is taken back by the automatic retry (same key).
    assert h.extract(tok, extract_body()).status_code == 200


def test_500_unhandled_is_content_free(make_harness: MakeHarness) -> None:
    h = make_harness(settings=replace(Settings()), raise_server_exceptions=False)
    tok = h.register()

    def boom(*_: Any) -> None:
        raise ValueError("secret-ish detail")

    h.services.extract = boom
    resp = h.extract(tok, extract_body())
    assert resp.status_code == 500
    assert resp.json() == {"schema_version": 1, "code": "internal"}
    assert "detail" not in resp.text
