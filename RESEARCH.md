# Research and choices

Research date: 2026-10-26. No web search tool is available. Direct official documentation requests returned proxy 403. Upstream GitHub README/docs below were retrieved over verified HTTPS; linked product sites are references, not inspected live examples. No web content was executed or treated as instructions.

## Product and visualization
[Grafana](https://github.com/grafana/grafana) describes templated dashboards, drilldown, exploration and alerting. Adopt overview → engine detail → replay, one shared cycle cursor, fixed cycle units, explicit source badges, and threshold text alongside color. [Azure Digital Twins](https://learn.microsoft.com/en-us/azure/digital-twins/overview) is a relevant real digital-twin example (site inaccessible here). Avoid a decorative 3D twin: this repo has trajectories, not a physical geometry/telemetry model. Add uncertainty only when model outputs support it. Do not infer fleet health from aggregate RMSE.

## Charts
| Library | Strength | Cost for this project |
|---|---|---|
| [Recharts](https://github.com/recharts/recharts) | Declarative React SVG charts, responsive composition, inspectable DOM | Large datasets need sampling; heatmap needs a small custom grid |
| [visx](https://github.com/airbnb/visx) | Low-level D3 + React, complete control | More custom axes, tooltips and accessibility work |
| [ECharts](https://github.com/apache/echarts) | High-volume canvas, built-in heatmaps and zoom | Additional integration and accessible-table work |
| [Tremor](https://github.com/tremorlabs/tremor) | Dashboard components and consistent defaults | Extra styling conventions; less visual flexibility |

Choose Recharts with lazy-loaded chart module; native semantic tables accompany charts. No smoothing that implies unobserved accuracy. Cursor filters every trajectory, tooltip exposes exact values, model colors stay fixed. Small correlation matrix uses labeled HTML buttons with numeric values.

## Architecture and interaction
[Next App Router server/client boundaries](https://github.com/vercel/next.js/blob/canary/docs/01-app/01-getting-started/05-server-and-client-components.mdx) supports keeping layout server-rendered and interactive experience client-side. Choose a self-contained client module imported by one App Router page. [Motion](https://github.com/motiondivision/motion) supports declarative React animation; use motion/react, MotionConfig reducedMotion="user", short opacity/transform transitions and layout animation, no essential animation. [shadcn/ui](https://github.com/shadcn-ui/ui) ownership model fits local Button/Dialog primitives; Radix dialog provides focus trapping and escape handling. Zustand owns shared cursor/playback/navigation, local form state stays local. Tailwind utilities are scoped to the module; no preflight or global font/style reset. CSS module tokens support dark and light themes.

Verification matters more than a claimed score: use production Lighthouse plus axe and keyboard checks at 360/768/1440. Report actual scores and any unavailable checks. This is targeted upstream research, not a comprehensive current-market survey.
