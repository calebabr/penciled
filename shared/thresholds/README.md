# shared/thresholds

`thresholds_vN.json` files live here. Format: `shared/schema/thresholds.schema.json`
(type `ThresholdsFile` in `@penciled/shared` and `penciled_contracts`).

- **COMP-CALIB writes `thresholds_v1.json`** from the eval set (pooled Platt, cost rule
  "ask when p < 0.90"), reproducible from a fixed seed, in a human-approved baseline-bump commit
  with the eval report attached (hard rule 9). It is a release-candidate gate (CP3).
- Until then COMP-GATE runs on the DESIGN 5.5 initial constants. No thresholds file is committed
  in SPR-02; `shared/fixtures/thresholds_initial_constants.json` shows those constants in this
  format but is a test fixture, not something any component loads.
- `thresholds_version` must equal the file name suffix (`v1` for `thresholds_v1.json`) and is
  echoed as `ExtractResponse.thresholds_version`.
- Beta user data may only tighten thresholds; loosening needs a human-reviewed release.
