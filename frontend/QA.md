# Verification — real-model update, 2026-10-26

Validated with Node 24.19.0, Next.js 16.4.3, Python 3.11 and installed Chromium. All model and training implementations and API response shapes were reused unchanged for this update. No package, checksum or TLS verification was disabled.

| Check | Current result |
|---|---|
| Data acquisition | All 12 raw files verified: FD001–FD004 train/test/RUL |
| Integrity | Pinned Git tree blob identities + frozen SHA-256; repeated `make data-all` passes |
| Real model bundles | 16 trained/evaluated, all required artifact SHA-256 hashes pass |
| Official test engine counts | FD001 100; FD002 259; FD003 100; FD004 248 |
| Python suite | **51 passed**, 12 dependency/model warnings, no skips (7.42 s) |
| Browser suite | **8 passed**, no skips (42.2 s), including live real-checkpoint API |
| ESLint / TypeScript / production build | Passed |
| Responsive screenshots | 15 recaptured at **360 / 768 / 1440 px**, viewport height 1000 px |
| Axe | No WCAG 2 A/AA or 2.1 AA violations in tested fleet/detail/explorer dark and explorer light states at each width |
| Browser console | Zero console errors/page exceptions during normal multi-view journeys at all three widths |
| Production Lighthouse mobile simulation | Performance **94**, accessibility **100** |
| Lighthouse timings | FCP 0.8 s; LCP 2.5 s; TBT 210 ms; CLS 0 |
| Initial fleet payload | **4,742 bytes transferred**, 18,160 bytes uncompressed catalog; full real histories load on entering analysis |
| Static / API parity | All 16 models checked with padded/full/final and perturbed windows; maximum batch difference **0.0000153 cycles** |
| Model importance | 21-sensor model-dependent permutation Δ MAE for all 16 models; up to 512 validation windows, seed 42 |
| What-if | Exact precomputed single-sensor perturbations for every exported cycle and four models; no interpolation |

The retained [Lighthouse HTML](qa/lighthouse.report.html) and [JSON](qa/lighthouse.report.json) are the final isolated production run. Initial eager loading of all full-resolution results scored 70; it was corrected by loading a small exact snapshot catalog first. Full real predictions remain available on demand. These scores are local measurements, not guarantees for a future portfolio deployment. Existing [contrast pairs](qa/contrast.json) remain valid because the token palette is unchanged.

## What was exercised

Python regression includes independent API comparisons of baseline and sensor-4 +10% predictions for every model/subset, hash verification of every required committed bundle, all four source-manifest memberships, real export/validation-engine membership, finite outputs, and exact catalog-snapshot consistency. Export generation additionally verified cycles 1, 29, 30 and final cycle against serving, plus a perturbed window.

Browser regression exercises search, health filtering and the risk-sorted fleet, replay/cursor/speed/reset, illustrative threshold alerts, palette/focus/keyboard/reduced motion, request failure/retry, themes, model arena and dataset explorer. The new four-subset test loads each real dataset and matches its Transformer what-if result to the corresponding exact static output. The live test uses a real FD004 XGBoost checkpoint, not a synthetic artifact, and checks a 30-row POST, successful result, controlled API 400, retry and recovery. The optional live branch is enabled with LIVE_UI_URL; without it that test is explicitly skipped. Expected negative-test HTTP errors are distinct from normal-path console errors.

## Measured reduced-budget test RMSE (cycles)

| Subset | XGBoost | LSTM | GRU | Transformer |
|---|---:|---:|---:|---:|
| FD001 | 12.78 | 40.57 | 40.50 | 17.54 |
| FD002 | 13.54 | 17.59 | 16.15 | 14.92 |
| FD003 | 13.29 | 42.31 | 36.94 | 18.19 |
| FD004 | 16.57 | 20.73 | 20.15 | 19.13 |

Single seed 42, three neural epochs, 120-tree XGBoost cap. No variance estimate or published-level accuracy is claimed. Exact metrics, predictions and settings are in results/portfolio, artifacts/portfolio and configs/portfolio. Original published multi-seed results remain unchanged.

## Limits and explicitly illustrative elements

Replay and importance use held-out validation engines that also informed checkpoint selection. Their residuals are not independent final test evidence; official test metrics are reported separately. Permutation importance is predictive sensitivity, not causality, SHAP or an uncertainty estimate. Static what-if supports one adjusted sensor at a time at five discrete levels; unsupported combinations are not approximated. The live backend still serves its configured single model and may differ from the replay selection.

Only the uncalibrated 30/60-cycle health/alert policy and the decorative turbofan schematic remain **illustrative**, explicitly labeled in the UI. No physical telemetry twin, calibrated confidence or maintenance safety guarantee is invented. Full-budget multi-seed FD002/FD003 research and operational validation remain future work.

Axe/contrast and keyboard tests are not a formal WCAG conformance audit. No screen-reader user study or Safari/Firefox test was performed. Lighthouse covers initial fleet rendering; later views were checked through browser tests and axe, not separate Lighthouse runs. No public deployment was performed.
