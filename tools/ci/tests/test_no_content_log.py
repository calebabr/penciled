from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import no_content_log as ncl  # noqa: E402

BAD = HERE / "fixtures" / "bad"
GOOD = HERE / "fixtures" / "good"
SCRIPT = HERE.parent / "no_content_log.py"


def _lines(findings: list[ncl.Finding], name: str) -> set[int]:
    return {f.line for f in findings if f.path.endswith(name)}


def test_bad_python_fixture_flagged() -> None:
    lines = _lines(ncl.scan([BAD / "server_bad.py"]), "server_bad.py")
    assert lines == {7, 8, 12, 13}


def test_bad_ts_fixture_flagged() -> None:
    lines = _lines(ncl.scan([BAD / "mobile_bad.ts"]), "mobile_bad.ts")
    assert lines == {2, 3, 7, 8}


def test_bad_kotlin_fixture_flagged() -> None:
    lines = _lines(ncl.scan([BAD / "Worker_bad.kt"]), "Worker_bad.kt")
    assert lines == {4, 5, 6}


def test_good_fixtures_clean() -> None:
    assert ncl.scan([GOOD]) == []


@pytest.mark.parametrize(
    "src",
    [
        "logger.info('x %s', ocrText)",
        "logger.info('x %s', OCR_TEXT)",
        "log.debug(image_bytes)",
        "logging.error('%s', req.extractedFields)",
        "logger.info('%s', await request.json())",
        "logger.info('%s', payload.fields)",
    ],
)
def test_python_content_names(src: str) -> None:
    assert ncl.scan_python(Path("x.py"), src, forbid_print=False)


def test_print_forbidden_in_server_app() -> None:
    findings = ncl.scan_python(Path("x.py"), "print('hello')", forbid_print=True)
    assert len(findings) == 1 and "print()" in findings[0].message


def test_print_without_content_allowed_outside_server() -> None:
    assert ncl.scan_python(Path("x.py"), "print('hello')", forbid_print=False) == []


def test_findings_do_not_echo_source() -> None:
    findings = ncl.scan_clike(Path("a.ts"), 'console.log("SECRET-CANARY", ocrText)')
    assert findings and all("SECRET-CANARY" not in str(f) for f in findings)


def test_fixtures_excluded_from_directory_walk() -> None:
    assert ncl.scan([HERE]) == []


def test_cli_exit_codes() -> None:
    bad = subprocess.run([sys.executable, str(SCRIPT), str(BAD)], capture_output=True, text=True)
    good = subprocess.run([sys.executable, str(SCRIPT), str(GOOD)], capture_output=True, text=True)
    assert bad.returncode == 1 and "server_bad.py:7:" in bad.stdout
    assert good.returncode == 0


def test_repo_default_roots_clean() -> None:
    assert ncl.main([]) == 0
