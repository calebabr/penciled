"""COMP-AUTH: opaque invite token, stored as sha256 only (DESIGN 3.6, SEC-TOKEN).

The raw token is returned once by /v1/register and never stored or logged.
`tier` is read from the token row only (D25); no request field can set it.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import get_args

import sqlalchemy as sa
from penciled_contracts.generated import Tier
from sqlalchemy.engine import Connection

from app.db.schema import invite, token

TOKEN_PREFIX = "pcl_"
INVITE_PREFIX = "inv_"
_TIERS: frozenset[str] = frozenset(get_args(Tier))


def hash_secret(value: str) -> str:
    """sha256 hex. Tokens and invite codes are 256/128-bit random, so no salt is needed."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_token() -> str:
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def new_invite_code() -> str:
    return INVITE_PREFIX + secrets.token_urlsafe(16)


def bearer_from_header(header: str | None) -> str | None:
    if not header:
        return None
    scheme, _, value = header.partition(" ")
    value = value.strip()
    if scheme.lower() != "bearer" or not value or len(value) > 256:
        return None
    return value


def _tier(value: object) -> Tier:
    return value if isinstance(value, str) and value in _TIERS else "free"  # type: ignore[return-value]


@dataclass(frozen=True)
class TokenRecord:
    token_hash: str
    tier: Tier


def lookup_token(conn: Connection, raw_token: str) -> TokenRecord | None:
    th = hash_secret(raw_token)
    row = conn.execute(
        sa.select(token.c.tier).where(token.c.token_hash == th, token.c.revoked_at.is_(None))
    ).first()
    if row is None:
        return None
    return TokenRecord(token_hash=th, tier=_tier(row.tier))


def create_invite(conn: Connection, code: str, now: datetime, max_uses: int = 1) -> None:
    conn.execute(
        invite.insert().values(code_hash=hash_secret(code), max_uses=max_uses, created_at=now)
    )


def register(conn: Connection, invite_code: str, now: datetime) -> tuple[str, Tier] | None:
    """Consume one use of the invite atomically and issue a token. None = invalid invite."""
    ch = hash_secret(invite_code)
    used = conn.execute(
        invite.update()
        .where(
            invite.c.code_hash == ch,
            invite.c.revoked_at.is_(None),
            invite.c.uses < invite.c.max_uses,
        )
        .values(uses=invite.c.uses + 1)
        .returning(invite.c.code_hash)
    ).first()
    if used is None:
        return None
    raw = new_token()
    th = hash_secret(raw)
    # tier is not set here: the column default ('free') applies (D25).
    conn.execute(token.insert().values(token_hash=th, invite_hash=ch, created_at=now))
    tier = conn.execute(sa.select(token.c.tier).where(token.c.token_hash == th)).scalar_one()
    return raw, _tier(tier)
