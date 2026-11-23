"""Schema check (D20, SEC-DEL-ALL): no content column in any table.

Introspects the MIGRATED database (not just the metadata), so a column added by a
hand-written migration is caught too. A column whose name contains a content-ish
fragment fails unless it is in ALLOWLIST with a reason, and allowlisted columns
must be integer counters. Blob/JSON-typed columns fail outright.
"""

from __future__ import annotations

import re

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.engine import Engine

from app.db.schema import metadata

CONTENT_FRAGMENTS = (
    "ocr",
    "text",
    "image",
    "img",
    "body",
    "title",
    "field",
    "result",
    "output",
    "prompt",
    "raw",
    "content",
    "json",
    "payload",
    "blob",
    "note",
    "summary",
    "location",
    "line",
    "message",
    "caption",
    "data",
    "model",
    "response",
    "request",
)

# (table, column) -> why it is not content. Allowlisted columns must be integers.
ALLOWLIST: dict[tuple[str, str], str] = {
    ("usage_daily", "image_calls"): "count of image escalations",
    ("usage_daily", "output_tokens"): "count of provider output tokens",
}

FORBIDDEN_TYPES = (sa.JSON, sa.LargeBinary, sa.PickleType)
EXPECTED_TABLES = {
    "invite",
    "token",
    "usage_daily",
    "spend_daily",
    "idempotency",
    "metric_daily",
    "alembic_version",
}


def find_content_columns(
    columns: list[tuple[str, str, sa.types.TypeEngine[object]]],
) -> list[str]:
    bad: list[str] = []
    for table, name, coltype in columns:
        lowered = name.lower()
        hits = [f for f in CONTENT_FRAGMENTS if re.search(f, lowered)]
        if isinstance(coltype, FORBIDDEN_TYPES):
            bad.append(f"{table}.{name}: blob/json type")
        if not hits:
            continue
        if (table, name) in ALLOWLIST:
            if not isinstance(coltype, sa.Integer):
                bad.append(f"{table}.{name}: allowlisted but not an integer counter")
            continue
        bad.append(f"{table}.{name}: name suggests content ({', '.join(hits)})")
    return bad


def _live_columns(engine: Engine) -> list[tuple[str, str, sa.types.TypeEngine[object]]]:
    insp = sa.inspect(engine)
    return [(t, c["name"], c["type"]) for t in insp.get_table_names() for c in insp.get_columns(t)]


def test_no_content_column_in_any_table(engine: Engine) -> None:
    cols = _live_columns(engine)
    assert {t for t, _, _ in cols} == EXPECTED_TABLES  # a new table needs a review here
    assert find_content_columns(cols) == []


def test_idempotency_has_no_result_column(engine: Engine) -> None:
    names = {c["name"] for c in sa.inspect(engine).get_columns("idempotency")}
    assert names == {"key_hash", "token_hash", "status", "created_at", "updated_at", "expires_at"}


def test_checker_catches_content_columns() -> None:
    samples = [
        ("idempotency", "result_json", sa.Text()),
        ("token", "ocr_text", sa.String()),
        ("usage_daily", "image_b64", sa.Text()),
        ("metric_daily", "dim_raw", sa.String()),
        ("x", "blob", sa.LargeBinary()),
        ("x", "extra", sa.JSON()),
        ("usage_daily", "image_calls", sa.String()),  # allowlisted name, wrong type
    ]
    bad = find_content_columns(samples)
    assert len({b.split(":")[0] for b in bad}) == len(samples), bad


def test_migrations_match_metadata(engine: Engine) -> None:
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), metadata)
    assert diff == []
