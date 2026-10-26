# Verification — 2026-10-26

Validated on the current branch using Node 24.19.0, Next.js 16.4.3, Python 3.11 and system Chromium. Production build used webpack. The first Turbopack build passed, but later sandbox socket restrictions broke its CSS worker; webpack was verified and saved as the reproducible default. No TLS/package verification was disabled.

| Check | Result |
|---|---|
| ESLint | Passed, no warnings/errors |
| TypeScript | Passed |
| Production build | Passed; prerendered root, not-found and icon routes |
| Python regression suite | 29 passed, 4 existing dependency/model warnings, no skips |
| Playwright combined suite | 7 passed, no skips, 33.4 seconds |
| Responsive | 360 / 768 / 1440 px, 1000 px viewport height; no document overflow |
| Axe WCAG 2 A/AA and 2.1 AA | No violations in tested fleet, engine detail, explorer dark and explorer light states at each width |
| Browser console | Zero console errors or page exceptions on the normal multi-view journeys at all three widths |
| Lighthouse mobile simulation, production root | Performance **96**, accessibility **100** |
| Lighthouse timings | FCP 0.8 s, LCP 2.3 s, TBT 190 ms, CLS 0 |
| Token contrast | 32 text/status/chart foreground-background pairs meet 4.5:1 text or 3:1 chart thresholds; see contrast.json |
| Trained exporter path | One engine exported through unchanged prediction pipeline using a synthetic XGBoost smoke artifact; all predictions finite, missing models omitted |

Lighthouse was run in isolation after browser tests, with default mobile simulation. A concurrent-run score of 81 reflected test/build CPU contention; the retained HTML/JSON are the final isolated run. Scores are local measurements, not a guarantee for a future portfolio host. The initial isolated build measured 97/100. Full traces, final reports and screenshots are in [qa/](qa/).

## What the browser tests cover

Fleet search/empty/reset; health filtering; selecting engines; synchronized cycle controls; play/pause/speed/reset; threshold alert; model/dataset navigation; published and missing benchmark states; sensor what-if calculation and stale-result feedback; light theme; command palette engine search; Escape and focus restoration; reduced-motion preference; data request failure/retry. All viewport journeys assert no document overflow and no normal-path console errors. There are 15 retained screenshots across the three widths.

The live test ran against a second API-enabled Next dev server and real FastAPI with a **synthetic smoke artifact**, not a research-trained checkpoint. It asserted a 30-row POST, successful xgboost output, changed sensor inputs, a controlled API 400, retry and successful recovery. Expected network errors in negative tests are distinct from normal-path console errors. The suite requires LIVE_UI_URL to include the live check; without it that one test is explicitly skipped. Reproduce with `NEXT_PUBLIC_DEMO_MODE=false npm run dev -- --port 3001 --webpack` alongside FastAPI, then `LIVE_UI_URL=http://127.0.0.1:3001 npm test` while the default production server runs on 3000.

## Limits

Automated axe/token checks and keyboard checks do not constitute a full WCAG conformance audit. No real screen-reader user study or Safari/Firefox run was performed. Lighthouse covers the initial root view; later in-page views were checked through browser interaction/axe, not separate Lighthouse audits. Reduced-motion preferences are applied to Motion and CSS; chart animation is explicitly disabled when reduced motion is requested.

No research-trained weights exist here. Real four-model inference accuracy, SHAP attributions, calibrated uncertainty and full experiments could not be validated. Illustrative replay residuals do not represent held-out model performance. FD001–FD003 raw data and FD002/FD003 evaluations remain absent. No public deployment or portfolio integration was performed. Local servers and synthetic artifacts are QA aids.
