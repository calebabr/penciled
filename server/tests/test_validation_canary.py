"""Canary for hard rule 3 / D20.7: a 422 must not echo any part of the request,
in the response or in the logs. Bodies carry paths and error types only."""

from __future__ import annotations

import io
import logging

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from penciled_contracts.generated import ErrorResponse
from pydantic import BaseModel
from srv_support import Harness, extract_body

from app.logs import make_handler
from app.main import content_free_validation_handler

CANARY = "CANARY-ocr-text-7f3a9c"


class _Body(BaseModel):
    count: int
    note: str


def _client() -> TestClient:
    # A throwaway app with a typed route, sharing the production handler.
    test_app = FastAPI()
    test_app.add_exception_handler(RequestValidationError, content_free_validation_handler)  # type: ignore[arg-type]

    @test_app.post("/echo")
    async def echo(body: _Body) -> dict[str, str]:
        return {"ok": "yes"}

    return TestClient(test_app)


def _assert_envelope(body: dict[str, object]) -> None:
    parsed = ErrorResponse.model_validate(body)
    assert parsed.code == "invalid_request"
    assert parsed.schema_version == 1
    for issue in parsed.issues or []:
        assert set(issue.model_dump(by_alias=True)) == {"loc", "type"}


@pytest.fixture
def captured(caplog: pytest.LogCaptureFixture) -> io.StringIO:
    """Raw records (caplog) at DEBUG for every logger, plus the production formatter."""
    caplog.set_level(logging.DEBUG)
    stream = io.StringIO()
    handler = make_handler(stream)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger()
    root.addHandler(handler)
    yield stream
    root.removeHandler(handler)


def test_main_app_registers_handler() -> None:
    from app.main import app

    assert app.exception_handlers[RequestValidationError] is content_free_validation_handler


def test_422_does_not_echo_body() -> None:
    resp = _client().post("/echo", json={"count": CANARY, "note": CANARY, "extra": CANARY})
    assert resp.status_code == 422
    assert CANARY not in resp.text
    _assert_envelope(resp.json())
    assert resp.json()["issues"] == [{"loc": ["body", "count"], "type": "int_parsing"}]


def test_422_on_malformed_json_does_not_echo() -> None:
    raw = '{"count": "' + CANARY + '", broken'
    resp = _client().post("/echo", content=raw, headers={"content-type": "application/json"})
    assert resp.status_code == 422
    assert CANARY not in resp.text
    _assert_envelope(resp.json())


def test_422_on_wrong_type_list_does_not_echo() -> None:
    resp = _client().post("/echo", json=[CANARY, {"nested": CANARY}])
    assert resp.status_code == 422
    assert CANARY not in resp.text
    _assert_envelope(resp.json())


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda b: b.update(ocr={"lines": [{"t": CANARY, "c": CANARY}]}), id="bad-conf"
        ),
        pytest.param(lambda b: b.update(tz=CANARY + " /bad zone"), id="bad-tz"),
        pytest.param(lambda b: b.update(captured_at=CANARY), id="bad-ts"),
        pytest.param(lambda b: b.update(idempotency_key=CANARY), id="bad-key"),
        pytest.param(lambda b: b.update(ocr={"lines": [{"t": CANARY * 200, "c": 0.5}]}), id="long"),
        pytest.param(lambda b: b.update(counters=[{CANARY: 1, "name": CANARY}]), id="counters"),
        pytest.param(lambda b: b.update(raw=CANARY), id="raw-not-object"),
        pytest.param(lambda b: b.pop("ocr"), id="missing"),
    ],
)
def test_extract_422_canary_response_and_logs(
    harness: Harness, captured: io.StringIO, caplog: pytest.LogCaptureFixture, mutate: object
) -> None:
    token = harness.register()
    body = extract_body()
    body[CANARY] = CANARY  # unknown key: dropped, never echoed
    mutate(body)  # type: ignore[operator]
    resp = harness.extract(token, body)
    assert resp.status_code == 422
    assert CANARY not in resp.text
    _assert_envelope(resp.json())
    assert CANARY not in caplog.text
    assert CANARY not in captured.getvalue()
    assert "http" in captured.getvalue()  # the access log line did get written


def test_extract_422_malformed_json_canary(
    harness: Harness, captured: io.StringIO, caplog: pytest.LogCaptureFixture
) -> None:
    token = harness.register()
    raw = '{"ocr": {"lines": [{"t": "' + CANARY + '"'
    resp = harness.client.post(
        "/v1/extract",
        content=raw,
        headers={"Authorization": f"Bearer {token}", "content-type": "application/json"},
    )
    assert resp.status_code == 422
    assert resp.json()["issues"] == [{"loc": ["body"], "type": "json_invalid"}]
    assert CANARY not in resp.text
    assert CANARY not in caplog.text
    assert CANARY not in captured.getvalue()


def test_register_422_canary(
    harness: Harness, captured: io.StringIO, caplog: pytest.LogCaptureFixture
) -> None:
    resp = harness.client.post("/v1/register", json={"schema_version": 1, "invite_code": 7})
    assert resp.status_code == 422
    resp = harness.client.post("/v1/register", json={"schema_version": CANARY})
    assert resp.status_code == 422
    assert CANARY not in resp.text
    _assert_envelope(resp.json())
    assert CANARY not in caplog.text
    assert CANARY not in captured.getvalue()
