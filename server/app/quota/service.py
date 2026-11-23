"""COMP-QUOTA: per-token daily limit from tier_limits config, global daily $ estimate
(per tier), shadow-threshold counting, and a per-token burst limiter (429)."""

from __future__ import annotations

import math
import threading
from collections import deque
from datetime import date

import sqlalchemy as sa
from penciled_contracts.generated import QuotaState, Tier
from sqlalchemy.engine import Connection

from app.config import TierLimits
from app.db.engine import upsert_add
from app.db.schema import metric_daily, spend_daily, usage_daily
from app.proxy.adapter import ProviderUsage

# Server-side count of "would have exceeded the shadow threshold" (D25), dim = tier.
# Named apart from the client's shadow_cap_hit event so the two are never summed.
SHADOW_METRIC = "shadow_cap_hit_srv"


def extractions_today(conn: Connection, token_hash: str, day: date) -> int:
    n = conn.execute(
        sa.select(usage_daily.c.extractions).where(
            usage_daily.c.token_hash == token_hash, usage_daily.c.day == day
        )
    ).scalar_one_or_none()
    return int(n or 0)


def quota_state(count: int, tier: Tier, limits: TierLimits) -> QuotaState:
    limit = limits.for_tier(tier).daily_limit
    if count >= limit:
        return "exhausted"
    if count >= math.ceil(limits.near_fraction * limit):
        return "near"
    return "ok"


def at_cap(count: int, tier: Tier, limits: TierLimits) -> bool:
    return count >= limits.for_tier(tier).daily_limit


def global_spend_micro_usd(conn: Connection, day: date) -> int:
    total = conn.execute(
        sa.select(sa.func.coalesce(sa.func.sum(spend_daily.c.est_micro_usd), 0)).where(
            spend_daily.c.day == day
        )
    ).scalar_one()
    return int(total)


def bump_metric(conn: Connection, day: date, name: str, dim: str, n: int = 1) -> None:
    upsert_add(conn, metric_daily, {"day": day, "name": name, "dim": dim}, {"n": n})


def record_extraction(
    conn: Connection,
    token_hash: str,
    tier: Tier,
    day: date,
    usage: ProviderUsage,
    limits: TierLimits,
) -> int:
    """Count one extraction; returns today's new count for the token."""
    upsert_add(
        conn,
        usage_daily,
        {"token_hash": token_hash, "day": day},
        {
            "extractions": 1,
            "provider_calls": usage.provider_calls,
            "image_calls": usage.image_calls,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
        },
    )
    upsert_add(
        conn,
        spend_daily,
        {"day": day, "tier": tier},
        {"est_micro_usd": usage.est_micro_usd, "provider_calls": usage.provider_calls},
    )
    count = extractions_today(conn, token_hash, day)
    shadow = limits.for_tier(tier).shadow_threshold
    if shadow is not None and count == shadow + 1:
        # Counted once per token-day; metric_daily has no token id.
        bump_metric(conn, day, SHADOW_METRIC, tier)
    return count


class BurstLimiter:
    """In-memory sliding one-minute window per token hash (single container in the beta)."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, token_hash: str, now_s: float) -> int | None:
        """Record a hit. None = allowed; otherwise seconds until a slot frees."""
        with self._lock:
            q = self._hits.setdefault(token_hash, deque())
            while q and q[0] <= now_s - 60:
                q.popleft()
            if len(q) >= self.per_minute:
                return max(1, math.ceil(q[0] + 60 - now_s))
            q.append(now_s)
            return None

    def forget(self, token_hash: str) -> None:
        with self._lock:
            self._hits.pop(token_hash, None)
