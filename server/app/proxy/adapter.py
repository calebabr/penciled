"""Provider adapter seam (DESIGN 3.6 seam 5). SPR-05 plugs the real COMP-LLMPROXY
in behind `Extractor`; until then `StubExtractor` returns a schema-valid
nothing-to-do result and counts its (pretend) provider calls."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Protocol

from penciled_contracts.generated import SCHEMA_VERSION, ExtractRequest, ExtractResponse


@dataclass(frozen=True)
class ProviderUsage:
    provider_calls: int = 0
    image_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    est_micro_usd: int = 0


@dataclass(frozen=True)
class ExtractOutcome:
    response: ExtractResponse
    usage: ProviderUsage = field(default_factory=ProviderUsage)


class Extractor(Protocol):
    def run(self, req: ExtractRequest, request_id: str, min_app_version: str) -> ExtractOutcome:
        """Never logs the request; raises on provider failure."""
        ...


class StubExtractor:
    model = "stub"
    prompt_version = "p0"
    thresholds_version = "v0"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.provider_calls = 0

    def run(self, req: ExtractRequest, request_id: str, min_app_version: str) -> ExtractOutcome:
        usage = ProviderUsage()
        if req.mode == "extract":
            with self._lock:
                self.provider_calls += 1
            usage = ProviderUsage(provider_calls=1, image_calls=int(req.image_b64 is not None))
        override = req.anchor_override
        response = ExtractResponse.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "request_id": request_id,
                "class": "nothing",
                "gate_state": "none",
                "card_score": None,
                "actions": [],
                "nothing_subtype": "other",
                "notification": None,
                "anchor": {
                    "iso": override if override is not None else req.captured_at,
                    "source": "override" if override is not None else "capture",
                },
                "escalate_hint": False,
                "raw": None,
                "min_app_version": min_app_version,
                "model": self.model,
                "prompt_version": self.prompt_version,
                "thresholds_version": self.thresholds_version,
            }
        )
        return ExtractOutcome(response=response, usage=usage)
