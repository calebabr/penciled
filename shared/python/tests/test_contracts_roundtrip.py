"""COMP-CONTRACTS acceptance: pydantic <-> zod round trip on shared/fixtures.

Round trip per fixture: Python parses input -> canonical JSON -> zod parses (node) ->
serializes -> Python parses again; every stage must equal the fixture's `expected`
(unknown keys gone, defaults filled, schema_version present). Negative fixtures must be
rejected by pydantic, zod and the JSON Schema itself. Needs `node` (>= 22.18) on PATH and
the root `npm ci` (for zod).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from referencing import Registry, Resource

from penciled_contracts import SCHEMA_VERSION, SCHEMAS, canonical, parse

SHARED = Path(__file__).resolve().parents[2]
FIXTURES = SHARED / "fixtures"
SCHEMA_DIR = SHARED / "schema"
ZOD_HELPER = SHARED / "tools" / "zod_parse.ts"

POSITIVE = sorted(FIXTURES.glob("*.json"))
NEGATIVE = sorted((FIXTURES / "negative").glob("*.json"))
RULES_FILES = [SHARED / "rules" / "rules.json"]
RULES_FIXTURE_FILES = sorted((SHARED / "rules" / "fixtures").glob("*.json"))


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def node() -> str:
    exe = shutil.which("node")
    if exe is None:
        pytest.fail("node is required for the zod leg of the round trip")
    return exe


def zod_parse(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proc = subprocess.run(
        [node(), str(ZOD_HELPER)],
        input=json.dumps(items),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=SHARED,
        check=False,
    )
    assert proc.returncode == 0, f"zod helper failed: {proc.stderr[-2000:]}"
    out: list[dict[str, Any]] = json.loads(proc.stdout)
    return out


def carries_schema_version(name: str) -> bool:
    doc = load(SCHEMA_DIR / f"{name}.schema.json")
    if "schema_version" in doc.get("properties", {}):
        return True
    members = [m["$ref"].split("/")[-1] for m in doc.get("oneOf", [])]
    return bool(members) and all("schema_version" in doc["$defs"][m]["properties"] for m in members)


# ------------------------------------------------------------------ coverage


def test_fixture_coverage() -> None:
    fx = [load(p) for p in POSITIVE]
    assert len(fx) >= 20
    assert {f["schema"] for f in fx} == set(SCHEMAS), "every top-level schema needs a fixture"

    responses = [f["expected"] for f in fx if f["schema"] == "extract_response"]
    subtypes = {r.get("nothing_subtype") for r in responses if r["class"] == "nothing"}
    assert subtypes == {"receipt_order", "shipping", "booking", "meme", "other"}
    origins = {
        a["deadline_origin"] for r in responses for a in r["actions"] if a["kind"] == "deadline"
    }
    assert origins == {"printed_return_by", "other"}
    assert any("quota" in r for r in responses) and any("quota" not in r for r in responses)

    requests = [f for f in fx if f["schema"] == "extract_request"]
    assert any("tier" in f["input"] and "tier" not in f["expected"] for f in requests)
    assert any(f["schema"] == "worker_config" for f in fx)
    assert any(f["schema"] == "inbox" and f["input"]["status"] == "pending_app" for f in fx)
    assert len(NEGATIVE) >= 3


# ------------------------------------------------------------------ python leg


@pytest.mark.parametrize("path", POSITIVE, ids=lambda p: p.stem)
def test_python_canonical(path: Path) -> None:
    f = load(path)
    out = canonical(f["schema"], f["input"])
    assert out == f["expected"]
    if carries_schema_version(f["schema"]):
        assert out["schema_version"] == SCHEMA_VERSION


@pytest.mark.parametrize("path", NEGATIVE, ids=lambda p: p.stem)
def test_python_rejects_negative(path: Path) -> None:
    f = load(path)
    with pytest.raises(ValidationError):
        parse(f["schema"], f["input"])


# ------------------------------------------------------------------ cross-language


def test_roundtrip_python_zod_python() -> None:
    fx = [load(p) for p in POSITIVE]
    py1 = [canonical(f["schema"], f["input"]) for f in fx]
    zod = zod_parse([{"schema": f["schema"], "data": d} for f, d in zip(fx, py1, strict=True)])
    for path, f, z in zip(POSITIVE, fx, zod, strict=True):
        assert z["ok"], f"{path.stem}: zod rejected python output at {z.get('paths')}"
        assert z["data"] == f["expected"], f"{path.stem}: zod output differs"
        py2 = canonical(f["schema"], z["data"])
        assert py2 == f["expected"], f"{path.stem}: second python parse differs"
        if carries_schema_version(f["schema"]):
            assert z["data"]["schema_version"] == SCHEMA_VERSION


def test_zod_rejects_negative() -> None:
    fx = [load(p) for p in NEGATIVE]
    res = zod_parse([{"schema": f["schema"], "data": f["input"]} for f in fx])
    for path, r in zip(NEGATIVE, res, strict=True):
        assert not r["ok"], f"{path.stem}: zod accepted a negative fixture"


# ------------------------------------------------------------------ JSON Schema itself


def registry() -> Registry[Any]:
    reg: Registry[Any] = Registry()
    for p in SCHEMA_DIR.glob("*.schema.json"):
        doc = load(p)
        reg = reg.with_resource(doc["$id"], Resource.from_contents(doc))
    return reg


def validator(name: str) -> Draft202012Validator:
    doc = load(SCHEMA_DIR / f"{name}.schema.json")
    return Draft202012Validator(doc, registry=registry())


def test_schemas_are_valid_2020_12() -> None:
    for p in SCHEMA_DIR.glob("*.schema.json"):
        Draft202012Validator.check_schema(load(p))


@pytest.mark.parametrize("path", POSITIVE, ids=lambda p: p.stem)
def test_json_schema_accepts_positive(path: Path) -> None:
    f = load(path)
    v = validator(f["schema"])
    v.validate(f["input"])
    v.validate(f["expected"])


@pytest.mark.parametrize("path", NEGATIVE, ids=lambda p: p.stem)
def test_json_schema_rejects_negative(path: Path) -> None:
    f = load(path)
    assert not validator(f["schema"]).is_valid(f["input"])


# ------------------------------------------------------------------ committed data files


def test_rules_json_and_rules_fixtures_are_valid() -> None:
    assert RULES_FIXTURE_FILES, "shared/rules/fixtures needs at least one file"
    items = [{"schema": "rules", "data": load(p)} for p in RULES_FILES]
    items += [{"schema": "rules_fixture", "data": load(p)} for p in RULES_FIXTURE_FILES]
    for it in items:
        validator(it["schema"]).validate(it["data"])
        assert canonical(it["schema"], it["data"]) == it["data"]
    assert all(r["ok"] for r in zod_parse(items))


def test_generated_code_is_up_to_date() -> None:
    proc = subprocess.run(
        [node(), str(SHARED / "tools" / "generate.mjs"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
