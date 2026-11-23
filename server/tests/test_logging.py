"""SEC-LOG-NOCONTENT / SEC-LOG-SCRUB: log capture finds no body text, and the
formatter scrubs whatever a caller passes."""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Iterator

import pytest
from srv_support import Harness, extract_body

from app.logs import SCRUBBED, configure_logging, make_handler

MARKER = "MARKER-pizza-night-91c2"


@pytest.fixture
def out(caplog: pytest.LogCaptureFixture) -> Iterator[io.StringIO]:
    caplog.set_level(logging.DEBUG)
    stream = io.StringIO()
    handler = make_handler(stream)
    root = logging.getLogger()
    root.addHandler(handler)
    yield stream
    root.removeHandler(handler)


def _lines(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(x) for x in stream.getvalue().splitlines() if x.strip()]


def test_full_flow_logs_no_body_text(
    harness: Harness, out: io.StringIO, caplog: pytest.LogCaptureFixture
) -> None:
    tok = harness.register()
    body = extract_body(
        ocr={"lines": [{"t": MARKER, "c": 0.9}]},
        counters=[{"day": "2026-11-23", "name": "card_state", "dim": "ready", "n": 1}],
    )
    assert harness.extract(tok, body).status_code == 200
    assert harness.extract(tok, body).status_code == 200  # cached path
    harness.client.delete("/v1/me", headers={"Authorization": f"Bearer {tok}"})
    text = out.getvalue()
    assert MARKER not in caplog.text and MARKER not in text
    assert tok not in caplog.text and tok not in text  # bearer tokens are not logged either
    events = [(x.get("event"), x.get("outcome")) for x in _lines(out)]
    assert ("extract", "ok") in events and ("extract", "cached") in events
    access = [x for x in _lines(out) if x.get("event") == "http"]
    assert {x["route"] for x in access} >= {"/v1/register", "/v1/extract", "/v1/me"}
    assert all(
        set(x)
        <= {"ts", "level", "logger", "msg", "event", "method", "route", "status", "latency_ms"}
        for x in access
    )


def test_formatter_never_interpolates_args(out: io.StringIO) -> None:
    logging.getLogger("penciled.test").info("value %s", MARKER)
    logging.getLogger("thirdparty").warning(f"pre-formatted {MARKER}")
    logging.getLogger("uvicorn.error").info("Started %s", MARKER)
    assert MARKER not in out.getvalue()
    msgs = [x["msg"] for x in _lines(out)]
    assert msgs == ["value %s", SCRUBBED, "Started %s"]


def test_formatter_scrubs_extras_and_exceptions(out: io.StringIO) -> None:
    log = logging.getLogger("penciled.test")
    log.info("x", extra={"event": MARKER + " with spaces", "status": 200, "ocr": MARKER})
    try:
        raise ValueError(MARKER)
    except ValueError:
        log.exception("failed")
    text = out.getvalue()
    assert MARKER not in text
    first, second = _lines(out)
    assert first["event"] == SCRUBBED and first["status"] == 200 and "ocr" not in first
    assert second["exc_type"] == "ValueError" and second["frames"]


def test_configure_logging_silences_uvicorn_access() -> None:
    root = logging.getLogger()
    saved = list(root.handlers), root.level
    try:
        configure_logging()
        assert logging.getLogger("uvicorn.access").disabled
        assert logging.getLogger("uvicorn.access").propagate is False
        assert len(root.handlers) == 1
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
        for h in saved[0]:
            root.addHandler(h)
        root.setLevel(saved[1])
        logging.getLogger("uvicorn.access").disabled = False
        logging.getLogger("uvicorn.access").propagate = True
