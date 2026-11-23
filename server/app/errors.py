"""Contract error envelopes (shared/schema/error.schema.json) and content-free
validation issues (D20.7, hard rule 3): paths and error types only, never input."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TypeVar

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from penciled_contracts.generated import SCHEMA_VERSION, ErrorCode, ErrorResponse
from pydantic import BaseModel, ValidationError

STATUS_FOR_CODE: dict[ErrorCode, int] = {
    "in_flight": 202,
    "unauthorized": 401,
    "invalid_invite": 403,
    "payload_too_large": 413,
    "invalid_request": 422,
    "upgrade_required": 426,
    "rate_limited": 429,
    "internal": 500,
    "service_paused": 503,
}

_LOC_PART = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TYPE_TOKEN = re.compile(r"^[a-z0-9][a-z0-9_.:\-]*$")
MAX_ISSUES = 50
M = TypeVar("M", bound=BaseModel)
MAX_LOC = 16


def error_response(
    code: ErrorCode,
    *,
    retry_after: int | None = None,
    basic: bool | None = None,
    min_app_version: str | None = None,
    issues: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    raw: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "code": code}
    if retry_after is not None:
        raw["retry_after"] = retry_after
    if basic is not None:
        raw["basic"] = basic
    if min_app_version is not None:
        raw["min_app_version"] = min_app_version
    if issues is not None:
        raw["issues"] = issues
    body = ErrorResponse.model_validate(raw).to_json_dict()
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
    return JSONResponse(status_code=STATUS_FOR_CODE[code], content=body, headers=headers)


def _issue(loc: Iterable[Any], err_type: Any) -> dict[str, Any]:
    parts: list[str | int] = []
    for p in loc:
        if isinstance(p, bool):
            continue
        if isinstance(p, int) and p >= 0:
            parts.append(p)
        elif isinstance(p, str) and len(p) <= 64 and _LOC_PART.match(p):
            parts.append(p)
        # Anything else (union branch labels, dict keys from the body) is dropped:
        # a loc segment must never carry request data.
    t = err_type if isinstance(err_type, str) else ""
    if not (len(t) <= 64 and _TYPE_TOKEN.match(t)):
        t = "invalid"
    return {"loc": parts[:MAX_LOC], "type": t}


def issues_from_errors(
    errors: Sequence[Mapping[str, Any]], prefix: tuple[str, ...] = ()
) -> list[dict[str, Any]]:
    out = [_issue((*prefix, *e.get("loc", ())), e.get("type")) for e in errors]
    return out[:MAX_ISSUES]


def invalid_request(issues: list[dict[str, Any]]) -> JSONResponse:
    return error_response("invalid_request", issues=issues)


def decode_json(body: bytes) -> tuple[bool, Any]:
    """(ok, data). Never raises; the error carries no input."""
    try:
        return True, json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return False, None


JSON_INVALID = [{"loc": ["body"], "type": "json_invalid"}]


def validate_model(model: type[M], data: Any) -> M | JSONResponse:
    """Validate decoded JSON against a model. On failure, a content-free 422."""
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        errs = exc.errors(include_url=False, include_context=False, include_input=False)
        return invalid_request(issues_from_errors(errs, prefix=("body",)))


def parse_json_model(model: type[M], body: bytes) -> M | JSONResponse:
    ok, data = decode_json(body)
    if not ok:
        return invalid_request(JSON_INVALID)
    return validate_model(model, data)


async def content_free_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Replace FastAPI's default 422, which echoes the request input (hard rule 3)."""
    return invalid_request(issues_from_errors(exc.errors()))
