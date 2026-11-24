"""FastAPI application entry point.

Hard rule 3: no screenshot content (OCR text, image bytes, extracted fields,
model output, request bodies) may appear in logs or error responses. Every
non-200 body is the contract ErrorResponse envelope; 422s carry paths and
error types only.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from penciled_contracts.generated import SCHEMA_VERSION

from app.api.routes import router
from app.api.service import Services, utcnow
from app.config import TierLimits, load_tier_limits
from app.db.engine import Database
from app.errors import content_free_validation_handler, error_response
from app.logs import AccessLogMiddleware
from app.proxy.adapter import Extractor
from app.proxy.factory import make_extractor
from app.settings import Settings

__all__ = ["SCHEMA_VERSION", "app", "content_free_validation_handler", "create_app"]

logger = logging.getLogger("penciled.app")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Exception type only: messages from drivers/pydantic can embed input values.
    logger.error(
        "unhandled_exception", extra={"event": "unhandled", "exc_type": type(exc).__name__}
    )
    return error_response("internal")


def create_app(
    settings: Settings | None = None,
    *,
    limits: TierLimits | None = None,
    extractor: Extractor | None = None,
    db: Database | None = None,
    clock: Callable[[], datetime] = utcnow,
) -> FastAPI:
    settings = settings or Settings.from_env()
    services = Services(
        settings=settings,
        db=db or Database(settings.database_url),
        limits=limits or load_tier_limits(settings.tier_limits_path),
        extractor=extractor or make_extractor(settings),
        clock=clock,
    )
    application = FastAPI(
        title="Penciled API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.state.services = services
    application.add_exception_handler(
        RequestValidationError,
        content_free_validation_handler,  # type: ignore[arg-type]
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)
    application.add_middleware(AccessLogMiddleware)
    application.include_router(router)
    return application


app = create_app()
