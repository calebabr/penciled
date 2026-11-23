from __future__ import annotations

from app.db.engine import normalize_url
from app.settings import Settings, parse_version


def test_parse_version() -> None:
    assert parse_version("0.3.1") == (0, 3, 1, 0)
    assert parse_version("1.2.3-beta.4") == (1, 2, 3, 0)
    assert parse_version("2") == (2, 0, 0, 0)
    assert parse_version("x") is None
    assert parse_version("0.10.0") > parse_version("0.9.9")  # type: ignore[operator]


def test_settings_from_env() -> None:
    s = Settings.from_env(
        {
            "PENCILED_MIN_APP_VERSION": "0.2.0",
            "PENCILED_PAUSED": "true",
            "PENCILED_GLOBAL_DAILY_USD_CAP": "2.5",
            "PENCILED_BURST_PER_MINUTE": "7",
        }
    )
    assert (s.min_app_version, s.paused, s.global_daily_usd_cap, s.burst_per_minute) == (
        "0.2.0",
        True,
        2.5,
        7,
    )
    assert s.database_url is None
    assert Settings.from_env({}).paused is False


def test_normalize_url() -> None:
    assert normalize_url("postgres://u@h/db") == "postgresql+psycopg://u@h/db"
    assert normalize_url("postgresql://u@h/db") == "postgresql+psycopg://u@h/db"
    assert normalize_url("postgresql+psycopg://u@h/db") == "postgresql+psycopg://u@h/db"


def test_health_needs_no_database() -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app

    client = TestClient(create_app(Settings(database_url=None)))
    assert client.get("/v1/health").json() == {"status": "ok", "schema_version": 1}
    # No database configured: a content-free 500, not a crash or a stack trace.
    client = TestClient(create_app(Settings(database_url=None)), raise_server_exceptions=False)
    resp = client.post("/v1/extract", headers={"Authorization": "Bearer pcl_x"}, json={})
    assert resp.status_code == 500
    assert resp.json() == {"schema_version": 1, "code": "internal"}
