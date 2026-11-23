"""Engine creation and small dialect-portable helpers (Postgres in prod and CI;
SQLite in-memory is a local-only test fallback, so SQL here stays portable)."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.pool import StaticPool


class DatabaseNotConfigured(RuntimeError):
    """DATABASE_URL is not set (the message never contains a URL)."""


def normalize_url(url: str) -> str:
    """Hosts hand out postgres:// or postgresql://; we always use the psycopg 3 driver."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def make_engine(url: str) -> Engine:
    url = normalize_url(url)
    if url.startswith("sqlite"):
        return sa.create_engine(
            url, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
    # echo stays off: SQL parameters must never reach logs.
    return sa.create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5, echo=False)


class Database:
    """Lazily created engine, so the app (and /v1/health) starts without a database."""

    def __init__(self, url: str | None) -> None:
        self._url = url
        self._engine: Engine | None = None
        self._lock = threading.Lock()

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    if not self._url:
                        raise DatabaseNotConfigured("database is not configured")
                    self._engine = make_engine(self._url)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()


def as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; everything we store is UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _insert(conn: Connection, table: sa.Table) -> Any:
    if conn.dialect.name == "postgresql":
        return postgresql.insert(table)
    if conn.dialect.name == "sqlite":
        return sqlite.insert(table)
    raise RuntimeError("unsupported database dialect")


def upsert_add(
    conn: Connection, table: sa.Table, keys: dict[str, Any], increments: dict[str, int]
) -> None:
    """INSERT keys+increments, or add the increments to the existing row."""
    stmt = _insert(conn, table).values(**keys, **increments)
    stmt = stmt.on_conflict_do_update(
        index_elements=list(keys),
        set_={k: table.c[k] + stmt.excluded[k] for k in increments},
    )
    conn.execute(stmt)


def insert_ignore(conn: Connection, table: sa.Table, values: dict[str, Any]) -> bool:
    """INSERT ... ON CONFLICT DO NOTHING. True if a row was inserted."""
    pk = list(table.primary_key.columns)
    stmt = _insert(conn, table).values(**values).on_conflict_do_nothing().returning(*pk)
    # RETURNING, not rowcount: some Postgres-compatible servers omit command-tag counts.
    return conn.execute(stmt).first() is not None
