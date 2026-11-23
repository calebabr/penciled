"""Operator commands (run with DATABASE_URL set from the host secret store):

    python -m app.admin add-invite [--uses N]   # writes one new invite code to stdout
    python -m app.admin revoke-invite CODE

The invite code is shown once to the operator who asked for it; only its hash is
stored. Nothing here writes to logs.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from app.auth.tokens import create_invite, hash_secret, new_invite_code
from app.db.engine import Database
from app.db.schema import invite
from app.settings import Settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.admin")
    sub = parser.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add-invite")
    add.add_argument("--uses", type=int, default=1)
    rev = sub.add_parser("revoke-invite")
    rev.add_argument("code")
    args = parser.parse_args(argv)

    db = Database(Settings.from_env().database_url)
    now = datetime.now(UTC)
    with db.engine.begin() as conn:
        if args.cmd == "add-invite":
            code = new_invite_code()
            create_invite(conn, code, now, max_uses=args.uses)
            sys.stdout.write(code + "\n")
        else:
            conn.execute(
                invite.update()
                .where(invite.c.code_hash == hash_secret(args.code))
                .values(revoked_at=now)
            )
    db.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
