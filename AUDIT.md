# Product audit — 2026-10-26

## Observed checkout
Branch `work`, baseline `9bb3742`. No React, Bootstrap, Recharts, package.json, or frontend test harness existed. `static/index.html` is a standalone vanilla HTML page, not mounted by FastAPI. Components: API check button, four summary values, raw JSON textarea, prediction table. No fleet, routes, navigation, playback, or dataset explorer.

## Backend contract (unchanged)
`GET /health` → `{ok, artifact_dir, loaded}`. `loaded` only tests path existence, not artifact integrity.
`POST /predict` accepts `{rows: Record<string, number>[]}`: unit_number, time_in_cycles, op_setting_1..3, sensor_1..21. Returns `{predictions: [{unit_number,time_in_cycles,predicted_rul}], model, typical_error_reference, confidence: null, confidence_note}`; errors are HTTP 400 `{detail}` (validation may return 422). Inference uses one persisted artifact selected with RULPM_ARTIFACT_DIR. It has no fleet, model switching, correlation, attribution, or historical-prediction endpoint. Historical metrics are not per-prediction confidence.

## UX defects
No pending, retry or parse-error states. Raw JSON is the only input. No accessible live feedback, chart descriptions or focus workflow. Dense manual input blocks exploration; no visual risk hierarchy. CSS is globally applied. Health labels imply readiness beyond the backend check. innerHTML creates avoidable injection risk. No frontend performance/accessibility tests. Mobile layout only stacks cards. API and UI deployment are undocumented.

## Completeness
FD004 raw files exist and passed hashes; FD001–FD003 raw data absent. Acquisition/configuration only support FD001 and FD004. FD002/FD003 evaluations absent. FD001 and FD004 aggregate comparisons and per-seed metrics exist for four models; production model weights and per-engine residuals are absent. Prior setup's synthetic pytest artifacts are smoke fixtures, not trained research models. Backend has 28 passing tests. No live operational ingestion, maintenance policy calibration, authentication, calibrated uncertainty, or causal sensor explanation exists. Full experiment reproduction has not run here. Existing experiment cards describe methodology; no portfolio architecture or screenshots existed.

## Implementation boundary
Add a route-embeddable frontend module and static illustrative replay, visibly distinct from published metrics. Export real predictions only from explicitly supplied trained bundles. Keep unsupported datasets empty and explain missing evidence. Never fabricate evaluations, confidence intervals or feature attribution.
