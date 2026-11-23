"""FastAPI application entry point.

Hard rule 3: no screenshot content (OCR text, image bytes, extracted fields,
model output, request bodies) may appear in logs or error responses.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

SCHEMA_VERSION = 1

app = FastAPI(title="Penciled API", version="0.1.0", docs_url=None, redoc_url=None)


@app.exception_handler(RequestValidationError)
async def content_free_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Replace FastAPI's default 422, which echoes the request input.

    The body is deliberately constant: no field values, no `input`, no `loc`.
    SPR-04 may add an enum-only reason code; it must never carry request data.
    """
    return JSONResponse(status_code=422, content={"error": "invalid_request"})


@app.get("/v1/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "schema_version": SCHEMA_VERSION}
