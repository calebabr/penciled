"""Server settings, read from the environment once at startup.

Secrets (DATABASE_URL, later the provider key) come only from the host secret
store as environment variables. Nothing here logs or echoes a setting value.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace

_VERSION_CORE = re.compile(r"^([0-9]+(?:\.[0-9]+){0,3})")


def parse_version(value: str) -> tuple[int, ...] | None:
    """Numeric core of a VersionString ("0.3.1-beta.2" -> (0, 3, 1, 0)); None if unparsable."""
    m = _VERSION_CORE.match(value)
    if m is None:
        return None
    parts = [int(p) for p in m.group(1).split(".")]
    return tuple(parts + [0] * (4 - len(parts)))


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(raw: str | None, default: int) -> int:
    return default if raw is None or raw == "" else int(raw)


def _float(raw: str | None, default: float) -> float:
    return default if raw is None or raw == "" else float(raw)


PROVIDERS = ("stub", "anthropic")


def _provider(raw: str | None, default: str) -> str:
    if raw is None or raw == "":
        return default
    value = raw.strip().lower()
    if value not in PROVIDERS:
        raise ValueError("PENCILED_PROVIDER must be stub or anthropic")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str | None = None
    # 426 below this client_version; also returned in every 200 (DESIGN 3.7).
    min_app_version: str = "0.1.0"
    # Global kill switch: every extract returns 503 {basic:true}.
    paused: bool = False
    # Global daily $ estimate cap across all tiers (provider $25/month cap is the backstop).
    global_daily_usd_cap: float = 1.0
    # Optional override of the packaged app/config/tier_limits.json.
    tier_limits_path: str | None = None
    # 413 limits (DESIGN 3.7: text > 16 KB or image too large).
    max_body_bytes: int = 3_000_000
    max_text_bytes: int = 16_384
    max_image_b64_chars: int = 2_200_000
    # 429 per-token burst limit (requests per rolling minute).
    burst_per_minute: int = 30
    # COMP-IDEMP: result TTL (memory) and the in-flight lease (a crashed request frees its key).
    idem_result_ttl_s: int = 600
    idem_inflight_lease_s: int = 60
    idem_retry_after_s: int = 3
    idem_cache_max_entries: int = 5000
    # How often expired idempotency rows are swept (seconds).
    idem_sweep_interval_s: int = 60
    # COMP-LLMPROXY: "stub" (default; tests) or "anthropic" (key from the host secret store).
    provider: str = "stub"
    # Optional override of the packaged app/config/provider.json.
    provider_config_path: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        e = os.environ if env is None else env
        d = cls()
        return replace(
            d,
            database_url=e.get("DATABASE_URL") or None,
            min_app_version=e.get("PENCILED_MIN_APP_VERSION") or d.min_app_version,
            paused=_bool(e.get("PENCILED_PAUSED"), d.paused),
            global_daily_usd_cap=_float(
                e.get("PENCILED_GLOBAL_DAILY_USD_CAP"), d.global_daily_usd_cap
            ),
            tier_limits_path=e.get("PENCILED_TIER_LIMITS_PATH") or None,
            burst_per_minute=_int(e.get("PENCILED_BURST_PER_MINUTE"), d.burst_per_minute),
            provider=_provider(e.get("PENCILED_PROVIDER"), d.provider),
            provider_config_path=e.get("PENCILED_PROVIDER_CONFIG_PATH") or None,
        )
