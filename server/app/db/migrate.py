"""Programmatic `alembic upgrade head` (used by tests and by `python -m app.db.migrate`)."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection

SERVER_DIR = Path(__file__).resolve().parents[2]


def alembic_config(connection: Connection | None = None) -> Config:
    cfg = Config(str(SERVER_DIR / "alembic.ini"))
    if connection is not None:
        cfg.attributes["connection"] = connection
    return cfg


def upgrade(connection: Connection | None = None, revision: str = "head") -> None:
    command.upgrade(alembic_config(connection), revision)


def downgrade(connection: Connection | None = None, revision: str = "base") -> None:
    command.downgrade(alembic_config(connection), revision)


if __name__ == "__main__":
    upgrade()
