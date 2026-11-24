"""COMP-LLMPROXY settings and price card, read from app/config/provider.json
(override path: PENCILED_PROVIDER_CONFIG_PATH). Prices live in config, not code.

No secret is read here: the Anthropic SDK reads ANTHROPIC_API_KEY from the
environment (host secret store) itself.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "provider.json"

Effort = Literal["low", "medium", "high"]
Thinking = Literal["adaptive", "disabled"]
CacheTtl = Literal["5m", "1h"]


@dataclass(frozen=True)
class Pricing:
    input: float
    output: float
    long_context_threshold_tokens: int
    long_input: float
    long_output: float
    cache_read_multiplier: float
    cache_write_5m_multiplier: float
    cache_write_1h_multiplier: float


@dataclass(frozen=True)
class TokenCounts:
    """Token counts from one provider response (Usage); counts only, no content."""

    input_tokens: int = 0  # uncached input, billed at the full input rate
    output_tokens: int = 0  # includes thinking tokens
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    @property
    def prompt_tokens(self) -> int:
        return self.input_tokens + self.cache_read_input_tokens + self.cache_creation_input_tokens


def cost_micro_usd(t: TokenCounts, p: Pricing, cache_ttl: CacheTtl = "5m") -> int:
    """Estimated cost in micro-USD, rounded up. $/MTok x tokens = micro-USD."""
    long = t.prompt_tokens > p.long_context_threshold_tokens
    in_rate = p.long_input if long else p.input
    out_rate = p.long_output if long else p.output
    write_mult = p.cache_write_1h_multiplier if cache_ttl == "1h" else p.cache_write_5m_multiplier
    total = (
        t.input_tokens * in_rate
        + t.cache_read_input_tokens * in_rate * p.cache_read_multiplier
        + t.cache_creation_input_tokens * in_rate * write_mult
        + t.output_tokens * out_rate
    )
    # Round to 1e-6 first so float noise (e.g. 30.000000000000004) does not add a micro-dollar.
    return math.ceil(round(total, 6))


@dataclass(frozen=True)
class ImageConfig:
    long_edge_px: int
    jpeg_quality: int
    status_bar_crop_frac: float
    max_source_pixels: int


@dataclass(frozen=True)
class ProviderConfig:
    model: str
    prompt_version: str
    thresholds_version: str
    effort: Effort
    thinking: Thinking
    max_tokens: int
    timeout_s: float
    cache_ttl: CacheTtl
    image: ImageConfig
    pricing: Pricing


def _pricing(raw: dict[str, Any]) -> Pricing:
    return Pricing(
        input=float(raw["input"]),
        output=float(raw["output"]),
        long_context_threshold_tokens=int(raw["long_context_threshold_tokens"]),
        long_input=float(raw["long_input"]),
        long_output=float(raw["long_output"]),
        cache_read_multiplier=float(raw["cache_read_multiplier"]),
        cache_write_5m_multiplier=float(raw["cache_write_5m_multiplier"]),
        cache_write_1h_multiplier=float(raw["cache_write_1h_multiplier"]),
    )


def load_provider_config(path: str | Path | None = None) -> ProviderConfig:
    raw = json.loads(Path(path or DEFAULT_PATH).read_text("utf-8"))
    effort = raw["effort"]
    thinking = raw["thinking"]
    ttl = raw["cache_ttl"]
    # Haiku 5.5: thinking "disabled" is accepted only at effort low/medium/high.
    if effort not in ("low", "medium", "high"):
        raise ValueError("provider effort must be low, medium or high")
    if thinking not in ("adaptive", "disabled"):
        raise ValueError("provider thinking must be adaptive or disabled")
    if ttl not in ("5m", "1h"):
        raise ValueError("provider cache_ttl must be 5m or 1h")
    img = raw["image"]
    return ProviderConfig(
        model=str(raw["model"]),
        prompt_version=str(raw["prompt_version"]),
        thresholds_version=str(raw["thresholds_version"]),
        effort=effort,
        thinking=thinking,
        max_tokens=int(raw["max_tokens"]),
        timeout_s=float(raw["timeout_s"]),
        cache_ttl=ttl,
        image=ImageConfig(
            long_edge_px=int(img["long_edge_px"]),
            jpeg_quality=int(img["jpeg_quality"]),
            status_bar_crop_frac=float(img["status_bar_crop_frac"]),
            max_source_pixels=int(img["max_source_pixels"]),
        ),
        pricing=_pricing(raw["pricing_usd_per_mtok"]),
    )
