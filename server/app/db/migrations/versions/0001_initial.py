"""SPR-04 initial schema: invite, token, usage_daily, spend_daily, idempotency, metric_daily.

No content column anywhere (D20); idempotency has no result column.

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_TS = sa.DateTime(timezone=True)
_TIER_CHECK = "tier IN ('free', 'pro')"


def upgrade() -> None:
    op.create_table(
        "invite",
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("max_uses", sa.Integer, nullable=False, server_default="1"),
        sa.Column("uses", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("revoked_at", _TS, nullable=True),
        sa.PrimaryKeyConstraint("code_hash", name="pk_invite"),
    )
    op.create_table(
        "token",
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("tier", sa.String(16), nullable=False, server_default="free"),
        sa.Column("invite_hash", sa.String(64), nullable=True),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("revoked_at", _TS, nullable=True),
        sa.CheckConstraint(_TIER_CHECK, name="ck_token_tier"),
        sa.PrimaryKeyConstraint("token_hash", name="pk_token"),
    )
    op.create_table(
        "usage_daily",
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("extractions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("provider_calls", sa.Integer, nullable=False, server_default="0"),
        sa.Column("image_calls", sa.Integer, nullable=False, server_default="0"),
        sa.Column("input_tokens", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.BigInteger, nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("token_hash", "day", name="pk_usage_daily"),
    )
    op.create_table(
        "spend_daily",
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("tier", sa.String(16), nullable=False),
        sa.Column("est_micro_usd", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("provider_calls", sa.BigInteger, nullable=False, server_default="0"),
        sa.CheckConstraint(_TIER_CHECK, name="ck_spend_daily_tier"),
        sa.PrimaryKeyConstraint("day", "tier", name="pk_spend_daily"),
    )
    op.create_table(
        "idempotency",
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", _TS, nullable=False),
        sa.Column("updated_at", _TS, nullable=False),
        sa.Column("expires_at", _TS, nullable=False),
        sa.CheckConstraint(
            "status IN ('in_flight', 'done', 'failed')", name="ck_idempotency_status"
        ),
        sa.PrimaryKeyConstraint("key_hash", name="pk_idempotency"),
    )
    op.create_index("ix_idempotency_token_hash", "idempotency", ["token_hash"])
    op.create_index("ix_idempotency_expires_at", "idempotency", ["expires_at"])
    op.create_table(
        "metric_daily",
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("dim", sa.String(64), nullable=False),
        sa.Column("n", sa.BigInteger, nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("day", "name", "dim", name="pk_metric_daily"),
    )


def downgrade() -> None:
    op.drop_table("metric_daily")
    op.drop_index("ix_idempotency_expires_at", table_name="idempotency")
    op.drop_index("ix_idempotency_token_hash", table_name="idempotency")
    op.drop_table("idempotency")
    op.drop_table("spend_daily")
    op.drop_table("usage_daily")
    op.drop_table("token")
    op.drop_table("invite")
