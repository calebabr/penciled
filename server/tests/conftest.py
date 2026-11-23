"""Test database and app fixtures.

DB selection (DB approach for SPR-04):
- TEST_DATABASE_URL set -> that Postgres (CI: postgres:16 service container;
  locally: e.g. a PGlite socket server, see server/STATUS.md). A dedicated
  variable, never DATABASE_URL, so tests can never wipe a real database.
- unset -> SQLite in-memory (local fallback only; the SQL stays portable).
- PENCILED_REQUIRE_POSTGRES=1 (set in CI) fails the run if Postgres is not in use.

The schema is always created by the Alembic migrations, not by metadata.create_all.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import replace

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from srv_support import FakeClock, Harness, MakeHarness, SharedDatabase

from app.config import TierLimits, load_tier_limits
from app.db import migrate
from app.db.engine import make_engine
from app.db.schema import metadata
from app.main import create_app
from app.proxy.adapter import StubExtractor
from app.settings import Settings


def _test_url() -> str:
    return os.environ.get("TEST_DATABASE_URL") or "sqlite+pysqlite:///:memory:"


def _reset(engine: Engine) -> None:
    with engine.begin() as conn:
        for table in reversed(metadata.sorted_tables):
            conn.execute(sa.text(f'DROP TABLE IF EXISTS "{table.name}"'))
        conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version"))


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    eng = make_engine(_test_url())
    if os.environ.get("PENCILED_REQUIRE_POSTGRES") == "1" and eng.dialect.name != "postgresql":
        pytest.fail("PENCILED_REQUIRE_POSTGRES=1 but TEST_DATABASE_URL is not a Postgres URL")
    _reset(eng)
    with eng.begin() as conn:
        migrate.upgrade(conn)
    yield eng
    _reset(eng)
    eng.dispose()


@pytest.fixture(autouse=True)
def _clean(request: pytest.FixtureRequest) -> Iterator[None]:
    yield
    if "engine" in request.fixturenames:
        eng: Engine = request.getfixturevalue("engine")
        with eng.begin() as conn:
            for table in reversed(metadata.sorted_tables):
                conn.execute(table.delete())


@pytest.fixture
def make_harness(engine: Engine) -> MakeHarness:
    def _make(
        settings: Settings | None = None,
        limits: TierLimits | None = None,
        extractor: StubExtractor | None = None,
        raise_server_exceptions: bool = True,
    ) -> Harness:
        s = settings or Settings()
        s = replace(s, database_url="unused")
        ext = extractor or StubExtractor()
        clock = FakeClock()
        app = create_app(
            s,
            limits=limits or load_tier_limits(),
            extractor=ext,
            db=SharedDatabase(engine),
            clock=clock,
        )
        client = TestClient(app, raise_server_exceptions=raise_server_exceptions)
        return Harness(client, engine, ext, clock, s, app.state.services)

    return _make


@pytest.fixture
def harness(make_harness: MakeHarness) -> Harness:
    return make_harness()
