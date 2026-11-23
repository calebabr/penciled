"""Alembic environment. URL from DATABASE_URL (or a connection passed by tests);
the URL is never logged or printed."""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy.engine import Connection

from app.db.engine import make_engine
from app.db.schema import metadata

config = context.config


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    passed = config.attributes.get("connection")
    if isinstance(passed, Connection):
        _run(passed)
        return
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    engine = make_engine(url)
    try:
        with engine.connect() as connection:
            _run(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise SystemExit("offline (SQL script) mode is not supported; run against a database")
run_migrations_online()
