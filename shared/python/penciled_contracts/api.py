"""Parse and dump any top-level contract by its schema stem (e.g. "extract_request").

Works for both model roots and union roots (ProposedAction, InboxEntry) through
pydantic TypeAdapters. Output is canonical JSON (see base.ContractModel).
"""

from __future__ import annotations

from functools import cache
from typing import Any

from pydantic import TypeAdapter

from .generated import SCHEMAS


@cache
def adapter(name: str) -> TypeAdapter[Any]:
    if name not in SCHEMAS:
        raise KeyError(f"unknown contract {name!r}")
    return TypeAdapter(SCHEMAS[name])


def parse(name: str, data: Any) -> Any:
    """Validate python data (e.g. from json.loads). Raises pydantic.ValidationError."""
    return adapter(name).validate_python(data)


def dump(name: str, value: Any) -> Any:
    """Canonical JSON-compatible form of a parsed value."""
    return adapter(name).dump_python(value, mode="json", by_alias=True, exclude_unset=True)


def canonical(name: str, data: Any) -> Any:
    """parse then dump: unknown keys dropped, defaults filled."""
    return dump(name, parse(name, data))
