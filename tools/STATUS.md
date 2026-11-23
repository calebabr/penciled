# tools/STATUS.md

**State:** SPR-01 (COMP-REPO) CI tooling in place.

## Done (SPR-01)
- [x] `tools/perf/`: placeholder for COMP-PERF (10k/30k seeder, measurement scripts).
- [x] `tools/ci/no_content_log.py` (stdlib only): scans `server/app`, `apps/mobile/{src,app,modules}` for log/print/console.*/logger.*/Log.*/Timber/Sentry breadcrumb calls whose arguments reference content-bearing names (ocr text, image bytes/base64, raw text, model output, extracted*, fields, request/req .body/.json/.form). Any `print(` in `server/app` fails. Python is parsed with `ast`; TS/JS/Kotlin/Java use call-start regex + paren balancing (multi-line calls covered). Output is `path:line: message` and never echoes source.
- [x] `tools/ci/tests/`: pytest with bad/good fixtures (py, ts, kt). Fixtures are skipped by directory walks of the real scan.
- [x] `tools/ci/test_secret_scan.py`: generates fake AWS and Anthropic-format keys at runtime (literals never stored), plants them in a temp dir and in a temp git repo (key removed in a later commit), asserts gitleaks exits non-zero; a clean control must exit 0.
- [x] Repo `.gitleaks.toml` extends gitleaks defaults; only allowlists git-ignored `node_modules/` and `.venv/` for local `dir` scans. Scanner pinned to 8.30.1 in CI (checksum-verified release download).
- [x] `.github/workflows/ci.yml`: jobs js (Node 22.x), python (3.12: ruff, mypy, pytest), secret-scan (full history + planted-key test), no-content-log. `permissions: contents: read`.

## Not verified locally
- CI green on an empty PR needs a push (builder approval).
- The js job depends on a root `package-lock.json` (for `npm ci` and the npm cache) from the mobile lane.

## Commands
```
python tools/ci/no_content_log.py
python tools/ci/test_secret_scan.py            # needs gitleaks on PATH
server/.venv/Scripts/python -m pytest tools/ci/tests
```
