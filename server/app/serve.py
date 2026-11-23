"""Production entry point: `python -m app.serve`.

One process, one worker: idempotency results live in this process's memory
(D20.2), so the beta runs exactly one warm instance. uvicorn's access log is off
(AccessLogMiddleware logs route templates and statuses only), and every log line
goes through the scrubbing JSON formatter. No request body is ever logged.
"""

from __future__ import annotations

import os

import uvicorn

from app.logs import configure_logging


def main() -> None:
    configure_logging()
    uvicorn.run(
        "app.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8080")),
        workers=1,
        access_log=False,
        log_config=None,
        proxy_headers=True,
        forwarded_allow_ips="*",
        server_header=False,
    )


if __name__ == "__main__":
    main()
