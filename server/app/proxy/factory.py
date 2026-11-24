"""Picks the provider from settings: PENCILED_PROVIDER=stub (default) | anthropic.

The anthropic client reads ANTHROPIC_API_KEY from the environment (host secret
store) itself; nothing here reads, echoes or logs it.
"""

from __future__ import annotations

from app.proxy.adapter import Extractor, StubExtractor
from app.settings import Settings


def make_extractor(settings: Settings) -> Extractor:
    if settings.provider == "anthropic":
        from app.proxy.anthropic_extractor import AnthropicExtractor
        from app.proxy.config import load_provider_config

        return AnthropicExtractor(load_provider_config(settings.provider_config_path))
    return StubExtractor()
