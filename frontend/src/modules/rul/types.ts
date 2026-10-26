export const models = ["xgboost", "lstm", "gru", "transformer"] as const;
export type Model = (typeof models)[number];
export type Point = {
  cycle: number;
  actual: number;
  sensors: Record<string, number>;
  row: Record<string, number>;
  whatIf?: Partial<Record<Model, Record<string, Record<string, number>>>>;
} & Partial<Record<Model, number>>;
export type Engine = {
  id: number;
  name: string;
  cycles: number;
  current: number;
  points: Point[];
};
export type Metric = {
  model: Model;
  mae_mean: number;
  rmse_mean: number;
  nasa_score_mean: number;
  rmse_std: number | null;
};
export type Dataset = {
  schemaVersion: number;
  subset: string;
  predictionSource: string;
  trajectorySource: string;
  models: Model[];
  sensors: number[];
  engines: Engine[];
  correlation: number[][];
  metrics: Record<string, Metric[]>;
  metricSources?: Record<string, string>;
  importance?: Partial<
    Record<Model, { sensor: number; deltaMae: number; retained: boolean }[]>
  >;
  importanceSource?: string;
};
export const status = (rul: number) =>
  rul <= 30 ? "critical" : rul <= 60 ? "watch" : "healthy";
export const colors: Record<Model, string> = {
  xgboost: "var(--model-xgboost)",
  lstm: "var(--model-lstm)",
  gru: "var(--model-gru)",
  transformer: "var(--model-transformer)",
};
export const names: Record<Model, string> = {
  xgboost: "XGBoost",
  lstm: "LSTM",
  gru: "GRU",
  transformer: "Transformer",
};
