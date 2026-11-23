"""COMP-QUOTA (D25): limits come from tier_limits config; tier comes from the token row."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from pydantic import ValidationError
from srv_support import Harness, MakeHarness, extract_body

from app.auth.tokens import hash_secret
from app.config import TierLimits, load_tier_limits
from app.db.schema import metric_daily, token
from app.quota.service import SHADOW_METRIC
from app.settings import Settings


def _limits(free: int, pro: int, shadow: int | None = None) -> TierLimits:
    return TierLimits.model_validate(
        {
            "schema_version": 1,
            "near_fraction": 0.8,
            "tiers": {
                "free": {"daily_limit": free, "shadow_threshold": shadow},
                "pro": {"daily_limit": pro, "shadow_threshold": None},
            },
        }
    )


def _call(h: Harness, tok: str, i: int, **kw: object) -> int:
    body = extract_body(idempotency_key=f"hmacq:text:p7:1:{i}", **kw)
    return int(h.extract(tok, body).status_code)


def test_packaged_beta_limits() -> None:
    limits = load_tier_limits()
    assert limits.for_tier("free").daily_limit == 100
    assert limits.for_tier("free").shadow_threshold == 30


def test_config_change_changes_enforced_limit(make_harness: MakeHarness) -> None:
    for limit in (2, 3):
        h = make_harness(limits=_limits(free=limit, pro=50))
        tok = h.register()
        statuses = [_call(h, tok, i) for i in range(limit + 1)]
        assert statuses == [200] * limit + [503]


def test_config_file_override_path(tmp_path: Path, make_harness: MakeHarness) -> None:
    cfg = tmp_path / "tier_limits.json"
    cfg.write_text(json.dumps(_limits(free=1, pro=1).model_dump()), "utf-8")
    limits = load_tier_limits(str(cfg))
    h = make_harness(limits=limits)
    tok = h.register()
    assert [_call(h, tok, i) for i in range(2)] == [200, 503]


def test_cap_body_is_basic_and_no_provider_call(make_harness: MakeHarness) -> None:
    h = make_harness(limits=_limits(free=1, pro=1))
    tok = h.register()
    _call(h, tok, 0)
    resp = h.extract(tok, extract_body(idempotency_key="hmacq:text:p7:1:1"))
    assert resp.json() == {"schema_version": 1, "code": "service_paused", "basic": True}
    assert h.extractor.provider_calls == 1
    # A done duplicate is still served from memory at the cap (it costs nothing).
    assert _call(h, tok, 0) == 200


def test_tier_set_in_db_changes_limit(make_harness: MakeHarness) -> None:
    h = make_harness(limits=_limits(free=1, pro=3))
    tok = h.register()
    assert [_call(h, tok, i) for i in range(2)] == [200, 503]
    with h.engine.begin() as conn:
        conn.execute(
            token.update().where(token.c.token_hash == hash_secret(tok)).values(tier="pro")
        )
    resp = h.extract(tok, extract_body(idempotency_key="hmacq:text:p7:1:7"))
    assert resp.status_code == 200
    assert resp.json()["quota"]["tier"] == "pro"


def test_client_cannot_set_tier(make_harness: MakeHarness) -> None:
    h = make_harness(limits=_limits(free=1, pro=50))
    tok = h.register()
    resp = h.extract(tok, extract_body(tier="pro", quota={"tier": "pro", "state": "ok"}))
    assert resp.status_code == 200
    assert resp.json()["quota"] == {"tier": "free", "state": "exhausted"}
    assert _call(h, tok, 5, tier="pro") == 503


def test_quota_state_near_and_exhausted(make_harness: MakeHarness) -> None:
    h = make_harness(limits=_limits(free=5, pro=5))
    tok = h.register()
    states = []
    for i in range(5):
        resp = h.extract(tok, extract_body(idempotency_key=f"hmacq:text:p7:1:{i}"))
        states.append(resp.json()["quota"]["state"])
    assert states == ["ok", "ok", "ok", "near", "exhausted"]


def test_shadow_threshold_counted_once_without_token(make_harness: MakeHarness) -> None:
    h = make_harness(limits=_limits(free=10, pro=10, shadow=2), settings=Settings())
    tok = h.register()
    for i in range(5):
        _call(h, tok, i)
    with h.engine.connect() as conn:
        rows = list(conn.execute(sa.select(metric_daily)))
    assert [(r.name, r.dim, r.n) for r in rows] == [(SHADOW_METRIC, "free", 1)]


def test_tier_limits_must_cover_every_tier() -> None:
    with pytest.raises(ValidationError):
        TierLimits.model_validate(
            {"schema_version": 1, "near_fraction": 0.8, "tiers": {"free": {"daily_limit": 1}}}
        )
    with pytest.raises(ValidationError):
        TierLimits.model_validate(
            {
                "schema_version": 1,
                "near_fraction": 0.8,
                "tiers": {
                    "free": {"daily_limit": 1},
                    "pro": {"daily_limit": 1},
                    "beta": {"daily_limit": 1},
                },
            }
        )
