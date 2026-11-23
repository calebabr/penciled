#!/usr/bin/env python3
"""Prove the secret scan blocks a planted fake key (SPR-01 exit criterion).

Builds fake keys at runtime (the literals never exist in this repo), plants them in
a throwaway directory and a throwaway git repo, runs gitleaks with the repo's
.gitleaks.toml, and asserts a non-zero exit. A clean control must exit zero.

Usage: python tools/ci/test_secret_scan.py [--gitleaks PATH]
Exit 0 = scanner behaves as required. Stdlib only.
"""

from __future__ import annotations

import argparse
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / ".gitleaks.toml"
B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
B64URL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def _rand(alphabet: str, n: int) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(n))


def fake_aws_key_id() -> str:
    return "AK" + "IA" + _rand(B32, 16)


def fake_anthropic_key() -> str:
    return "sk" + "-ant-" + "api03-" + _rand(B64URL, 93) + "AA"


def run_scan(gitleaks: str, mode: str, target: Path) -> int:
    cmd = [
        gitleaks,
        mode,
        str(target),
        "--config",
        str(CONFIG),
        "--redact",
        "--no-banner",
        "--exit-code",
        "1",
        "--log-level",
        "warn",
    ]
    return subprocess.run(cmd, capture_output=True, text=True).returncode


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=scan-test",
            "-c",
            "user.email=scan-test@invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gitleaks", default=shutil.which("gitleaks"))
    args = ap.parse_args()
    if not args.gitleaks:
        print("FAIL: gitleaks not found on PATH (pass --gitleaks)")
        return 2

    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        clean = root / "clean"
        clean.mkdir()
        (clean / "config.py").write_text('API_URL = "https://api.example.invalid"\n')
        if run_scan(args.gitleaks, "dir", clean) != 0:
            failures.append("control: clean directory was flagged")

        for name, key in (("aws", fake_aws_key_id()), ("anthropic", fake_anthropic_key())):
            d = root / f"dir-{name}"
            d.mkdir()
            (d / "settings.py").write_text(f'KEY = "{key}"\n')
            if run_scan(args.gitleaks, "dir", d) == 0:
                failures.append(f"dir scan missed planted fake {name} key")

        repo = root / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        (repo / "app.ts").write_text(f'export const k = "{fake_anthropic_key()}";\n')
        _git(repo, "add", "app.ts")
        _git(repo, "commit", "-q", "-m", "plant")
        # Remove it in a later commit: history scan must still catch it.
        (repo / "app.ts").write_text("export const k = process.env.K;\n")
        _git(repo, "commit", "-q", "-am", "remove")
        if run_scan(args.gitleaks, "git", repo) == 0:
            failures.append("git history scan missed a key removed in a later commit")

    if failures:
        for f in failures:
            print("FAIL:", f)
        return 1
    print("OK: gitleaks blocks planted fake keys (dir + git history); clean control passes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
