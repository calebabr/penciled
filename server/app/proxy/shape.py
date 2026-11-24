"""Turns a validated model result into the contract ExtractResponse, and decides
`escalate_hint` (DESIGN 5.2 triggers).

INTERIM (SPR-05): COMP-RESOLVER-GVP (SPR-14: grounding fuzzy >= 0.9, validation,
propose) and COMP-RESOLVER-DATE (SPR-13) are not built yet, so this module is
deliberately conservative and is replaced there:
- grounding is exact (after case/whitespace normalisation): evidence must be a
  substring of the OCR line it cites, and a text value must be a substring of
  that line, otherwise the field is cleared to `missing`;
- dates are never resolved here (hard rule 7): every start/due has value null,
  flag needs_review (or missing) and blocking true, so no card can be Ready;
- gate_state is `ask` for a grounded proposal and `needs_look` otherwise;
  card_score is null (AI-CONF not built); alarms [] and notification null
  (AI-PROPOSE not built); deadline_origin "other" (the rules.json pattern is
  applied by SPR-14 code, never by the model).

The model output is untrusted (hard rule 1, SEC-INJ-VALIDATE): kinds are limited to
two, <= 3 actions, related_to must point at an event, titles with URLs, emails or
commands are cleared, unknown keys were already rejected by model_output.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from penciled_contracts.generated import SCHEMA_VERSION, ExtractRequest, ExtractResponse

from app.proxy.model_output import DeadlineProposal, EventProposal, Evidence, ExtractResult, FieldM

_WS = re.compile(r"\s+")
_BAD_TITLE = re.compile(
    r"(https?://|www\.|://|\S+@\S+\.\S+|\b(?:sudo|rm\s+-rf|curl|wget|powershell|cmd\.exe)\b)",
    re.IGNORECASE,
)
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
GOOD_LINE_CONF = 0.5
MIN_GOOD_LINES = 3


def norm(text: str) -> str:
    return _WS.sub(" ", unicodedata.normalize("NFKC", text)).strip().casefold()


@dataclass(frozen=True)
class Versions:
    model: str
    prompt_version: str
    thresholds_version: str
    min_app_version: str


def _line(req: ExtractRequest, idx: int) -> str | None:
    lines = req.ocr.lines
    return lines[idx].t if 0 <= idx < len(lines) else None


def evidence_grounded(req: ExtractRequest, ev: Evidence | None) -> bool:
    if ev is None:
        return False
    line = _line(req, ev.line)
    return line is not None and norm(ev.text) != "" and norm(ev.text) in norm(line)


def _span(line: str, value: str, idx: int) -> dict[str, int] | None:
    low = line.casefold()
    if len(low) != len(line):
        return None
    pos = low.find(value.casefold())
    if pos < 0:
        return None
    return {"line": idx, "start": pos, "end": pos + len(value)}


def text_field(req: ExtractRequest, f: FieldM, required: bool, is_title: bool) -> dict[str, Any]:
    """Grounded value, or cleared to missing. Never the model's unsupported text."""
    value = f.value.strip() if f.value is not None else None
    ok = (
        value is not None
        and value != ""
        and _CTRL.search(value) is None
        and evidence_grounded(req, f.evidence)
        and not (is_title and _BAD_TITLE.search(value))
    )
    if ok and value is not None and f.evidence is not None:
        line = _line(req, f.evidence.line) or ""
        if norm(value) in norm(line):
            out: dict[str, Any] = {"value": value, "flag": "ok", "blocking": False}
            span = _span(line, value, f.evidence.line)
            if span is not None:
                out["src_span"] = span
            return out
    return {"value": None, "flag": "missing", "blocking": required}


def when_field(req: ExtractRequest, w: Any) -> tuple[dict[str, Any], bool]:
    """(field, grounded). Unresolved until COMP-RESOLVER-DATE: value is always null."""
    has_text = w is not None and (w.date_text or w.time_text)
    grounded = (
        bool(has_text) and bool(w.evidence) and all(evidence_grounded(req, e) for e in w.evidence)
    )
    if not grounded:
        return {"value": None, "flag": "missing", "blocking": True}, False
    return {"value": None, "flag": "needs_review", "blocking": True}, True


def _actions(req: ExtractRequest, result: ExtractResult) -> tuple[list[dict[str, Any]], bool]:
    """(actions, any required field missing or ungrounded)."""
    out: list[dict[str, Any]] = []
    weak = False
    kinds = [a.kind for a in result.actions]
    for i, a in enumerate(result.actions):
        title = text_field(req, a.title, required=True, is_title=True)
        if isinstance(a, EventProposal):
            start, ok = when_field(req, a.start)
            fields: dict[str, Any] = {
                "title": title,
                "start": start,
                "location": text_field(req, a.location, required=False, is_title=False),
            }
            out.append({"kind": "event", "fields": fields, "alarms": [], "related_to": None})
        elif isinstance(a, DeadlineProposal):
            due, ok = when_field(req, a.due)
            rel = a.related_to
            if rel is not None and not (rel != i and rel < len(kinds) and kinds[rel] == "event"):
                rel = None
            out.append(
                {
                    "kind": "deadline",
                    "fields": {"title": title, "due": due},
                    "alarms": [],
                    "related_to": rel,
                    "deadline_origin": "other",
                }
            )
        weak = weak or not ok or title["flag"] == "missing"
    return out, weak


def few_good_lines(req: ExtractRequest) -> bool:
    good = sum(1 for line in req.ocr.lines if float(line.c) >= GOOD_LINE_CONF and line.t.strip())
    return good < MIN_GOOD_LINES


def escalate_hint(req: ExtractRequest, weak: bool) -> bool:
    """DESIGN 5.2: only from a text call, only if images are allowed and not a chat.
    Sensitive items never reach the server; redaction hits are gated on device
    (the request carries no redaction flag)."""
    if req.image_b64 is not None or not req.image_allowed or req.is_chat:
        return False
    return weak or few_good_lines(req)


def _base(req: ExtractRequest, request_id: str, v: Versions) -> dict[str, Any]:
    override = req.anchor_override
    return {
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "card_score": None,
        "notification": None,
        "anchor": {
            "iso": override if override is not None else req.captured_at,
            "source": "override" if override is not None else "capture",
        },
        "min_app_version": v.min_app_version,
        "model": v.model,
        "prompt_version": v.prompt_version,
        "thresholds_version": v.thresholds_version,
    }


def needs_look(req: ExtractRequest, request_id: str, v: Versions, *, hint: bool) -> ExtractResponse:
    """Refusal, invalid model output or truncated output: a 'Needs a look' card."""
    body = _base(req, request_id, v)
    body.update(
        {
            "class": "unsure",
            "gate_state": "needs_look",
            "actions": [],
            "escalate_hint": escalate_hint(req, True) if hint else False,
            "raw": None,
        }
    )
    return ExtractResponse.model_validate(body)


def from_result(
    req: ExtractRequest, result: ExtractResult, request_id: str, v: Versions
) -> ExtractResponse:
    body = _base(req, request_id, v)
    cls = result.screen_class
    if cls == "sensitive":
        # Model as a backup guard signal (DESIGN 5.3): drop everything, keep no content.
        body.update({"class": "sensitive", "gate_state": "none", "actions": [], "raw": None})
        body["escalate_hint"] = False
        return ExtractResponse.model_validate(body)
    if cls == "nothing":
        body.update(
            {
                "class": "nothing",
                "gate_state": "none",
                "actions": [],
                "nothing_subtype": result.nothing_subtype or "other",
                "raw": result.model_dump(mode="json"),
                "escalate_hint": escalate_hint(req, False),
            }
        )
        return ExtractResponse.model_validate(body)

    actions, weak = _actions(req, result)
    if cls == "unsure" or not actions:
        out_cls, gate, weak = "unsure", "needs_look", True
    else:
        # The model's class is kept only when it matches what it proposed.
        out_cls = cls if any(a["kind"] == cls for a in actions) else actions[0]["kind"]
        gate = "ask" if not weak else "needs_look"
    body.update(
        {
            "class": out_cls,
            "gate_state": gate,
            "actions": actions,
            "raw": result.model_dump(mode="json"),
            "escalate_hint": escalate_hint(req, weak),
        }
    )
    return ExtractResponse.model_validate(body)
