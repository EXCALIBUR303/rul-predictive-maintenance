"use client";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  BarChart,
  Bar,
} from "recharts";
import { motion, useReducedMotion } from "motion/react";
import { colors, models, names, type Point, type Model } from "../types";
const axis = {
  tick: { fill: "var(--muted)", fontSize: 11 },
  axisLine: false,
  tickLine: false,
};
const tooltip = {
  contentStyle: {
    background: "var(--panel)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    color: "var(--text)",
  },
  labelStyle: { color: "var(--text)" },
};
export default function Charts({
  points,
  active = models.slice(),
  kind = "rul",
}: {
  points: Point[];
  active?: Model[];
  kind?: "rul" | "sensor" | "residual" | "distribution";
}) {
  const reduced = useReducedMotion();
  const sampled = points.filter(
    (_, i) =>
      i % Math.max(1, Math.floor(points.length / 80)) === 0 ||
      i === points.length - 1,
  );
  const residuals = sampled.map((p) => ({
    cycle: p.cycle,
    ...Object.fromEntries(
      models.map((m) => [
        m,
        p[m] === undefined ? undefined : Number((p[m]! - p.actual).toFixed(2)),
      ]),
    ),
  }));
  const bins = Array.from({ length: 9 }, (_, i) => ({
    bin: i === 0 ? "<−17.5" : i === 8 ? "≥17.5" : `${i * 5 - 20}`,
    count: points.filter(
      (p) =>
        p.xgboost !== undefined &&
        (i === 0 || p.xgboost - p.actual >= i * 5 - 22.5) &&
        (i === 8 || p.xgboost - p.actual < i * 5 - 17.5),
    ).length,
  }));
  return (
    <motion.div
      initial={reduced ? false : { clipPath: "inset(0 100% 0 0)" }}
      animate={{ clipPath: "inset(0 0% 0 0)" }}
      transition={{ duration: 0.45 }}
      style={{ height: 260, width: "100%", minWidth: 0 }}
      role="img"
      aria-label={
        kind === "rul"
          ? "Remaining useful life in cycles, actual and selected models"
          : kind === "sensor"
            ? "Sensor 11 trajectory through selected cycle"
            : kind === "residual"
              ? "Predicted minus actual RUL by cycle"
              : "XGBoost residual distribution in five-cycle bins"
      }
    >
      <ResponsiveContainer
        width="100%"
        height="100%"
        initialDimension={{ width: 600, height: 260 }}
      >
        {kind === "distribution" ? (
          <BarChart data={bins}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="bin" {...axis} />
            <YAxis {...axis} />
            <Tooltip {...tooltip} />
            <Bar
              dataKey="count"
              fill={colors.xgboost}
              radius={[4, 4, 0, 0]}
              isAnimationActive={false}
            />
          </BarChart>
        ) : kind === "sensor" ? (
          <AreaChart
            data={sampled.map((p) => ({
              cycle: p.cycle,
              value: p.sensors["11"],
            }))}
          >
            <defs>
              <linearGradient id="sensorFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="var(--accent)" stopOpacity={0.3} />
                <stop offset="1" stopColor="var(--accent)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="cycle" {...axis} />
            <YAxis domain={["auto", "auto"]} {...axis} width={48} />
            <Tooltip {...tooltip} />
            <Area
              type="linear"
              dataKey="value"
              stroke="var(--accent)"
              fill="url(#sensorFill)"
              isAnimationActive={false}
            />
          </AreaChart>
        ) : (
          <LineChart data={kind === "residual" ? residuals : sampled}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="cycle" {...axis} />
            <YAxis
              {...axis}
              width={36}
              domain={kind === "rul" ? [0, 130] : ["auto", "auto"]}
            />
            <Tooltip {...tooltip} />
            {kind === "rul" ? (
              <>
                <ReferenceLine
                  y={30}
                  stroke="var(--critical)"
                  strokeDasharray="3 5"
                />
                <Line
                  dataKey="actual"
                  name="Actual RUL"
                  stroke="var(--muted)"
                  strokeDasharray="5 5"
                  dot={false}
                  isAnimationActive={false}
                />
              </>
            ) : (
              <ReferenceLine y={0} stroke="var(--muted)" />
            )}
            {active.map((m) => (
              <Line
                key={m}
                type="linear"
                dataKey={m}
                name={names[m]}
                stroke={colors[m]}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </motion.div>
  );
}
