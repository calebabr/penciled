"""COMP-SERVERDB: the whole server schema (DESIGN 3.4), as SQLAlchemy Core tables.

Hard rule (D20, SEC-REST-SERVER): no table has a column for screenshot content,
OCR text, extracted fields or model output. Idempotency RESULTS live only in
process memory (app/idemp); the `idempotency` table holds key hash, token hash,
status and timestamps. tests/test_schema_check.py enforces this by introspection.

Alembic migrations in app/db/migrations are the source of truth for the live
database; tests assert this metadata and the migrated schema stay identical.
"""

from __future__ import annotations

import sqlalchemy as sa

TIERS = ("free", "pro")
IDEM_STATUSES = ("in_flight", "done", "failed")

metadata = sa.MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "pk": "pk_%(table_name)s",
    }
)

_TS = sa.DateTime(timezone=True)
_HASH = sa.String(64)  # sha256 hex
_TIER_CHECK = "tier IN ('free', 'pro')"

# One row per invite code (stored hashed). Issued by `python -m app.admin add-invite`.
invite = sa.Table(
    "invite",
    metadata,
    sa.Column("code_hash", _HASH, primary_key=True),
    sa.Column("max_uses", sa.Integer, nullable=False, server_default="1"),
    sa.Column("uses", sa.Integer, nullable=False, server_default="0"),
    sa.Column("created_at", _TS, nullable=False),
    sa.Column("revoked_at", _TS, nullable=True),
)

# COMP-AUTH: opaque bearer token, stored as sha256 only. tier is server-controlled (D25).
token = sa.Table(
    "token",
    metadata,
    sa.Column("token_hash", _HASH, primary_key=True),
    sa.Column("tier", sa.String(16), nullable=False, server_default="free"),
    sa.Column("invite_hash", _HASH, nullable=True),
    sa.Column("created_at", _TS, nullable=False),
    sa.Column("revoked_at", _TS, nullable=True),
    sa.CheckConstraint(_TIER_CHECK, name="tier"),
)

# COMP-QUOTA: counts only, per token per UTC day.
usage_daily = sa.Table(
    "usage_daily",
    metadata,
    sa.Column("token_hash", _HASH, primary_key=True),
    sa.Column("day", sa.Date, primary_key=True),
    sa.Column("extractions", sa.Integer, nullable=False, server_default="0"),
    sa.Column("provider_calls", sa.Integer, nullable=False, server_default="0"),
    sa.Column("image_calls", sa.Integer, nullable=False, server_default="0"),
    sa.Column("input_tokens", sa.BigInteger, nullable=False, server_default="0"),
    sa.Column("output_tokens", sa.BigInteger, nullable=False, server_default="0"),
)

# COMP-QUOTA global $ estimate, per tier (D25: a later per-tier budget split needs no
# schema change). No token column: it survives DELETE /v1/me, so deleting a token
# cannot reset the global spend estimate.
spend_daily = sa.Table(
    "spend_daily",
    metadata,
    sa.Column("day", sa.Date, primary_key=True),
    sa.Column("tier", sa.String(16), primary_key=True),
    sa.Column("est_micro_usd", sa.BigInteger, nullable=False, server_default="0"),
    sa.Column("provider_calls", sa.BigInteger, nullable=False, server_default="0"),
    sa.CheckConstraint(_TIER_CHECK, name="tier"),
)

# COMP-IDEMP: status only. There is deliberately NO result column (D20.2).
idempotency = sa.Table(
    "idempotency",
    metadata,
    sa.Column("key_hash", _HASH, primary_key=True),
    sa.Column("token_hash", _HASH, nullable=False, index=True),
    sa.Column("status", sa.String(16), nullable=False),
    sa.Column("created_at", _TS, nullable=False),
    sa.Column("updated_at", _TS, nullable=False),
    sa.Column("expires_at", _TS, nullable=False, index=True),
    sa.CheckConstraint("status IN ('in_flight', 'done', 'failed')", name="status"),
)

# F8 / SEC-PRICING-METRICS: unlinkable count-only aggregates. No token column.
metric_daily = sa.Table(
    "metric_daily",
    metadata,
    sa.Column("day", sa.Date, primary_key=True),
    sa.Column("name", sa.String(64), primary_key=True),
    sa.Column("dim", sa.String(64), primary_key=True),
    sa.Column("n", sa.BigInteger, nullable=False, server_default="0"),
)
