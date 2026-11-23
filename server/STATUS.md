# server/STATUS.md

**State:** SPR-01 skeleton (COMP-REPO). No business logic yet; COMP-SERVER-CORE (SPR-04) builds on this.

## Done (SPR-01)
- [x] `server/pyproject.toml`: requires-python >=3.11 (CI runs 3.12; builder's machine has 3.11.9). Deps fastapi, pydantic v2, uvicorn; dev extra pytest, httpx, ruff, mypy (strict).
- [x] Packages `app/{api,auth,quota,idemp,db,proxy,resolver,gate}` (empty `__init__.py`).
- [x] `app/main.py`: `GET /v1/health` -> `{"status":"ok","schema_version":1}`; OpenAPI docs UIs disabled.
- [x] Content-free `RequestValidationError` handler: every 422 body is exactly `{"error":"invalid_request"}` (hard rule 3). Canary tests in `tests/test_validation_canary.py` (bad types, extra fields, malformed JSON, wrong top-level type).
- [x] Ruff rule T20 bans `print` in `app/`.

## Local commands (from `server/`)
```
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"   # Windows path
.venv/Scripts/python -m pytest -q
.venv/Scripts/ruff check .
.venv/Scripts/mypy app
```

## Notes / next
- SPR-04 may add an enum-only reason code to the 422 body; it must never include `input`, `loc` values or any request data. Keep the canary green.
- Starlette warns that `httpx` with its TestClient is deprecated in favour of `httpx2`; harmless for now, revisit when bumping deps.
- Host body logging must be off when the host is chosen (SPR-04).
