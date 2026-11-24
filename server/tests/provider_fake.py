"""Recorded-response fake for the Anthropic API (no network, no key).

The real `anthropic.Anthropic` client runs on top of an `httpx2.MockTransport`
that replays hand-written, synthetic recorded responses from
tests/fixtures/provider/*.json, so the SDK's own response parsing, error mapping
(RateLimitError, OverloadedError, ...) and retry logic are exercised for real.
Requests are kept in memory only, for structural assertions.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic
import httpx2

from app.proxy.anthropic_extractor import AnthropicExtractor
from app.proxy.config import ProviderConfig, load_provider_config

PROVIDER_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "provider"
# Not a credential: the mock transport never leaves the process.
FAKE_KEY = "test-fake-key-not-a-secret"


def load_fixture(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((PROVIDER_FIXTURES / f"{name}.json").read_text("utf-8"))
    return data


@dataclass
class FakeProvider:
    """Queue of scripted replies: a fixture name, or an exception class to raise."""

    script: deque[str | type[Exception]] = field(default_factory=deque)
    requests: list[dict[str, Any]] = field(default_factory=list)

    @property
    def calls(self) -> int:
        return len(self.requests)

    def queue(self, *items: str | type[Exception]) -> FakeProvider:
        self.script.extend(items)
        return self

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(json.loads(request.content))
        if not self.script:
            raise AssertionError("unexpected provider call (script empty)")
        item = self.script.popleft()
        if isinstance(item, type):
            raise item("scripted transport failure", request=request)  # type: ignore[call-arg]
        fx = load_fixture(item)
        return httpx2.Response(
            fx["status"], headers=fx["headers"], content=json.dumps(fx["body"]).encode()
        )

    def client(self, max_retries: int = 2) -> anthropic.Anthropic:
        # max_retries deliberately left at the SDK default here: the extractor must
        # force 0 itself (hard rule 8), whatever client it is handed.
        return anthropic.Anthropic(
            api_key=FAKE_KEY,
            max_retries=max_retries,
            http_client=httpx2.Client(transport=httpx2.MockTransport(self.handler)),
        )

    def extractor(self, cfg: ProviderConfig | None = None) -> AnthropicExtractor:
        return AnthropicExtractor(cfg or load_provider_config(), client=self.client())
