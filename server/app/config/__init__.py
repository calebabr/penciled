"""COMP-QUOTA per-tier limits (D25): config, not code.

`tier_limits.json` is the beta table: free = 100/day with a 30/day shadow
threshold (counted, never enforced); the Pro value is a placeholder. A deploy
can point PENCILED_TIER_LIMITS_PATH at another file. The tier itself comes
only from the token record, never from the client.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Literal, get_args

from penciled_contracts.generated import Tier
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TierLimit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    daily_limit: int = Field(ge=0)
    # Would-have-hit count for pricing research (shadow_cap_hit); None = not tracked.
    shadow_threshold: int | None = Field(default=None, ge=0)


class TierLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    # quota.state is "near" once usage >= near_fraction * daily_limit.
    near_fraction: float = Field(gt=0, le=1)
    tiers: dict[Tier, TierLimit]

    @model_validator(mode="after")
    def _every_tier_present(self) -> TierLimits:
        missing = set(get_args(Tier)) - set(self.tiers)
        if missing:
            raise ValueError("tier_limits must define every contract tier")
        return self

    def for_tier(self, tier: Tier) -> TierLimit:
        return self.tiers[tier]


def load_tier_limits(path: str | None = None) -> TierLimits:
    if path is None:
        raw = resources.files(__package__).joinpath("tier_limits.json").read_text("utf-8")
    else:
        raw = Path(path).read_text("utf-8")
    return TierLimits.model_validate(json.loads(raw))
