"""COMP-IDEMP: status in the DB, result in memory only (D20.2, D20.6)."""

from __future__ import annotations

from datetime import timedelta

import sqlalchemy as sa
from srv_support import MakeHarness, extract_body

from app.db.schema import idempotency, metric_daily, usage_daily

TEXT_KEY = "hmacsame:text:p7:1:0"
IMG_KEY = "hmacsame:img:p7:1:0"


def _rows(h: object, table: sa.Table) -> list[sa.Row[object]]:
    with h.engine.connect() as conn:  # type: ignore[attr-defined]
        return list(conn.execute(sa.select(table)))


def test_done_duplicate_served_from_memory_without_provider_call(
    make_harness: MakeHarness,
) -> None:
    h = make_harness()
    tok = h.register()
    first = h.extract(tok, extract_body(idempotency_key=TEXT_KEY))
    assert first.status_code == 200
    assert h.extractor.provider_calls == 1
    h.clock.advance(minutes=9)
    again = h.extract(tok, extract_body(idempotency_key=TEXT_KEY))
    assert again.status_code == 200
    assert again.json()["request_id"] == first.json()["request_id"]
    assert h.extractor.provider_calls == 1  # unchanged: served from memory
    with h.engine.connect() as conn:
        assert conn.execute(sa.select(usage_daily.c.extractions)).scalar_one() == 1
        status = conn.execute(sa.select(idempotency.c.status)).scalar_one()
    assert status == "done"


def test_text_and_img_keys_never_collide(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    assert h.extract(tok, extract_body(idempotency_key=TEXT_KEY)).status_code == 200
    img = h.extract(tok, extract_body(idempotency_key=IMG_KEY, image_b64="QUJD"))
    assert img.status_code == 200
    assert h.extractor.provider_calls == 2  # the img call was never served the text result
    rows = _rows(h, idempotency)
    assert len(rows) == 2 and len({r.key_hash for r in rows}) == 2
    assert len(h.services.cache) == 2


def test_rerun_segment_is_a_new_call(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    h.extract(tok, extract_body(idempotency_key="hmacsame:text:p7:1:0"))
    h.extract(tok, extract_body(idempotency_key="hmacsame:text:p7:1:1"))
    assert h.extractor.provider_calls == 2


def test_same_key_different_tokens_are_separate(make_harness: MakeHarness) -> None:
    h = make_harness()
    a, b = h.register(), h.register()
    h.extract(a, extract_body(idempotency_key=TEXT_KEY))
    h.extract(b, extract_body(idempotency_key=TEXT_KEY))
    assert h.extractor.provider_calls == 2


def test_result_expires_after_ten_minutes(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    h.extract(tok, extract_body(idempotency_key=TEXT_KEY))
    h.clock.advance(minutes=10, seconds=1)
    assert h.extract(tok, extract_body(idempotency_key=TEXT_KEY)).status_code == 200
    assert h.extractor.provider_calls == 2


def test_memory_miss_reruns_once_and_is_counted(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    h.extract(tok, extract_body(idempotency_key=TEXT_KEY))
    h.services.cache.clear()  # simulates a container restart
    assert h.extract(tok, extract_body(idempotency_key=TEXT_KEY)).status_code == 200
    assert h.extract(tok, extract_body(idempotency_key=TEXT_KEY)).status_code == 200
    assert h.extractor.provider_calls == 2  # re-run once, then memory again
    rows = _rows(h, metric_daily)
    assert [(r.name, r.dim, r.n) for r in rows] == [("idem_memory_miss", "all", 1)]


def test_stale_in_flight_lease_is_reclaimed(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    from app.auth.tokens import hash_secret
    from app.idemp.store import key_hash

    th = hash_secret(tok)
    now = h.clock()
    with h.engine.begin() as conn:
        conn.execute(
            idempotency.insert().values(
                key_hash=key_hash(th, TEXT_KEY),
                token_hash=th,
                status="in_flight",
                created_at=now,
                updated_at=now,
                expires_at=now - timedelta(seconds=1),  # lease expired
            )
        )
    assert h.extract(tok, extract_body(idempotency_key=TEXT_KEY)).status_code == 200


def test_idempotency_rows_hold_no_result(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    resp = h.extract(tok, extract_body(idempotency_key=TEXT_KEY))
    with h.engine.connect() as conn:
        row = conn.execute(sa.select(idempotency)).one()
    assert set(row._mapping) == {
        "key_hash",
        "token_hash",
        "status",
        "created_at",
        "updated_at",
        "expires_at",
    }
    assert resp.json()["request_id"] not in [str(v) for v in row]
    assert TEXT_KEY not in [str(v) for v in row]  # the raw client key is hashed too


def test_sweep_purges_expired_rows(make_harness: MakeHarness) -> None:
    h = make_harness()
    tok = h.register()
    h.extract(tok, extract_body(idempotency_key=TEXT_KEY))
    h.clock.advance(minutes=11)
    h.extract(tok, extract_body(idempotency_key="hmacother:text:p7:1:0"))
    keys = {r.status for r in _rows(h, idempotency)}
    assert len(_rows(h, idempotency)) == 1 and keys == {"done"}
