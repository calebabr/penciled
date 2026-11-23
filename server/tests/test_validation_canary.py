"""Canary for hard rule 3: a 422 must not echo any part of the request."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import content_free_validation_handler

CANARY = "CANARY-ocr-text-7f3a9c"


class _Body(BaseModel):
    count: int
    note: str


def _client() -> TestClient:
    # A throwaway app with a typed route, sharing the production handler.
    from fastapi.exceptions import RequestValidationError

    test_app = FastAPI()
    test_app.add_exception_handler(RequestValidationError, content_free_validation_handler)  # type: ignore[arg-type]

    @test_app.post("/echo")
    async def echo(body: _Body) -> dict[str, str]:
        return {"ok": "yes"}

    return TestClient(test_app)


def test_main_app_registers_handler() -> None:
    from fastapi.exceptions import RequestValidationError

    from app.main import app

    assert app.exception_handlers[RequestValidationError] is content_free_validation_handler


def test_422_does_not_echo_body() -> None:
    resp = _client().post("/echo", json={"count": CANARY, "note": CANARY, "extra": CANARY})
    assert resp.status_code == 422
    assert resp.json() == {"error": "invalid_request"}
    assert CANARY not in resp.text


def test_422_on_malformed_json_does_not_echo() -> None:
    raw = '{"count": "' + CANARY + '", broken'
    resp = _client().post("/echo", content=raw, headers={"content-type": "application/json"})
    assert resp.status_code == 422
    assert CANARY not in resp.text
    assert resp.json() == {"error": "invalid_request"}


def test_422_on_wrong_type_list_does_not_echo() -> None:
    resp = _client().post("/echo", json=[CANARY, {"nested": CANARY}])
    assert resp.status_code == 422
    assert CANARY not in resp.text
