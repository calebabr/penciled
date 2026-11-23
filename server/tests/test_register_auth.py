"""COMP-AUTH: /v1/register issues an opaque token stored only as a hash; 401/403 envelopes."""

from __future__ import annotations

import sqlalchemy as sa
from penciled_contracts.generated import ErrorResponse
from srv_support import Harness, extract_body

from app.auth.tokens import hash_secret
from app.db.schema import metadata, token


def _all_cells(harness: Harness) -> list[str]:
    cells: list[str] = []
    with harness.engine.connect() as conn:
        for table in metadata.sorted_tables:
            for row in conn.execute(sa.select(table)):
                cells.extend(str(v) for v in row)
    return cells


def test_register_issues_token_and_stores_only_hash(harness: Harness) -> None:
    code = harness.invite()
    resp = harness.client.post("/v1/register", json={"schema_version": 1, "invite_code": code})
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == 1
    assert body["tier"] == "free"
    assert body["token"].startswith("pcl_")
    assert resp.headers["cache-control"] == "no-store"
    cells = _all_cells(harness)
    assert body["token"] not in cells and code not in cells
    assert hash_secret(body["token"]) in cells


def test_register_client_cannot_set_tier(harness: Harness) -> None:
    code = harness.invite()
    resp = harness.client.post(
        "/v1/register", json={"schema_version": 1, "invite_code": code, "tier": "pro"}
    )
    assert resp.status_code == 200
    assert resp.json()["tier"] == "free"
    with harness.engine.connect() as conn:
        assert conn.execute(sa.select(token.c.tier)).scalar_one() == "free"


def test_register_403_unknown_invite(harness: Harness) -> None:
    resp = harness.client.post("/v1/register", json={"schema_version": 1, "invite_code": "nope"})
    assert resp.status_code == 403
    assert ErrorResponse.model_validate(resp.json()).code == "invalid_invite"


def test_register_403_invite_used_up(harness: Harness) -> None:
    code = harness.invite(uses=1)
    ok = harness.client.post("/v1/register", json={"schema_version": 1, "invite_code": code})
    assert ok.status_code == 200
    again = harness.client.post("/v1/register", json={"schema_version": 1, "invite_code": code})
    assert again.status_code == 403
    assert again.json() == {"schema_version": 1, "code": "invalid_invite"}


def test_register_413_oversized(harness: Harness) -> None:
    resp = harness.client.post(
        "/v1/register", json={"schema_version": 1, "invite_code": "x" * 5000}
    )
    assert resp.status_code == 413
    assert resp.json() == {"schema_version": 1, "code": "payload_too_large"}


def test_extract_401_variants(harness: Harness) -> None:
    body = extract_body()
    assert harness.extract(None, body).status_code == 401
    assert harness.extract("pcl_not-a-real-token", body).status_code == 401
    resp = harness.client.post("/v1/extract", json=body, headers={"Authorization": "Basic abc"})
    assert resp.status_code == 401
    assert resp.json() == {"schema_version": 1, "code": "unauthorized"}


def test_revoked_token_401(harness: Harness) -> None:
    tok = harness.register()
    with harness.engine.begin() as conn:
        conn.execute(token.update().values(revoked_at=harness.clock()))
    assert harness.extract(tok, extract_body()).status_code == 401


def test_401_before_body_is_read(harness: Harness) -> None:
    # An unauthenticated request is rejected even when its body is invalid.
    resp = harness.client.post("/v1/extract", content=b"not json")
    assert resp.status_code == 401
