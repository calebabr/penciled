"""DELETE /v1/me (SEC-DEL-ALL, F7d): zero rows for the token_hash in every table."""

from __future__ import annotations

import sqlalchemy as sa
from srv_support import Harness, extract_body

from app.auth.tokens import hash_secret
from app.db.schema import metadata


def _rows_for(h: Harness, token_hash: str) -> dict[str, int]:
    out: dict[str, int] = {}
    insp_tables = sa.inspect(h.engine).get_table_names()
    with h.engine.connect() as conn:
        for name in insp_tables:
            table = sa.Table(name, sa.MetaData(), autoload_with=conn)
            if "token_hash" in table.c:
                q = sa.select(sa.func.count()).where(table.c.token_hash == token_hash)
                out[name] = int(conn.execute(q).scalar_one())
    return out


def test_delete_leaves_zero_rows_everywhere(harness: Harness) -> None:
    h = harness
    tok, other = h.register(), h.register()
    th = hash_secret(tok)
    for i in range(3):  # seed N items
        assert (
            h.extract(tok, extract_body(idempotency_key=f"hmacd:text:p7:1:{i}")).status_code == 200
        )
    h.extract(other, extract_body())
    before = _rows_for(h, th)
    assert before["token"] == 1 and before["usage_daily"] == 1 and before["idempotency"] == 3
    assert len(h.services.cache) == 4

    resp = h.client.delete("/v1/me", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 204
    assert resp.content == b""

    after = _rows_for(h, th)
    assert after and all(n == 0 for n in after.values()), after
    # Every live table with a token_hash column was checked (introspection, not a list).
    assert set(after) == {t.name for t in metadata.sorted_tables if "token_hash" in t.c}
    assert len(h.services.cache) == 1  # only the other token's result remains
    assert _rows_for(h, hash_secret(other))["token"] == 1
    # The token is dead.
    assert h.extract(tok, extract_body()).status_code == 401
    assert h.client.delete("/v1/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 401


def test_delete_requires_auth(harness: Harness) -> None:
    resp = harness.client.delete("/v1/me")
    assert resp.status_code == 401
    assert resp.json() == {"schema_version": 1, "code": "unauthorized"}


def test_tables_without_token_column_are_unlinkable(harness: Harness) -> None:
    # metric_daily and spend_daily survive deletion because they carry no token id.
    for name in ("metric_daily", "spend_daily", "invite"):
        cols = {c["name"] for c in sa.inspect(harness.engine).get_columns(name)}
        assert not any("token" in c for c in cols), (name, cols)
