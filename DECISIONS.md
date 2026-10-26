# Decisions for review

| Decision | Alternatives | Why / risk | How to reverse |
|---|---|---|---|
| Create frontend/ on existing branch; preserve legacy static page | Replace vanilla page in place | Required Next.js stack; legacy reference remains | Remove frontend and restore original entry |
| Default NEXT_PUBLIC_DEMO_MODE=true, deterministic illustrative trajectories | Fabricate model output; require absent weights | Visitors can explore without implying validated predictions. Published metrics remain real and separately labeled | Export trained bundles and build with demo mode false for API what-if |
| FD001/FD004 aggregate metrics only; FD002/FD003 empty | Simulate missing benchmark scores | No evaluation evidence exists | Add validated results and regenerate JSON |
| What-if demo is explicitly heuristic; live uses same-origin Next rewrite to unchanged /predict | Modify FastAPI/CORS; pretend API supports model selection | Avoid response changes and cross-origin deployment complexity. Live API serves its configured model only | Change API_BASE_URL and provide artifact; no Python changes needed |
| Sensor trend/sensitivity is not SHAP importance | Invent attributions | No persisted attribution bundle; UI distinguishes normalized trend from causal importance | Extend exporter with verified attribution data |
| Replay thresholds 30/60 cycles are illustrative | Imply operational maintenance limits | No calibrated maintenance policy exists | Change shared status helper and labels |
| CPU-sized preview, no full retraining | Run 12 costly experiments | UI task; no request to retrain; weights missing | Run existing documented training separately and export |
| Scoped CSS, native font stack, inline vector engine graphic | Remote fonts/images or 3D model | Offline portfolio portability, no tracking or asset licensing ambiguity | Replace module tokens/assets |

No model/training code or API response shapes changed. Research access limits and measured QA results are documented separately.
