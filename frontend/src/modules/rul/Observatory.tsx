"use client";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import {
  AnimatePresence,
  motion,
  MotionConfig,
  useReducedMotion,
  animate,
} from "motion/react";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Activity,
  ArrowRight,
  Box,
  ChevronRight,
  Command,
  Database,
  FlaskConical,
  Gauge,
  Grid2X2,
  Moon,
  Pause,
  Play,
  RotateCcw,
  Search,
  ShieldCheck,
  Sun,
  TriangleAlert,
  X,
  Zap,
} from "lucide-react";
import { Button } from "./components/ui/button";
import { useRul, type View } from "./store";
import {
  type Dataset,
  type Engine,
  type Model,
  models,
  colors,
  names,
  status,
} from "./types";
import s from "./styles.module.css";
const Charts = dynamic(() => import("./components/Charts"), {
  ssr: false,
  loading: () => <div className={s.skeleton} aria-label="Loading chart" />,
});
const DEMO = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";
const views: View[] = [
  "Fleet overview",
  "Engine detail",
  "Model arena",
  "Dataset explorer",
];
const icons = [Grid2X2, Activity, FlaskConical, Database];
function Count({ value }: { value: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduced = useReducedMotion();
  const previous = useRef(value);
  useEffect(() => {
    if (!ref.current) return;
    const controls = animate(previous.current, value, {
      duration: reduced ? 0 : 0.4,
      onUpdate: (v) => {
        if (ref.current)
          ref.current.textContent = Number.isInteger(value)
            ? Math.round(v).toString()
            : v.toFixed(1);
      },
    });
    previous.current = value;
    return () => controls.stop();
  }, [value, reduced]);
  return (
    <span ref={ref}>{Number.isInteger(value) ? value : value.toFixed(1)}</span>
  );
}
function Badge({ value }: { value: number }) {
  const state = status(value);
  return (
    <span className={`${s.badge} ${s[state]}`}>
      <i />
      {state[0].toUpperCase() + state.slice(1)}
    </span>
  );
}
function Ring({ value }: { value: number }) {
  return (
    <div className={`${s.ring} ${s[status(value)]}`}>
      <svg viewBox="0 0 80 80" aria-hidden="true">
        <circle
          cx="40"
          cy="40"
          r="34"
          fill="none"
          stroke="var(--border)"
          strokeWidth="5"
        />
        <motion.circle
          cx="40"
          cy="40"
          r="34"
          fill="none"
          stroke="currentColor"
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray="214"
          initial={false}
          animate={{ strokeDashoffset: 214 * (1 - Math.min(125, value) / 125) }}
          transition={{ duration: 0.4 }}
        />
      </svg>
      <span className={s.ringValue}>
        <Count value={Math.round(value)} />
      </span>
    </div>
  );
}
function EngineArt() {
  return (
    <div className={s.heroArt}>
      <svg
        viewBox="0 0 440 190"
        aria-label="Technical illustration of a turbofan engine"
        role="img"
      >
        <defs>
          <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
            <stop stopColor="#94bdd5" stopOpacity=".4" />
            <stop offset=".5" stopColor="#2d465f" stopOpacity=".1" />
            <stop offset="1" stopColor="#8aacc7" stopOpacity=".3" />
          </linearGradient>
        </defs>
        <g fill="url(#metal)" stroke="#89b5d3" strokeWidth=".8">
          <path d="M110 37 Q170 16 270 54 L357 72 L384 92 L357 113 L270 132 Q170 169 110 146 Z" />
          <ellipse cx="110" cy="92" rx="40" ry="55" />
          <ellipse cx="110" cy="92" rx="32" ry="47" />
          <ellipse cx="110" cy="92" rx="9" ry="13" />
          <path d="M150 42L150 141M169 40L169 144M189 42L189 140M210 45L210 135M232 47L232 135M255 51L255 130M280 56L280 129M300 61L300 122M320 65L320 120M340 69L340 115" />
          {Array.from({ length: 16 }, (_, i) => (
            <path
              key={i}
              d="M110 81Q88 63 110 49"
              transform={`rotate(${i * 22.5} 110 92)`}
            />
          ))}
          <path d="M70 92H391" strokeDasharray="3 5" />
          <path d="M175 37L197 14H231L240 47M194 143L208 165H245L257 135" />
          <path
            d="M85 152L62 174H20M300 59L336 26H416"
            fill="none"
            strokeDasharray="2 4"
          />
          <circle cx="300" cy="59" r="3" fill="#58bbff" />
          <circle cx="85" cy="152" r="3" fill="#46cfb4" />
        </g>
        <text x="341" y="20" fill="#a2b0c3" fontSize="8" fontFamily="monospace">
          CORE ASSEMBLY
        </text>
      </svg>
      <span className={s.artLabel}>C-MAPSS / TURBOFAN SYSTEM</span>
    </div>
  );
}
function DataTable({ children }: { children: React.ReactNode }) {
  return <div className={s.scroll}>{children}</div>;
}
export default function Observatory() {
  const paletteTrigger = useRef<HTMLButtonElement>(null);
  const state = useRul();
  const {
    view,
    engine,
    cycle,
    playing,
    speed,
    theme,
    navigate,
    select,
    setCycle,
    setPlaying,
    setSpeed,
    toggleTheme,
  } = state;
  const [data, setData] = useState<Dataset | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [palette, setPalette] = useState(false);
  const [command, setCommand] = useState("");
  const [toast, setToast] = useState("");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("risk");
  const [subset, setSubset] = useState("FD004");
  const [active, setActive] = useState<Model[]>([...models]);
  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const r = await fetch(
        process.env.NEXT_PUBLIC_RUL_DATA_URL || "/demo.json",
      );
      if (!r.ok) throw Error(`Dataset request failed (${r.status})`);
      const d = await r.json();
      if (
        d.schemaVersion !== 1 ||
        !d.engines?.length ||
        !d.models?.length ||
        !d.engines.every((e: Engine) => e.points?.length)
      )
        throw Error("Unsupported or empty dataset export");
      setData(d);
      setActive(d.models);
      setSubset(d.subset);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Dataset unavailable");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    const task = setTimeout(() => void load(), 0);
    return () => clearTimeout(task);
  }, [load]);
  const selected =
    data?.engines.find((e) => e.id === engine) ?? data?.engines[0];
  const current =
    selected?.points[
      Math.max(0, Math.min(cycle - 1, selected.points.length - 1))
    ];
  const value = current?.xgboost ?? current?.actual ?? 0;
  useEffect(() => {
    if (!playing || !selected) return;
    const timer = setInterval(() => {
      const previous = useRul.getState().cycle;
      const next = previous + 1;
      if (next > selected.cycles) {
        setPlaying(false);
        return;
      }
      const old = selected.points[previous - 1];
      const point = selected.points[next - 1];
      const before = status(old.xgboost ?? old.actual);
      const after = status(point.xgboost ?? point.actual);
      if (before !== after && after !== "healthy")
        setToast(
          `${selected.name}: ${after} threshold crossed at cycle ${next}. Illustrative alert; not maintenance advice.`,
        );
      setCycle(next);
    }, 1000 / speed);
    return () => clearInterval(timer);
  }, [playing, selected, speed, setCycle, setPlaying]);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 7000);
    return () => clearTimeout(t);
  }, [toast]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette((v) => !v);
        return;
      }
      if (
        e.target instanceof HTMLElement &&
        e.target.closest("input,textarea,select,[role=dialog],button")
      )
        return;
      if (e.key === " " && view === "Engine detail") {
        e.preventDefault();
        setPlaying(!useRul.getState().playing);
      }
      if (e.key === "ArrowRight" && selected && view === "Engine detail") {
        e.preventDefault();
        setCycle(Math.min(selected.cycles, useRul.getState().cycle + 1));
      }
      if (e.key === "ArrowLeft" && view === "Engine detail") {
        e.preventDefault();
        setCycle(Math.max(1, useRul.getState().cycle - 1));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [view, selected, setPlaying, setCycle]);
  const fleet = useMemo(
    () =>
      data?.engines
        .filter((e) => {
          const v =
            e.points[e.current - 1]?.xgboost ??
            e.points[e.current - 1]?.actual ??
            0;
          return (
            (filter === "all" || status(v) === filter) &&
            e.name.toLowerCase().includes(query.toLowerCase())
          );
        })
        .sort((a, b) =>
          sort === "name"
            ? a.name.localeCompare(b.name)
            : ((a.points[a.current - 1].xgboost ??
                a.points[a.current - 1].actual) -
                (b.points[b.current - 1].xgboost ??
                  b.points[b.current - 1].actual)) *
              (sort === "risk" ? 1 : -1),
        ) ?? [],
    [data, filter, query, sort],
  );
  const totals =
    data?.engines.map(
      (e) => e.points[e.current - 1].xgboost ?? e.points[e.current - 1].actual,
    ) ?? [];
  const points = selected?.points.slice(0, cycle) ?? [];
  const metrics = data?.metrics[subset] ?? [];
  const provenance = data?.predictionSource.startsWith("illustrative")
    ? "Illustrative replay"
    : "Exported model predictions";
  return (
    <MotionConfig reducedMotion="user">
      <div className={s.root} data-theme={theme}>
        <a href="#rul-main" className={s.skip}>
          Skip to main content
        </a>
        <div className={s.shell}>
          <aside className={s.sidebar}>
            <div className={s.brand}>
              <span className={s.brandMark}>
                <Activity size={19} />
              </span>
              RUL
              <span style={{ fontWeight: 400, color: "var(--muted)" }}>
                {" "}
                / lab
              </span>
            </div>
            <div>
              <p
                className={s.eyebrow}
                style={{ padding: "0 10px", marginBottom: 12 }}
              >
                Workspace
              </p>
              <nav className={s.nav} aria-label="Main navigation">
                {views.map((v, i) => {
                  const Icon = icons[i];
                  return (
                    <Button
                      key={v}
                      variant="ghost"
                      aria-current={view === v ? "page" : undefined}
                      onClick={() => navigate(v)}
                    >
                      <Icon size={16} />
                      {v}
                    </Button>
                  );
                })}
              </nav>
            </div>
            <div className={s.sidebarBottom}>
              <Box size={20} />
              <p style={{ marginTop: 10, color: "var(--text)" }}>
                Built for the next cycle.
              </p>
              <p style={{ marginTop: 5 }}>
                NASA C-MAPSS research
                <br />
                FD001 + FD004 benchmarks
              </p>
              <div className={s.notice}>
                Research demonstrator.
                <br />
                Not an operational safety system.
              </div>
              <span>v1.0 / OBSERVATORY</span>
            </div>
          </aside>
          <div style={{ minWidth: 0 }}>
            <header className={s.topbar}>
              <div className={s.crumb}>
                <span>Workspace</span>
                <ChevronRight size={12} />
                <span style={{ color: "var(--text)" }}>{view}</span>
              </div>
              <div className={s.topActions}>
                <span className={`${s.badge} ${s.healthy}`}>
                  <i />
                  {DEMO ? "DEMO MODE" : "API WHAT-IF"}
                </span>
                <Button
                  variant="ghost"
                  ref={paletteTrigger}
                  onClick={() => setPalette(true)}
                  aria-label="Open command palette"
                >
                  <Search size={16} />
                  <kbd style={{ fontSize: 10 }}>⌘ K</kbd>
                </Button>
                <Button
                  variant="ghost"
                  aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
                  onClick={toggleTheme}
                >
                  {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                </Button>
              </div>
            </header>
            <main id="rul-main" tabIndex={-1} className={s.content}>
              <motion.div
                key={view}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.18 }}
              >
                <div className={s.heading}>
                  <div>
                    <p className={s.eyebrow} style={{ marginBottom: 10 }}>
                      Intelligent predictive maintenance
                    </p>
                    <motion.h1
                      layoutId={
                        view === "Engine detail"
                          ? `engine-title-${selected?.id}`
                          : undefined
                      }
                    >
                      {view === "Fleet overview"
                        ? "Every engine. One clear picture."
                        : view === "Engine detail"
                          ? `${selected?.name ?? "Engine"} / digital workspace`
                          : view === "Model arena"
                            ? "Four models. One fair comparison."
                            : "Understand the signal."}
                    </motion.h1>
                    <p className={s.subtitle}>
                      {view === "Fleet overview"
                        ? "A closer look at engine health. Spot degradation, explore the signals, and stay ahead of the next cycle."
                        : view === "Engine detail"
                          ? "Scrub through an engine’s life. Every view follows the same cycle."
                          : view === "Model arena"
                            ? "Published benchmarks alongside an explicitly labeled illustrative replay. Lower error is better."
                            : "Explore operating conditions, sensor relationships, and the data behind the models."}
                    </p>
                  </div>
                  <Button
                    onClick={() =>
                      view === "Fleet overview"
                        ? select(1, data?.engines[0].current ?? 120)
                        : navigate("Fleet overview")
                    }
                  >
                    <span>
                      {view === "Fleet overview"
                        ? "Explore an engine"
                        : "Back to fleet"}
                    </span>
                    <ArrowRight size={14} />
                  </Button>
                </div>
                {loading ? (
                  <div role="status" aria-label="Loading fleet">
                    <div className={s.stats}>
                      {[1, 2, 3, 4].map((i) => (
                        <div key={i} className={s.skeleton} />
                      ))}
                    </div>
                    <p>Loading engine trajectories…</p>
                  </div>
                ) : loadError ? (
                  <div className={s.empty} role="alert">
                    <TriangleAlert />
                    <h2>Couldn’t load the workspace</h2>
                    <p>{loadError}</p>
                    <Button onClick={() => void load()}>Retry dataset</Button>
                  </div>
                ) : data && selected && current ? (
                  <>
                    {view === "Fleet overview" && (
                      <>
                        <div className={s.stats}>
                          {[
                            {
                              label: "Engines in preview",
                              value: totals.length,
                              note: "Selected research trajectories",
                              icon: Box,
                            },
                            {
                              label: "Healthy",
                              value: totals.filter(
                                (v) => status(v) === "healthy",
                              ).length,
                              note: "More than 60 cycles remaining",
                              icon: ShieldCheck,
                            },
                            {
                              label: "Needs attention",
                              value: totals.filter(
                                (v) => status(v) !== "healthy",
                              ).length,
                              note: "Watch + critical · demo thresholds",
                              icon: TriangleAlert,
                            },
                            {
                              label: "Average remaining life",
                              value: Math.round(
                                totals.reduce((a, b) => a + b, 0) /
                                  totals.length,
                              ),
                              note: "Cycles · illustrative predictions",
                              icon: Gauge,
                            },
                          ].map(({ label, value, note, icon: Icon }) => (
                            <div className={s.stat} key={label}>
                              <div className={s.statLabel}>
                                {label}
                                <Icon size={15} />
                              </div>
                              <div
                                className={s.number}
                                style={{ marginTop: 12 }}
                              >
                                <Count value={value} />
                              </div>
                              <p className={s.statNote}>{note}</p>
                            </div>
                          ))}
                        </div>
                        <section className={s.hero}>
                          <div className={s.heroText}>
                            <span className={`${s.badge} ${s.healthy}`}>
                              <Zap size={11} /> THE ENGINE ROOM
                            </span>
                            <h2>
                              From sensor signals
                              <br />
                              to a clearer horizon.
                            </h2>
                            <p className={s.muted} style={{ fontSize: 12 }}>
                              Replay the journey. Compare the models.
                              <br />
                              See what the numbers are telling you.
                            </p>
                            <Button
                              variant="ghost"
                              onClick={() => {
                                select(1, 1);
                                setPlaying(true);
                              }}
                            >
                              Start a life-cycle replay <ArrowRight size={14} />
                            </Button>
                          </div>
                          <EngineArt />
                        </section>
                        <div className={s.toolbar}>
                          <div>
                            <h2>
                              Engine fleet{" "}
                              <span
                                className={s.muted}
                                style={{ fontSize: 12, fontWeight: 400 }}
                              >
                                {" "}
                                / {fleet.length} engines
                              </span>
                            </h2>
                            <p className={s.subtitle} style={{ marginTop: 4 }}>
                              {data.subset} · {provenance} · XGBoost view
                            </p>
                          </div>
                          <div className={s.controls}>
                            <input
                              type="search"
                              aria-label="Search engines"
                              placeholder="Search engines…"
                              value={query}
                              onChange={(e) => setQuery(e.target.value)}
                              style={{ width: 160 }}
                            />
                            <select
                              aria-label="Filter health"
                              value={filter}
                              onChange={(e) => setFilter(e.target.value)}
                            >
                              <option value="all">All health states</option>
                              <option value="healthy">Healthy</option>
                              <option value="watch">Watch</option>
                              <option value="critical">Critical</option>
                            </select>
                            <select
                              aria-label="Sort engines"
                              value={sort}
                              onChange={(e) => setSort(e.target.value)}
                            >
                              <option value="risk">Highest risk first</option>
                              <option value="life">Longest life first</option>
                              <option value="name">Engine name</option>
                            </select>
                          </div>
                        </div>
                        {!fleet.length ? (
                          <div className={s.empty}>
                            <Search />
                            <h2>No matching engines</h2>
                            <Button
                              onClick={() => {
                                setQuery("");
                                setFilter("all");
                              }}
                            >
                              Clear filters
                            </Button>
                          </div>
                        ) : (
                          <motion.div layout className={s.engineGrid}>
                            {fleet.map((e, i) => {
                              const p = e.points[e.current - 1];
                              const rul = p.xgboost ?? p.actual;
                              return (
                                <motion.div
                                  key={e.id}
                                  layout
                                  initial={{ opacity: 0, y: 8 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{
                                    delay: Math.min(i * 0.025, 0.2),
                                  }}
                                >
                                  <button
                                    className={s.engine}
                                    onClick={() => select(e.id, e.current)}
                                    aria-label={`Open ${e.name}, ${status(rul)}, ${Math.round(rul)} cycles remaining`}
                                  >
                                    <div className={s.engineTop}>
                                      <motion.span
                                        layoutId={`engine-title-${e.id}`}
                                        className={s.engineName}
                                      >
                                        {e.name}
                                      </motion.span>
                                      <Badge value={rul} />
                                    </div>
                                    <div className={s.engineBody}>
                                      <Ring value={rul} />
                                      <div>
                                        <p
                                          className={s.eyebrow}
                                          style={{ fontSize: 9 }}
                                        >
                                          Remaining useful life
                                        </p>
                                        <p
                                          style={{
                                            fontSize: 21,
                                            fontWeight: 550,
                                            marginTop: 3,
                                          }}
                                        >
                                          {Math.round(rul)}{" "}
                                          <span
                                            className={s.muted}
                                            style={{
                                              fontSize: 11,
                                              fontWeight: 400,
                                            }}
                                          >
                                            cycles
                                          </span>
                                        </p>
                                        <p
                                          className={s.muted}
                                          style={{ fontSize: 10, marginTop: 5 }}
                                        >
                                          Cycle {e.current} / {e.cycles}
                                        </p>
                                      </div>
                                      <ArrowRight
                                        size={14}
                                        style={{
                                          marginLeft: "auto",
                                          color: "var(--muted)",
                                        }}
                                      />
                                    </div>
                                    <div className={s.engineFooter}>
                                      <span>{data.subset} · Turbofan</span>
                                      <span>Explore trajectory ↗</span>
                                    </div>
                                  </button>
                                </motion.div>
                              );
                            })}
                          </motion.div>
                        )}
                        <div className={s.notice}>
                          {data.trajectorySource}. Predictions are{" "}
                          {data.predictionSource}. Healthy &gt;60, watch 31–60,
                          critical ≤30 cycles are illustrative thresholds.
                        </div>
                      </>
                    )}
                    {view === "Engine detail" && (
                      <>
                        <div
                          className={s.controls}
                          style={{ marginBottom: 18 }}
                        >
                          <label htmlFor="engine-select">Selected engine</label>
                          <select
                            id="engine-select"
                            value={selected.id}
                            onChange={(e) => {
                              const en = data.engines.find(
                                (x) => x.id === +e.target.value,
                              )!;
                              select(en.id, en.current);
                            }}
                          >
                            {data.engines.map((e) => (
                              <option key={e.id} value={e.id}>
                                {e.name}
                              </option>
                            ))}
                          </select>
                          <Badge value={value} />
                          <span className={s.badge}>{provenance}</span>
                        </div>
                        <section
                          className={s.replay}
                          aria-label="Life-cycle replay"
                        >
                          <Button
                            variant="default"
                            aria-label={
                              playing ? "Pause replay" : "Play replay"
                            }
                            onClick={() => {
                              if (cycle >= selected.cycles) setCycle(1);
                              setPlaying(!playing);
                            }}
                          >
                            {playing ? <Pause size={16} /> : <Play size={16} />}{" "}
                            {playing ? "Pause" : "Replay"}
                          </Button>
                          <div>
                            <label htmlFor="cycle">
                              Cycle {cycle} of {selected.cycles}{" "}
                              <span style={{ float: "right" }}>
                                ← → to step
                              </span>
                            </label>
                            <input
                              id="cycle"
                              type="range"
                              min="1"
                              max={selected.cycles}
                              value={cycle}
                              onChange={(e) => {
                                setPlaying(false);
                                setCycle(+e.target.value);
                              }}
                            />
                          </div>
                          <div className={s.controls}>
                            <select
                              value={speed}
                              aria-label="Replay speed"
                              onChange={(e) => setSpeed(+e.target.value)}
                            >
                              {[1, 2, 5, 10].map((v) => (
                                <option key={v} value={v}>
                                  {v}× speed
                                </option>
                              ))}
                            </select>
                            <Button
                              aria-label="Reset replay"
                              onClick={() => {
                                setPlaying(false);
                                setCycle(1);
                              }}
                            >
                              <RotateCcw size={14} />
                            </Button>
                          </div>
                        </section>
                        <div className={s.stats}>
                          {[
                            {
                              label: "Predicted RUL · XGBoost",
                              value: value,
                              note: "Illustrative unless exported from artifact",
                            },
                            {
                              label: "Actual remaining life",
                              value: current.actual,
                              note: "Capped at 125 · training trajectory",
                            },
                            {
                              label: "Cycles observed",
                              value: cycle,
                              note: `Of ${selected.cycles} run-to-failure cycles`,
                            },
                            {
                              label: "Current residual",
                              value: value - current.actual,
                              note: "Prediction minus actual · cycles",
                            },
                          ].map((m) => (
                            <div className={s.stat} key={m.label}>
                              <p className={s.statLabel}>{m.label}</p>
                              <div className={s.number}>
                                <Count value={m.value} />
                              </div>
                              <p className={s.statNote}>{m.note}</p>
                            </div>
                          ))}
                        </div>
                        <section className={`${s.panel} ${s.chart}`}>
                          <div className={s.panelHead}>
                            <div>
                              <h2>The remaining-life horizon</h2>
                              <p className={s.subtitle}>
                                RUL (cycles) against elapsed cycle · through
                                cycle {cycle}
                              </p>
                            </div>
                            <span className={s.badge}>
                              30-cycle alert guide
                            </span>
                          </div>
                          <ModelToggles
                            active={active}
                            setActive={setActive}
                            available={data.models}
                          />
                          <Charts points={points} active={active} />
                          <PointTable points={points} />
                        </section>
                        <div className={s.twoCol}>
                          <section className={s.panel}>
                            <div className={s.panelHead}>
                              <h2>Sensor telemetry / S11</h2>
                              <span className={s.badge}>Raw measurement</span>
                            </div>
                            <Charts points={points} kind="sensor" />
                            <p className={s.subtitle}>
                              Sensor values follow the same cycle cursor.
                              Operating regimes can change the baseline.
                            </p>
                          </section>
                          <Explain
                            engine={selected}
                            cycle={cycle}
                            value={value}
                          />
                        </div>
                      </>
                    )}
                    {view === "Model arena" && (
                      <>
                        <div className={s.toolbar}>
                          <h2>Published benchmark / held-out test engines</h2>
                          <select
                            aria-label="Benchmark dataset"
                            value={subset}
                            onChange={(e) => setSubset(e.target.value)}
                          >
                            {["FD001", "FD002", "FD003", "FD004"].map((d) => (
                              <option key={d}>{d}</option>
                            ))}
                          </select>
                        </div>
                        {!metrics.length ? (
                          <div className={s.empty}>
                            <FlaskConical />
                            <h2>No published evaluation for {subset}</h2>
                            <p className={s.muted}>
                              No raw data or model comparison is available for
                              this subset.
                            </p>
                            <Button onClick={() => setSubset("FD004")}>
                              View FD004 benchmarks
                            </Button>
                          </div>
                        ) : (
                          <>
                            <div className={s.modelGrid}>
                              {metrics.map((m) => (
                                <section
                                  className={`${s.panel} ${s.model}`}
                                  style={{ borderTopColor: colors[m.model] }}
                                  key={m.model}
                                >
                                  <div className={s.panelHead}>
                                    <h2>{names[m.model]}</h2>
                                    {m.rmse_mean ===
                                      Math.min(
                                        ...metrics.map((x) => x.rmse_mean),
                                      ) && (
                                      <span
                                        className={`${s.badge} ${s.healthy}`}
                                      >
                                        Best RMSE
                                      </span>
                                    )}
                                  </div>
                                  <p
                                    className={s.muted}
                                    style={{ fontSize: 10 }}
                                  >
                                    RMSE / CYCLES
                                  </p>
                                  <div className={s.number}>
                                    {m.rmse_mean.toFixed(2)}
                                  </div>
                                  <p className={s.statNote}>
                                    ± {m.rmse_std.toFixed(2)} across three seeds
                                  </p>
                                  <div className={s.metricLine}>
                                    <span className={s.muted}>NASA score</span>
                                    <b>{m.nasa_score_mean.toFixed(1)}</b>
                                  </div>
                                  <div className={s.metricLine}>
                                    <span className={s.muted}>MAE</span>
                                    <b>{m.mae_mean.toFixed(2)}</b>
                                  </div>
                                </section>
                              ))}
                            </div>
                            <DataTable>
                              <table>
                                <caption className={s.muted}>
                                  Published {subset} aggregate results · seeds
                                  42, 1337, 2026
                                </caption>
                                <thead>
                                  <tr>
                                    <th>Model</th>
                                    <th>RMSE ↓</th>
                                    <th>NASA score ↓</th>
                                    <th>MAE ↓</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {metrics.map((m) => (
                                    <tr key={m.model}>
                                      <th>{names[m.model]}</th>
                                      <td>{m.rmse_mean.toFixed(3)}</td>
                                      <td>{m.nasa_score_mean.toFixed(3)}</td>
                                      <td>{m.mae_mean.toFixed(3)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </DataTable>
                          </>
                        )}
                        <div className={s.notice}>
                          Charts below use {data.subset} {selected.name} replay,
                          independent of the benchmark selector. Residuals are{" "}
                          {data.predictionSource}; they are not published
                          per-engine test residuals.
                        </div>
                        <section className={s.panel}>
                          <h2>Per-engine residuals / preview snapshots</h2>
                          <p className={s.subtitle}>
                            Predicted minus actual RUL, in cycles · illustrative
                            unless exported from trained artifacts
                          </p>
                          <DataTable>
                            <table>
                              <thead>
                                <tr>
                                  <th>Engine</th>
                                  {data.models.map((m) => (
                                    <th key={m}>{names[m]}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {data.engines.map((e) => {
                                  const p = e.points[e.current - 1];
                                  return (
                                    <tr key={e.id}>
                                      <th>{e.name}</th>
                                      {data.models.map((m) => (
                                        <td key={m}>
                                          {p[m] === undefined
                                            ? "Unavailable"
                                            : (p[m]! - p.actual).toFixed(2)}
                                        </td>
                                      ))}
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </DataTable>
                        </section>
                        <div className={s.toolbar}>
                          <h2>Replay comparison / {selected.name}</h2>
                          <select
                            aria-label="Compare engine"
                            value={engine}
                            onChange={(e) => {
                              const en = data.engines.find(
                                (x) => x.id === +e.target.value,
                              )!;
                              select(en.id, en.cycles);
                              navigate("Model arena");
                            }}
                          >
                            {data.engines.map((e) => (
                              <option key={e.id} value={e.id}>
                                {e.name}
                              </option>
                            ))}
                          </select>
                        </div>
                        <ModelToggles
                          active={active}
                          setActive={setActive}
                          available={data.models}
                        />
                        <section className={s.panel}>
                          <h2>Prediction vs actual / full life cycle</h2>
                          <Charts points={selected.points} active={active} />
                          <PointTable points={selected.points} />
                        </section>
                        <div className={s.twoCol}>
                          <section className={s.panel}>
                            <h2>Residuals by cycle / {selected.name}</h2>
                            <p className={s.subtitle}>
                              Positive = overestimate · negative = underestimate
                            </p>
                            <Charts
                              points={selected.points}
                              active={active}
                              kind="residual"
                            />
                          </section>
                          <section className={s.panel}>
                            <h2>XGBoost error distribution</h2>
                            <p className={s.subtitle}>
                              Residual cycles on x-axis · observation count on
                              y-axis
                            </p>
                            <Charts
                              points={selected.points}
                              kind="distribution"
                            />
                          </section>
                        </div>
                      </>
                    )}
                    {view === "Dataset explorer" && (
                      <>
                        <div className={s.toolbar}>
                          <h2>Dataset workspace</h2>
                          <select
                            value={subset}
                            aria-label="Explore dataset"
                            onChange={(e) => setSubset(e.target.value)}
                          >
                            {["FD001", "FD002", "FD003", "FD004"].map((d) => (
                              <option key={d}>{d}</option>
                            ))}
                          </select>
                        </div>
                        {subset !== data.subset ? (
                          <div className={s.empty}>
                            <Database />
                            <h2>{subset} trajectories are not installed</h2>
                            <p className={s.muted}>
                              {data.metrics[subset]
                                ? "Published aggregate metrics are available in Model arena."
                                : "No raw data or published evaluation is available."}
                            </p>
                            <Button onClick={() => setSubset(data.subset)}>
                              Explore installed {data.subset}
                            </Button>
                          </div>
                        ) : (
                          <>
                            <div className={s.notice}>
                              {data.trajectorySource}. Correlations use the full
                              training subset; replay uses 12 selected engines.
                              Correlation does not establish causal sensor
                              importance.
                            </div>
                            <div className={s.twoCol}>
                              <section className={s.panel}>
                                <div className={s.panelHead}>
                                  <h2>Sensor correlation</h2>
                                  <span className={s.badge}>Pearson r</span>
                                </div>
                                <p className={s.subtitle}>
                                  Select a cell to inspect its coefficient. S =
                                  sensor number.
                                </p>
                                {data.correlation.length ? (
                                  <div className={s.scroll}>
                                    <div
                                      className={s.heatmap}
                                      style={{
                                        gridTemplateColumns: `30px repeat(${data.sensors.length},minmax(25px,1fr))`,
                                        minWidth: 390,
                                      }}
                                    >
                                      <span />
                                      {data.sensors.map((n) => (
                                        <span
                                          key={n}
                                          style={{
                                            fontSize: 9,
                                            textAlign: "center",
                                          }}
                                        >
                                          S{n}
                                        </span>
                                      ))}
                                      {data.correlation.map((row, i) => (
                                        <div
                                          key={i}
                                          style={{ display: "contents" }}
                                        >
                                          <span
                                            style={{
                                              fontSize: 9,
                                              alignSelf: "center",
                                            }}
                                          >
                                            S{data.sensors[i]}
                                          </span>
                                          {row.map((r, j) => (
                                            <button
                                              key={j}
                                              className={s.heatCell}
                                              aria-label={`Sensor ${data.sensors[i]} and sensor ${data.sensors[j]} correlation ${r}`}
                                              style={{
                                                background:
                                                  r >= 0
                                                    ? `rgb(${Math.round(25 + 45 * Math.abs(r))},${Math.round(40 + 65 * Math.abs(r))},${Math.round(60 + 70 * Math.abs(r))})`
                                                    : `rgb(${Math.round(60 + 70 * Math.abs(r))},60,90)`,
                                                color: "#fff",
                                              }}
                                              onClick={() =>
                                                setToast(
                                                  `S${data.sensors[i]} × S${data.sensors[j]}: Pearson correlation ${r.toFixed(2)}. Association, not causation.`,
                                                )
                                              }
                                            >
                                              {r.toFixed(1)}
                                            </button>
                                          ))}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                ) : (
                                  <p>No measured correlation available.</p>
                                )}
                                <p className={s.subtitle}>
                                  −1 inverse / 0 no linear relation / +1 aligned
                                </p>
                              </section>
                              <section className={s.panel}>
                                <h2>
                                  Degradation trajectory / {selected.name}
                                </h2>
                                <p className={s.subtitle}>
                                  S11 raw values · {selected.cycles} observed
                                  cycles
                                </p>
                                <Charts
                                  points={selected.points}
                                  kind="sensor"
                                />
                                <Button
                                  onClick={() =>
                                    select(selected.id, selected.current)
                                  }
                                >
                                  Inspect engine <ArrowRight size={14} />
                                </Button>
                              </section>
                            </div>
                            <section className={`${s.panel} ${s.sectionGap}`}>
                              <h2>Dataset facts</h2>
                              <DataTable>
                                <table>
                                  <thead>
                                    <tr>
                                      <th>Subset</th>
                                      <th>Operating regimes</th>
                                      <th>Fault modes</th>
                                      <th>Local status</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {[
                                      ["FD001", "1", "1", "Metrics only"],
                                      ["FD002", "6", "1", "Not installed"],
                                      ["FD003", "1", "2", "Not installed"],
                                      ["FD004", "6", "2", "Raw data + metrics"],
                                    ].map((row) => (
                                      <tr key={row[0]}>
                                        {row.map((c, i) => (
                                          <td key={i}>{c}</td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </DataTable>
                            </section>
                          </>
                        )}
                      </>
                    )}
                    <footer className={s.footer}>
                      <span>
                        RUL / lab <span style={{ margin: "0 10px" }}>·</span>{" "}
                        NASA C-MAPSS research demonstrator
                      </span>
                      <span>
                        Point estimates only · no calibrated confidence
                      </span>
                    </footer>
                  </>
                ) : null}
              </motion.div>
            </main>
          </div>
        </div>
        <Dialog.Root open={palette} onOpenChange={setPalette}>
          <Dialog.Portal>
            <div className={s.root} data-theme={theme}>
              <Dialog.Overlay className={s.overlay} />
              <Dialog.Content
                className={s.dialog}
                onCloseAutoFocus={(e) => {
                  e.preventDefault();
                  paletteTrigger.current?.focus();
                }}
              >
                <div className={s.panelHead}>
                  <Dialog.Title asChild>
                    <h2>
                      <Command
                        size={15}
                        style={{ verticalAlign: "middle", marginRight: 8 }}
                      />
                      Jump to workspace
                    </h2>
                  </Dialog.Title>
                  <Dialog.Close asChild>
                    <Button variant="ghost" aria-label="Close command palette">
                      <X size={16} />
                    </Button>
                  </Dialog.Close>
                </div>
                <Dialog.Description className={s.subtitle}>
                  Search pages and engines. Tab to a result, Enter to open.
                  Escape to close.
                </Dialog.Description>
                <input
                  className={s.textInput}
                  type="search"
                  placeholder="Find a page or engine…"
                  aria-label="Search commands"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                />
                <div className={s.dialogList}>
                  {views
                    .filter((v) =>
                      v.toLowerCase().includes(command.toLowerCase()),
                    )
                    .map((v) => (
                      <Button
                        key={v}
                        variant="ghost"
                        onClick={() => {
                          navigate(v);
                          setPalette(false);
                          setCommand("");
                        }}
                      >
                        {v}
                        <ArrowRight size={13} />
                      </Button>
                    ))}
                  {data?.engines
                    .filter((e) =>
                      e.name.toLowerCase().includes(command.toLowerCase()),
                    )
                    .map((e) => (
                      <Button
                        key={e.id}
                        variant="ghost"
                        onClick={() => {
                          select(e.id, e.current);
                          setPalette(false);
                          setCommand("");
                        }}
                      >
                        {e.name} <span className={s.muted}>Engine detail</span>
                      </Button>
                    ))}
                </div>
                <p className={s.subtitle}>
                  Engine shortcuts: Space play/pause · ← → step cycle
                </p>
              </Dialog.Content>
            </div>
          </Dialog.Portal>
        </Dialog.Root>
        <AnimatePresence>
          {toast && (
            <motion.div
              className={s.toast}
              role="status"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className={s.controls}>
                <TriangleAlert size={17} />
                <span style={{ flex: 1 }}>{toast}</span>
                <Button
                  variant="ghost"
                  onClick={() => setToast("")}
                  aria-label="Dismiss notification"
                >
                  <X size={14} />
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </MotionConfig>
  );
}
function ModelToggles({
  active,
  setActive,
  available,
}: {
  active: Model[];
  setActive: (a: Model[]) => void;
  available: Model[];
}) {
  return (
    <div
      className={s.controls}
      style={{ margin: "12px 0 18px" }}
      aria-label="Visible models"
    >
      {models.map((m) => (
        <Button
          key={m}
          disabled={!available.includes(m)}
          aria-pressed={active.includes(m)}
          onClick={() =>
            setActive(
              active.includes(m)
                ? active.filter((x) => x !== m)
                : [...active, m],
            )
          }
          style={{ opacity: active.includes(m) ? 1 : 0.55 }}
        >
          <span className={s.dot} style={{ background: colors[m] }} />
          {names[m]}
        </Button>
      ))}
      <span className={s.muted} style={{ fontSize: 11 }}>
        Dashed = actual RUL
      </span>
    </div>
  );
}
function PointTable({ points }: { points: Engine["points"] }) {
  return (
    <details>
      <summary>View exact values / latest 10 cycles</summary>
      <DataTable>
        <table>
          <thead>
            <tr>
              <th>Cycle</th>
              <th>Actual</th>
              {models.map((m) => (
                <th key={m}>{names[m]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {points.slice(-10).map((p) => (
              <tr key={p.cycle}>
                <td>{p.cycle}</td>
                <td>{p.actual}</td>
                {models.map((m) => (
                  <td key={m}>{p[m]?.toFixed(2) ?? "Unavailable"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </DataTable>
    </details>
  );
}
function Explain({
  engine,
  cycle,
  value,
}: {
  engine: Engine;
  cycle: number;
  value: number;
}) {
  const [changes, setChanges] = useState<Record<string, number>>({
    "2": 0,
    "4": 0,
    "11": 0,
  });
  const [result, setResult] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [resultModel, setResultModel] = useState("");
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);
  const fingerprint = `${engine.id}/${cycle}/${JSON.stringify(changes)}`;
  const [resultKey, setResultKey] = useState("");
  const valid = resultKey === fingerprint;
  async function predict() {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError("");
    try {
      if (DEMO) {
        await new Promise((r) => setTimeout(r, 180));
        if (controller.signal.aborted) return;
        setResult(
          Math.max(
            0,
            Math.min(
              125,
              value - Object.values(changes).reduce((a, b) => a + b, 0) * 0.4,
            ),
          ),
        );
        setResultModel("Illustrative sensitivity");
      } else {
        const rows = engine.points
          .slice(Math.max(0, cycle - 30), cycle)
          .map((p) => {
            const row = { ...p.row };
            Object.entries(changes).forEach(
              ([id, v]) => (row[`sensor_${id}`] *= 1 + v / 100),
            );
            return row;
          });
        const response = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rows }),
          signal: controller.signal,
        });
        const data = await response.json();
        if (!response.ok)
          throw Error(
            typeof data.detail === "string"
              ? data.detail
              : `Prediction failed (${response.status})`,
          );
        if (!Number.isFinite(data.predictions?.[0]?.predicted_rul))
          throw Error("Invalid prediction response");
        setResult(data.predictions[0].predicted_rul);
        setResultModel(data.model);
      }
      setResultKey(fingerprint);
    } catch (e) {
      if (!controller.signal.aborted)
        setError(e instanceof Error ? e.message : "Prediction failed");
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  const p = engine.points[Math.min(cycle - 1, engine.points.length - 1)];
  const base = engine.points[0];
  const impacts = ["2", "4", "11"]
    .map((id) => ({
      id,
      change:
        Math.abs(
          (p.sensors[id] - base.sensors[id]) /
            (Math.abs(base.sensors[id]) || 1),
        ) * 100,
    }))
    .sort((a, b) => b.change - a.change);
  return (
    <section className={s.panel}>
      <div className={s.panelHead}>
        <h2>Explain the signal</h2>
        <span className={s.badge}>Exploratory</span>
      </div>
      <p className={s.subtitle}>
        Relative sensor drift from cycle 1, not model importance or SHAP
        attribution.
      </p>
      {impacts.map((x) => (
        <div key={x.id} className={s.sensorRow}>
          <span>Sensor {x.id}</span>
          <div className={s.bar}>
            <span style={{ width: `${Math.min(100, x.change * 10)}%` }} />
          </div>
          <span>{x.change.toFixed(1)}%</span>
        </div>
      ))}
      <h3 style={{ marginTop: 24 }}>What if the signal changed?</h3>
      <p className={s.subtitle}>
        {DEMO
          ? "Demo heuristic only. Does not re-run a trained model."
          : "Queries the configured backend model, which may differ from the replay."}
      </p>
      {Object.entries(changes).map(([id, v]) => (
        <div key={id} style={{ marginTop: 12 }}>
          <label htmlFor={`sensor-${id}`}>
            Sensor {id} adjustment{" "}
            <b style={{ float: "right" }}>
              {v > 0 ? "+" : ""}
              {v}%
            </b>
          </label>
          <input
            id={`sensor-${id}`}
            type="range"
            min="-10"
            max="10"
            step="1"
            value={v}
            onChange={(e) =>
              setChanges((c) => ({ ...c, [id]: +e.target.value }))
            }
          />
        </div>
      ))}
      <div className={s.controls}>
        <Button
          variant="default"
          disabled={busy}
          onClick={() => void predict()}
        >
          {busy ? "Calculating…" : error ? "Retry prediction" : "Run what-if"}
          <ArrowRight size={14} />
        </Button>
        <Button
          onClick={() => {
            request.current?.abort();
            setBusy(false);
            setChanges({ "2": 0, "4": 0, "11": 0 });
            setResult(null);
            setError("");
          }}
          aria-label="Reset sensor adjustments"
        >
          <RotateCcw size={14} />
        </Button>
      </div>
      {error && (
        <p role="alert" className={s.critical} style={{ marginTop: 12 }}>
          {error}
        </p>
      )}
      {result !== null && (
        <p role="status" className={s.notice}>
          {valid
            ? `${resultModel}: ${result.toFixed(1)} cycles remaining.`
            : "Inputs changed. Run what-if again to update the result."}
        </p>
      )}
      <p className={s.subtitle}>
        No causal claim or calibrated confidence. Sensor perturbations may leave
        the training distribution.
      </p>
    </section>
  );
}
