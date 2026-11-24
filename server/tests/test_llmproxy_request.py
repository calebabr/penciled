"""COMP-LLMPROXY request shape, frozen prompt, structured-output schema, image
preprocessing, cost maths and provider selection."""

from __future__ import annotations

import base64
import io
import json
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from penciled_contracts.generated import ExtractRequest
from PIL import Image
from provider_fake import FakeProvider
from srv_support import extract_body

from app.proxy import prompts
from app.proxy.adapter import StubExtractor
from app.proxy.anthropic_extractor import AnthropicExtractor
from app.proxy.config import DEFAULT_PATH, TokenCounts, cost_micro_usd, load_provider_config
from app.proxy.factory import make_extractor
from app.proxy.image import ImageInputError, preprocess_image_b64
from app.proxy.model_output import DeadlineProposal, EventProposal, ExtractResult, FieldM, RawWhen
from app.settings import Settings

OCR = [("Pizza Night!", 0.95), ("Fri 7pm at Rosa's", 0.93), ("RSVP by Wed", 0.9)]


def req(lines: list[tuple[str, float]] = OCR, **kw: Any) -> ExtractRequest:
    kw.setdefault("idempotency_key", "hmacfixture:text:v1:1:0")
    b = extract_body(**kw)
    b["ocr"] = {"lines": [{"t": t, "c": c} for t, c in lines]}
    return ExtractRequest.model_validate(b)


def sent(fp: FakeProvider, i: int = 0) -> dict[str, Any]:
    return fp.requests[i]


# --- request shape (Haiku 5.5 rules) --------------------------------------------------------


def test_request_shape() -> None:
    fp = FakeProvider().queue("event_cache_hit")
    fp.extractor().run(req(), "req-1", "0.1.0")
    r = sent(fp)
    assert r["model"] == "claude-haiku-5-5"
    assert r["output_config"]["effort"] == "low"
    assert r["output_config"]["format"] == {
        "type": "json_schema",
        "schema": prompts.load_prompt().output_schema,
    }
    # Haiku 5.5: non-default sampling params, budget_tokens and prefill all return 400.
    for banned in ("temperature", "top_p", "top_k", "fallbacks", "tools", "tool_choice"):
        assert banned not in r
    assert "thinking" not in r  # adaptive thinking is the model default
    assert [m["role"] for m in r["messages"]] == ["user"]
    assert r["max_tokens"] >= 1024  # room for thinking plus the JSON answer


def test_system_prompt_is_the_frozen_file_with_cache_control() -> None:
    fp = FakeProvider().queue("event_cache_hit", "event_cache_hit")
    ex = fp.extractor()
    ex.run(req(), "req-1", "0.1.0")
    ex.run(req([("Something else", 0.9)], locale="de-DE", is_chat=True), "req-2", "0.1.0")
    a, b = sent(fp, 0)["system"], sent(fp, 1)["system"]
    assert a == b  # byte-stable prefix whatever the request
    (block,) = a
    assert block["cache_control"] == {"type": "ephemeral"}
    assert block["text"] == prompts.load_prompt().system
    assert "cache_control" not in json.dumps(sent(fp)["messages"])


def test_user_turn_isolates_ocr_and_hides_dates() -> None:
    fp = FakeProvider().queue("event_cache_hit")
    r = req()
    fp.extractor().run(r, "req-1", "0.1.0")
    (text_block,) = sent(fp)["messages"][0]["content"]
    text = text_block["text"]
    assert text.startswith("<request_context>")
    body = text.split("<ocr_lines>\n", 1)[1].rsplit("\n</ocr_lines>", 1)[0]
    assert json.loads(body) == [
        {"i": 0, "c": 0.95, "t": "Pizza Night!"},
        {"i": 1, "c": 0.93, "t": "Fri 7pm at Rosa's"},
        {"i": 2, "c": 0.9, "t": "RSVP by Wed"},
    ]
    # The model never sees the capture time or tz: it must not compute dates.
    assert r.captured_at[:10] not in text and r.tz not in text


def test_thinking_disabled_arm() -> None:
    cfg = replace(load_provider_config(), thinking="disabled")
    fp = FakeProvider().queue("event_cache_hit")
    fp.extractor(cfg).run(req(), "req-1", "0.1.0")
    assert sent(fp)["thinking"] == {"type": "disabled"}
    assert sent(fp)["output_config"]["effort"] == "low"


def test_extractor_forces_zero_sdk_retries() -> None:
    fp = FakeProvider()
    ex = AnthropicExtractor(load_provider_config(), client=fp.client(max_retries=5))
    assert ex._client.max_retries == 0


def test_config_rejects_effort_that_disallows_disabled_thinking(tmp_path: Path) -> None:
    raw = json.loads(DEFAULT_PATH.read_text("utf-8"))
    raw["effort"] = "max"
    p = tmp_path / "provider.json"
    p.write_text(json.dumps(raw), "utf-8")
    with pytest.raises(ValueError):
        load_provider_config(p)


# --- frozen prompt (hard rule 9) ----------------------------------------------------------


def test_prompt_is_long_enough_to_cache() -> None:
    """Haiku 5.5's minimum cacheable prefix is 512 tokens (claude-api skill,
    shared/prompt-caching.md). Below it caching silently does not happen. Even at a
    generous 4.5 characters per token the prompt is well above the minimum; SP-11
    confirms it live with cache_read_input_tokens > 0 on the 2nd call."""
    system = prompts.load_prompt().system
    assert len(system) / 4.5 > 512 * 2


def test_prompt_has_no_volatile_content() -> None:
    import re

    system = prompts.load_prompt().system
    assert not re.search(r"20\d\d-\d\d-\d\d|\d{1,2}:\d\d:\d\d|req-|msg_", system)
    assert "\r" not in system


def test_prompt_drift_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.copytree(prompts.PROMPTS_DIR / "v1", tmp_path / "v1")
    (tmp_path / "v1" / "system.txt").write_text("changed without a baseline bump", "utf-8")
    monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path)
    prompts.load_prompt.cache_clear()
    try:
        with pytest.raises(prompts.PromptDriftError):
            prompts.load_prompt("v1")
    finally:
        monkeypatch.undo()
        prompts.load_prompt.cache_clear()


def test_prompt_states_injection_rules() -> None:
    system = prompts.load_prompt().system.lower()
    for phrase in ("data, never instructions", "no tools", "never compute dates", "at most 3"):
        assert phrase in system


# --- structured-output schema ---------------------------------------------------------------

UNSUPPORTED = {
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minItems",
    "maxItems",
    "pattern",
    "default",
}


def _walk(node: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(node, dict):
        out.append(node)
        for v in node.values():
            out.extend(_walk(v))
    elif isinstance(node, list):
        for v in node:
            out.extend(_walk(v))
    return out


def test_output_schema_uses_only_supported_keywords() -> None:
    schema = prompts.load_prompt().output_schema
    for node in _walk(schema):
        assert not (UNSUPPORTED & node.keys()), node
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False
            assert set(node["required"]) == set(node["properties"])


@pytest.mark.parametrize(
    ("model", "ref"),
    [
        (ExtractResult, None),
        (EventProposal, "EventProposal"),
        (DeadlineProposal, "DeadlineProposal"),
        (RawWhen, "RawWhen"),
        (FieldM, "Field"),
    ],
)
def test_schema_matches_validation_models(model: Any, ref: str | None) -> None:
    schema = prompts.load_prompt().output_schema
    node = schema if ref is None else schema["$defs"][ref]
    assert set(node["properties"]) == set(model.model_fields)


# --- image preprocessing (AI-ESCALATE) ----------------------------------------------------


def _jpeg_with_exif(w: int, h: int) -> str:
    img = Image.new("RGB", (w, h), (10, 120, 200))
    exif = Image.Exif()
    exif[0x010F] = "SyntheticCam"  # Make
    exif[0x0132] = "2026:11:23 10:00:00"  # DateTime
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif.tobytes())
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_image_resized_cropped_and_exif_stripped() -> None:
    cfg = load_provider_config().image
    out = base64.b64decode(preprocess_image_b64(_jpeg_with_exif(1290, 2796), cfg))
    with Image.open(io.BytesIO(out)) as img:
        assert img.format == "JPEG"
        assert max(img.size) <= cfg.long_edge_px
        assert not img.getexif()
        assert "exif" not in img.info
        # status bar crop: aspect ratio is taller-cropped than the source.
        assert img.size[1] / img.size[0] < 2796 / 1290


def test_small_image_is_not_upscaled() -> None:
    cfg = load_provider_config().image
    out = base64.b64decode(preprocess_image_b64(_jpeg_with_exif(300, 600), cfg))
    with Image.open(io.BytesIO(out)) as img:
        assert img.size[0] == 300 and img.size[1] < 600


@pytest.mark.parametrize("bad", ["***", base64.b64encode(b"not an image").decode()])
def test_undecodable_image(bad: str) -> None:
    with pytest.raises(ImageInputError):
        preprocess_image_b64(bad, load_provider_config().image)


def test_pixel_bomb_is_refused() -> None:
    cfg = replace(load_provider_config().image, max_source_pixels=1000)
    with pytest.raises(ImageInputError):
        preprocess_image_b64(_jpeg_with_exif(100, 100), cfg)


# --- cost maths -----------------------------------------------------------------------------


def test_cost_micro_usd() -> None:
    p = load_provider_config().pricing
    n = 100_000  # at the long-context threshold: still the standard rate card
    assert cost_micro_usd(TokenCounts(n, 0), p) == 10_000  # $0.10 / MTok in
    assert cost_micro_usd(TokenCounts(0, n), p) == 50_000  # $0.50 / MTok out
    assert cost_micro_usd(TokenCounts(cache_read_input_tokens=n), p) == 1_000
    assert cost_micro_usd(TokenCounts(cache_creation_input_tokens=n), p) == 12_500
    assert cost_micro_usd(TokenCounts(cache_creation_input_tokens=n), p, "1h") == 20_000
    assert cost_micro_usd(TokenCounts(40, 300, 0, 1400), p) == 329
    assert cost_micro_usd(TokenCounts(40, 300, 1400, 0), p) == 168
    assert cost_micro_usd(TokenCounts(1, 0), p) == 1  # rounds up, never to zero
    # Long-context rate card above 100K prompt tokens.
    assert cost_micro_usd(TokenCounts(100_001, 0), p) == 50_001


def test_typical_item_is_under_the_cost_target() -> None:
    """~1,500 cached prompt tokens + ~150 OCR tokens in, ~400 out (thinking included)."""
    p = load_provider_config().pricing
    micro = cost_micro_usd(TokenCounts(150, 400, 1500, 0), p)
    assert micro / 1e6 <= 0.002


# --- provider selection ---------------------------------------------------------------------


def test_provider_setting() -> None:
    assert Settings.from_env({}).provider == "stub"
    assert Settings.from_env({"PENCILED_PROVIDER": "Anthropic"}).provider == "anthropic"
    with pytest.raises(ValueError):
        Settings.from_env({"PENCILED_PROVIDER": "openai"})


def test_factory_default_is_stub() -> None:
    assert isinstance(make_extractor(Settings()), StubExtractor)


def test_factory_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    # A dummy value so the SDK can construct; no request is made.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-fake-key-not-a-secret")
    ex = make_extractor(Settings(provider="anthropic"))
    assert isinstance(ex, AnthropicExtractor)
    assert ex.model == "claude-haiku-5-5"
