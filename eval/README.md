# eval/

Offline evaluation set and harness (COMP-EVALSET, COMP-EVALHARNESS, COMP-CALIB). Skeleton only as of SPR-01.

| Path | Contents |
|---|---|
| `generator/` | Playwright templates that render synthetic screenshots |
| `manifest.json` | One entry per image: source, license, split, sha256 (empty list until COMP-EVALSET) |
| `labels/` | Gold JSON per image |
| `images/synthetic/` | Committed synthetic renders |
| `images/own/` | Private real screenshots: git-ignored, only their hashes go in `manifest.json` |
| `harness/` | Runs the server pipeline over the set and scores it |
| `calib/` | Platt/logistic calibration; writes `shared/thresholds/` only via a human-approved baseline-bump commit |
| `reports/` | Eval reports attached to baseline bumps |

Rules: never commit real screenshots or their OCR text; never log image content (hard rule 3).
