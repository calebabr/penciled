"""Structured, content-scrubbing logging (SEC-LOG-NOCONTENT / SEC-LOG-SCRUB, hard rule 3).

Rules enforced by the formatter, whatever the caller does:
- The message is the call's *template* (record.msg); %-args are never interpolated,
  so a value passed as an argument cannot reach the output.
- Only allowlisted `extra` keys are emitted, and string values must be token-shaped
  (enum/id/route-like); anything else becomes "[scrubbed]".
- Exceptions emit the exception class and frame locations only, never the message
  (pydantic and driver errors embed input values in their messages).
- uvicorn's own access log is disabled; AccessLogMiddleware logs method, route
  template, status and latency. Request bodies and query strings are never logged.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import traceback
from datetime import UTC, datetime
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

SAFE_KEYS = (
    "event",
    "method",
    "route",
    "status",
    "latency_ms",
    "code",
    "request_id",
    "tier",
    "mode",
    "outcome",
    "exc_type",
    "count",
    # COMP-LLMPROXY provider_call: integer token counts only.
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
)
_SAFE_STR = re.compile(r"^[A-Za-z0-9_.:/{}\-]{1,80}$")
SCRUBBED = "[scrubbed]"
_MAX_TEMPLATE = 160

access_logger = logging.getLogger("penciled.access")


def _safe_value(value: Any) -> Any:
    if isinstance(value, bool | int | float):
        return value
    if isinstance(value, str) and _SAFE_STR.match(value):
        return value
    return SCRUBBED


# Third-party loggers whose messages are %-templates (args are never applied here).
# Any other third-party logger's message is dropped: it might be pre-formatted.
_TEMPLATE_LOGGERS = ("uvicorn", "uvicorn.error", "alembic.runtime.migration")


def _template(record: logging.LogRecord) -> str:
    msg = record.msg
    if not isinstance(msg, str):
        return SCRUBBED
    if record.name.startswith("penciled") or record.name in _TEMPLATE_LOGGERS:
        return msg[:_MAX_TEMPLATE]
    return SCRUBBED


class ScrubbingJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": _template(record),
        }
        for key in SAFE_KEYS:
            if key in record.__dict__:
                out[key] = _safe_value(record.__dict__[key])
        if record.exc_info and record.exc_info[0] is not None:
            out["exc_type"] = record.exc_info[0].__name__
            tb = record.exc_info[2]
            if tb is not None:
                out["frames"] = [
                    f"{fs.filename.replace(chr(92), '/').rsplit('/', 1)[-1]}:{fs.lineno}:{fs.name}"
                    for fs in traceback.extract_tb(tb)
                ][-8:]
        return json.dumps(out, separators=(",", ":"))

    def formatException(self, ei: Any) -> str:  # noqa: N802 (logging API name)
        return ""

    def formatStack(self, stack_info: str) -> str:  # noqa: N802
        return ""


def make_handler(stream: Any = None) -> logging.Handler:
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(ScrubbingJsonFormatter())
    return handler


def configure_logging(level: int = logging.INFO) -> None:
    """Root -> one scrubbing JSON handler. uvicorn's loggers propagate to it;
    uvicorn.access is silenced (our middleware replaces it)."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(make_handler())
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
    access = logging.getLogger("uvicorn.access")
    access.handlers.clear()
    access.propagate = False
    access.disabled = True
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


# Third-party loggers held at WARNING. The anthropic SDK and its httpx2 transport log
# request options (the full prompt, OCR text and image) at DEBUG when ANTHROPIC_LOG is
# set; holding them at WARNING means those records are never created (the formatter
# would scrub them anyway).
QUIET_LOGGERS = ("sqlalchemy", "alembic", "httpx", "httpcore", "anthropic", "httpx2", "httpcore2")


def quiet_provider_loggers() -> None:
    for name in ("anthropic", "httpx2", "httpcore2"):
        logging.getLogger(name).setLevel(logging.WARNING)


class AccessLogMiddleware:
    """Pure ASGI access log: method, matched route template, status, latency."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = time.perf_counter()
        status = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            access_logger.info(
                "http",
                extra={
                    "event": "http",
                    "method": scope.get("method", ""),
                    "route": getattr(route, "path", "unmatched"),
                    "status": status,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 1),
                },
            )
