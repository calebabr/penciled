"""Round-trip helper: parse a batch of values with the generated pydantic models.

stdin:  [{"schema": "<stem>", "data": <json>}, ...]
stdout: [{"ok": true, "data": <canonical>} | {"ok": false, "paths": ["a.b.0", ...]}, ...]
Only error locations are reported (never input values).
Run: python -m penciled_contracts.cli   (after `pip install -e shared/python`)
"""

from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import ValidationError

from .api import canonical
from .generated import SCHEMAS


def run(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        name = item["schema"]
        if name not in SCHEMAS:
            out.append({"ok": False, "paths": [f"<unknown schema {name}>"]})
            continue
        try:
            out.append({"ok": True, "data": canonical(name, item["data"])})
        except ValidationError as exc:
            out.append({"ok": False, "paths": [".".join(map(str, e["loc"])) for e in exc.errors()]})
    return out


if __name__ == "__main__":
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    sys.stdout.buffer.write(json.dumps(run(payload)).encode("utf-8"))
