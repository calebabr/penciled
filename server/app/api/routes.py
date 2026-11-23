"""/v1 routes (DESIGN 3.7). Bodies are read raw (size-capped) and validated against
the shared contracts, so every rejection is a content-free contract envelope."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from penciled_contracts.generated import SCHEMA_VERSION, ExtractRequest
from pydantic import BaseModel, ConfigDict, Field

from app.api.service import Services, no_content, precheck, precheck_raw
from app.errors import (
    JSON_INVALID,
    decode_json,
    error_response,
    invalid_request,
    parse_json_model,
    validate_model,
)

router = APIRouter(prefix="/v1")

MAX_REGISTER_BYTES = 4096


class RegisterRequest(BaseModel):
    """POST /v1/register body. Server-local: not in shared/ contracts v1 (reported gap)."""

    model_config = ConfigDict(extra="ignore", strict=True)

    schema_version: Literal[1]
    invite_code: str = Field(min_length=1, max_length=128)


def _services(request: Request) -> Services:
    svc: Services = request.app.state.services
    return svc


async def _read_capped(request: Request, max_bytes: int) -> bytes | None:
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > max_bytes:
        return None
    buf = bytearray()
    async for chunk in request.stream():
        buf += chunk
        if len(buf) > max_bytes:
            return None
    return bytes(buf)


@router.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "schema_version": SCHEMA_VERSION}


@router.post("/register", response_model=None)
async def register_route(request: Request) -> Response:
    svc = _services(request)
    raw = await _read_capped(request, MAX_REGISTER_BYTES)
    if raw is None:
        return error_response("payload_too_large")
    parsed = parse_json_model(RegisterRequest, raw)
    if isinstance(parsed, JSONResponse):
        return parsed
    issued = await run_in_threadpool(svc.register, parsed.invite_code)
    if issued is None:
        return error_response("invalid_invite")
    token, tier = issued
    return JSONResponse(
        status_code=200,
        content={"schema_version": SCHEMA_VERSION, "token": token, "tier": tier},
        headers={"Cache-Control": "no-store"},
    )


@router.post("/extract", response_model=None)
async def extract_route(request: Request) -> Response:
    svc = _services(request)
    record = await run_in_threadpool(svc.authenticate, request.headers.get("authorization"))
    if record is None:
        return error_response("unauthorized")
    raw = await _read_capped(request, svc.settings.max_body_bytes)
    if raw is None:
        return error_response("payload_too_large")
    ok, data = decode_json(raw)
    if not ok:
        return invalid_request(JSON_INVALID)
    upgrade = precheck_raw(data, svc.settings)
    if upgrade is not None:
        return upgrade
    parsed = validate_model(ExtractRequest, data)
    if isinstance(parsed, JSONResponse):
        return parsed
    rejected = precheck(parsed, svc.settings)
    if rejected is not None:
        return rejected
    return await run_in_threadpool(svc.extract, record, parsed)


@router.delete("/me", response_model=None)
async def delete_me_route(request: Request) -> Response:
    svc = _services(request)
    record = await run_in_threadpool(svc.authenticate, request.headers.get("authorization"))
    if record is None:
        return error_response("unauthorized")
    await run_in_threadpool(svc.delete_me, record)
    return no_content()
