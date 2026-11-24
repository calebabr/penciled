"""Builds the provider request (SEC-INJ-ISOLATE, DESIGN 7.3).

Order: frozen system prompt (cache breakpoint on its last block) -> user turn
with the optional image, a small request context block and the OCR lines as a
delimited JSON array. Instructions live only in the system prompt; OCR text is
data. Nothing volatile (ids, timestamps, the capture time) goes in the prefix.

The model is never shown captured_at or the tz: it must not compute dates
(date maths happens only in the server resolver, hard rule 7).
"""

from __future__ import annotations

import json
import re
from typing import Any

from penciled_contracts.generated import ExtractRequest

OCR_OPEN = "<ocr_lines>"
OCR_CLOSE = "</ocr_lines>"
_TAG_LIKE = re.compile(r"</?\s*(ocr_lines|request_context)\b[^>]*>", re.IGNORECASE)
TAG_REMOVED = "[tag]"


def neutralise(text: str) -> str:
    """Drop anything that imitates our delimiters, so OCR text cannot close the data block."""
    return _TAG_LIKE.sub(TAG_REMOVED, text)


def system_blocks(system_prompt: str, cache_ttl: str) -> list[dict[str, Any]]:
    cache: dict[str, Any] = {"type": "ephemeral"}
    if cache_ttl == "1h":
        cache["ttl"] = "1h"
    return [{"type": "text", "text": system_prompt, "cache_control": cache}]


def ocr_block(req: ExtractRequest) -> str:
    lines = [
        {"i": i, "c": round(float(line.c), 2), "t": neutralise(line.t)}
        for i, line in enumerate(req.ocr.lines)
    ]
    return OCR_OPEN + "\n" + json.dumps(lines, ensure_ascii=False) + "\n" + OCR_CLOSE


def context_block(req: ExtractRequest) -> str:
    ctx = {"locale": req.locale, "looks_like_chat": bool(req.is_chat)}
    return "<request_context>" + json.dumps(ctx) + "</request_context>"


def user_content(req: ExtractRequest, image_jpeg_b64: str | None) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    if image_jpeg_b64 is not None:
        content.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": image_jpeg_b64},
            }
        )
    content.append({"type": "text", "text": context_block(req) + "\n" + ocr_block(req)})
    return content
