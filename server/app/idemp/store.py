"""COMP-IDEMP: status in Postgres, result in process memory (D20.2, seam 2).

- The DB row holds key hash, token hash, status (in_flight | done | failed) and
  timestamps. There is no result column; results live in `ResultCache` for 10 min
  and never reach disk or database backups.
- key_hash = sha256(token_hash, idempotency_key). The client key carries the mode
  segment (text | img), so a text key and an img key never map to the same row or
  cache entry; scoping by token keeps one token's key away from another's.
- in_flight rows are a short lease (a crashed request frees its key); done/failed
  rows live for the result TTL. Expired rows are purged on read and by a sweep.
"""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from app.db.engine import as_utc, insert_ignore
from app.db.schema import idempotency


def key_hash(token_hash: str, idempotency_key: str) -> str:
    return hashlib.sha256(f"{token_hash}\n{idempotency_key}".encode()).hexdigest()


class ResultCache:
    """Thread-safe in-process TTL map: key_hash -> response dict. Bounded (oldest evicted)."""

    def __init__(self, ttl: timedelta, max_entries: int) -> None:
        self.ttl = ttl
        self.max_entries = max_entries
        self._data: OrderedDict[str, tuple[datetime, str, dict[str, Any]]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, kh: str, now: datetime) -> dict[str, Any] | None:
        with self._lock:
            item = self._data.get(kh)
            if item is None:
                return None
            if item[0] <= now:
                del self._data[kh]
                return None
            return item[2]

    def put(self, kh: str, token_hash: str, value: dict[str, Any], now: datetime) -> None:
        with self._lock:
            self._data[kh] = (now + self.ttl, token_hash, value)
            self._data.move_to_end(kh)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)

    def purge_token(self, token_hash: str) -> None:
        with self._lock:
            for kh in [k for k, v in self._data.items() if v[1] == token_hash]:
                del self._data[kh]

    def sweep(self, now: datetime) -> None:
        with self._lock:
            for kh in [k for k, v in self._data.items() if v[0] <= now]:
                del self._data[kh]

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        return len(self._data)


ClaimKind = Literal["new", "in_flight", "cached"]


@dataclass(frozen=True)
class Claim:
    kind: ClaimKind
    cached: dict[str, Any] | None = None
    # A done key whose result was gone from memory (restart); re-run once, counted.
    memory_miss: bool = False


def claim(
    conn: Connection,
    cache: ResultCache,
    kh: str,
    token_hash: str,
    now: datetime,
    lease: timedelta,
) -> Claim:
    row = conn.execute(
        sa.select(idempotency.c.status, idempotency.c.expires_at).where(
            idempotency.c.key_hash == kh
        )
    ).first()
    if row is not None and as_utc(row.expires_at) > now:
        memory_miss = False
        if row.status == "in_flight":
            return Claim("in_flight")
        if row.status == "done":
            cached = cache.get(kh, now)
            if cached is not None:
                return Claim("cached", cached=cached)
            memory_miss = True
        # failed, or done without a result in memory: take the key back (compare-and-set).
        taken = conn.execute(
            idempotency.update()
            .where(idempotency.c.key_hash == kh, idempotency.c.status == row.status)
            .values(status="in_flight", updated_at=now, expires_at=now + lease)
            .returning(idempotency.c.key_hash)
        ).first()
        if taken is None:
            return Claim("in_flight")
        return Claim("new", memory_miss=memory_miss)
    if row is not None:
        conn.execute(
            idempotency.delete().where(
                idempotency.c.key_hash == kh, idempotency.c.expires_at <= now
            )
        )
    inserted = insert_ignore(
        conn,
        idempotency,
        {
            "key_hash": kh,
            "token_hash": token_hash,
            "status": "in_flight",
            "created_at": now,
            "updated_at": now,
            "expires_at": now + lease,
        },
    )
    return Claim("new") if inserted else Claim("in_flight")


def finish(
    conn: Connection, kh: str, status: Literal["done", "failed"], now: datetime, ttl: timedelta
) -> None:
    conn.execute(
        idempotency.update()
        .where(idempotency.c.key_hash == kh)
        .values(status=status, updated_at=now, expires_at=now + ttl)
    )


def release(conn: Connection, kh: str) -> None:
    """Drop a claim that never reached the provider (e.g. the daily cap)."""
    conn.execute(idempotency.delete().where(idempotency.c.key_hash == kh))


def sweep(conn: Connection, now: datetime) -> None:
    conn.execute(idempotency.delete().where(idempotency.c.expires_at <= now))
