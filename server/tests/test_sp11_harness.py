"""SP-11 harness guard rails (offline): no API call without --i-approve-spend."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

HARNESS = Path(__file__).resolve().parents[1] / "tools" / "sp11_latency.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sp11_latency", HARNESS)
    assert spec is not None and spec.loader is not None
    if "sp11_latency" in sys.modules:
        return sys.modules["sp11_latency"]
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sp11_latency"] = mod  # dataclasses resolve their module by name
    spec.loader.exec_module(mod)
    return mod


def test_refuses_without_approval(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mod = _load()
    import anthropic

    def boom(*a: object, **k: object) -> None:
        raise AssertionError("client constructed without approval")

    monkeypatch.setattr(anthropic, "Anthropic", boom)
    assert mod.main(["-n", "5"]) == 2
    out = capsys.readouterr().out
    assert "Estimated MAXIMUM cost: $" in out and "No API call made" in out


def test_estimate_is_an_upper_bound_and_small() -> None:
    mod = _load()
    from app.proxy.config import load_provider_config

    cfg = load_provider_config()
    items = mod.synthetic_items(50, 11)
    est = mod.max_cost_usd(cfg, items, list(mod.ARMS))
    assert 0 < est < 1.0
    assert {i.gold_class for i in items} == {"event", "deadline", "nothing"}


def test_verdict_rules() -> None:
    mod = _load()
    row = {"calls_ok": 50, "mean_usd": 0.0003, "call2_cache_read_tokens": 1300}
    rows = [
        {**row, "arm": "adaptive", "p50_s": 1.4, "p95_s": 3.5, "class_accuracy": 0.95},
        {**row, "arm": "nothink", "p50_s": 0.9, "p95_s": 2.5, "class_accuracy": 0.90},
    ]
    assert mod.verdict(rows)[-1].startswith("pick: adaptive")  # faster arm loses > 2 points
    slow = [{**r, "p95_s": 7.0} for r in rows]
    assert any(v.startswith("HARD FAIL") for v in mod.verdict(slow))
