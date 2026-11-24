"""Model-facing extraction result (DESIGN 5.4, server-internal; C6).

The JSON schema sent as the structured-output format is the frozen
prompts/<version>/output_schema.json. The API cannot enforce length or range
constraints (structured outputs drop minLength/maxLength/minimum/maximum), so
these models re-validate every response with the full constraints. Model output
is untrusted (hard rule 1): anything that fails here never reaches the client.

Every value here is content; never log it.
"""

from __future__ import annotations

import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

Conf = Literal["high", "medium", "low"]
ScreenClassM = Literal["event", "deadline", "nothing", "sensitive", "unsure"]
NothingSubtypeM = Literal["receipt_order", "shipping", "booking", "meme", "other"]

MAX_ACTIONS = 3
MAX_LINE_INDEX = 10_000
_Short = Annotated[str, StringConstraints(max_length=500)]
_Hint = Annotated[str, StringConstraints(max_length=40)]
_Note = Annotated[str, StringConstraints(max_length=140)]


class _Strict(BaseModel):
    # Unknown keys are rejected, not dropped: schema-invalid output is not passed through.
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Evidence(_Strict):
    text: Annotated[str, StringConstraints(min_length=1, max_length=2000)]
    line: Annotated[int, Field(ge=0, le=MAX_LINE_INDEX)]


class RawWhen(_Strict):
    date_text: _Short | None
    time_text: _Short | None
    tz_text: _Short | None
    evidence: Annotated[list[Evidence], Field(max_length=4)]
    conf: Conf


class FieldM(_Strict):
    value: _Short | None
    evidence: Evidence | None
    conf: Conf


class EventProposal(_Strict):
    kind: Literal["event"]
    title: FieldM
    start: RawWhen
    end: RawWhen | None
    location: FieldM
    all_day_hint: bool


class DeadlineProposal(_Strict):
    kind: Literal["deadline"]
    title: FieldM
    due: RawWhen
    related_to: Annotated[int, Field(ge=0, le=MAX_ACTIONS - 1)] | None


class ExtractResult(_Strict):
    screen_class: ScreenClassM
    class_conf: Conf
    source_hint: _Hint | None
    nothing_subtype: NothingSubtypeM | None
    actions: Annotated[
        list[Annotated[EventProposal | DeadlineProposal, Field(discriminator="kind")]],
        Field(max_length=MAX_ACTIONS),
    ]
    notes_for_user: _Note | None


class ModelOutputInvalid(ValueError):
    """The model's text is not a valid ExtractResult. Carries no content."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def parse_model_text(text: str) -> ExtractResult:
    try:
        data = json.loads(text)
    except ValueError:
        raise ModelOutputInvalid("json_invalid") from None
    try:
        # json.loads output is plain JSON types, so strict mode applies cleanly.
        return ExtractResult.model_validate(data)
    except ValidationError:
        raise ModelOutputInvalid("schema_invalid") from None
