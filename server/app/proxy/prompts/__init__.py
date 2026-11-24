"""Frozen, versioned prompts (hard rule 9: a prompt changes only through a
human-approved baseline-bump commit with the eval report attached).

Each version directory holds `system.txt` (the cacheable system prompt: no
timestamps, ids or per-request values, so the prefix is byte-stable),
`output_schema.json` (the model-facing structured-output schema, DESIGN 5.4) and
`manifest.json` pinning both files by sha256. Loading fails if a file drifts from
its pin, so an edit cannot ship without bumping the manifest in the same commit.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent
CURRENT_VERSION = "v1"


class PromptDriftError(RuntimeError):
    """A prompt file no longer matches its manifest pin."""


@dataclass(frozen=True)
class PromptBundle:
    version: str
    system: str
    output_schema: dict[str, Any]
    system_sha256: str
    schema_sha256: str


def _read_normalised(path: Path) -> bytes:
    # Normalise line endings so a CRLF checkout cannot change the cached prefix.
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@cache
def load_prompt(version: str = CURRENT_VERSION) -> PromptBundle:
    folder = PROMPTS_DIR / version
    manifest = json.loads((folder / "manifest.json").read_text("utf-8"))
    system_b = _read_normalised(folder / "system.txt")
    schema_b = _read_normalised(folder / "output_schema.json")
    if sha256_hex(system_b) != manifest["system_sha256"]:
        raise PromptDriftError("system.txt does not match its manifest pin")
    if sha256_hex(schema_b) != manifest["output_schema_sha256"]:
        raise PromptDriftError("output_schema.json does not match its manifest pin")
    if manifest["prompt_version"] != version:
        raise PromptDriftError("manifest prompt_version does not match its directory")
    return PromptBundle(
        version=version,
        system=system_b.decode("utf-8"),
        output_schema=json.loads(schema_b),
        system_sha256=manifest["system_sha256"],
        schema_sha256=manifest["output_schema_sha256"],
    )
