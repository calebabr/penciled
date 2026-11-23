"""Shared test helpers (imported by conftest and the tests; unique module name on purpose)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from app.auth.tokens import create_invite, new_invite_code
from app.db.engine import Database
from app.proxy.adapter import StubExtractor
from app.settings import Settings

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "shared" / "fixtures"


class SharedDatabase(Database):
    """Database wrapper over the session engine (no dispose between tests)."""

    def __init__(self, engine: Engine) -> None:
        super().__init__("unused")
        self._engine = engine

    def dispose(self) -> None:
        pass


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 23, 15, 0, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kw: float) -> None:
        self.now = self.now + timedelta(**kw)


@dataclass
class Harness:
    client: TestClient
    engine: Engine
    extractor: StubExtractor
    clock: FakeClock
    settings: Settings
    services: Any

    def invite(self, uses: int = 1) -> str:
        code = new_invite_code()
        with self.engine.begin() as conn:
            create_invite(conn, code, self.clock(), max_uses=uses)
        return code

    def register(self) -> str:
        resp = self.client.post(
            "/v1/register", json={"schema_version": 1, "invite_code": self.invite()}
        )
        assert resp.status_code == 200, resp.status_code
        token: str = resp.json()["token"]
        return token

    def extract(self, token: str | None, body: dict[str, Any]) -> Any:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.post("/v1/extract", json=body, headers=headers)


MakeHarness = Callable[..., Harness]


def extract_body(**overrides: Any) -> dict[str, Any]:
    raw = json.loads((FIXTURES / "extract_request_basic.json").read_text("utf-8"))
    body: dict[str, Any] = raw["input"]
    body.update(overrides)
    return body
