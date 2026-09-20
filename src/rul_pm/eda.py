from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from rul_pm.data.io import SENSOR_COLUMNS, load_subset


EXPECTED_COUNTS = {
    "FD001": {"train_units": 100, "test_units": 100},
    "FD002": {"train_units": 260, "test_units": 259},
    "FD003": {"train_units": 100, "test_units": 100},
    "FD004": {"train_units": 249, "test_units": 248},
}


def run_eda(config: dict) -> dict:
    subset = config["experiment"]["subset"].upper()
    loaded = load_subset(config["experiment"]["data_dir"], subset)
    output_dir = Path("results") / "eda" / subset
    output_dir.mkdir(parents=True, exist_ok=True)
    train_lengths = loaded.train.groupby("unit_number")["time_in_cycles"].max()
    test_lengths = loaded.test.groupby("unit_number")["time_in_cycles"].max()
    sensor_variance = loaded.train[SENSOR_COLUMNS].var(ddof=0).sort_values()
    constant_sensors = sensor_variance[sensor_variance <= float(config["data"].get("low_variance_threshold", 1.0e-8))].index.tolist()
    summary = {
        "subset": subset,
        "train_units": int(loaded.train["unit_number"].nunique()),
        "test_units": int(loaded.test["unit_number"].nunique()),
        "train_rows": int(len(loaded.train)),
        "test_rows": int(len(loaded.test)),
        "train_length": _series_stats(train_lengths),
        "test_length": _series_stats(test_lengths),
        "constant_sensor_reference": constant_sensors,
        "expected_counts": EXPECTED_COUNTS.get(subset),
    }
    if subset in EXPECTED_COUNTS:
        expected = EXPECTED_COUNTS[subset]
        if summary["train_units"] != expected["train_units"] or summary["test_units"] != expected["test_units"]:
            raise ValueError(f"{subset} counts differ from C-MAPSS reference counts: {summary} vs {expected}")
    (output_dir / "eda_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    sensor_variance.to_csv(output_dir / "sensor_variance.csv", header=["variance"])
    return summary


def _series_stats(series: pd.Series) -> dict[str, float]:
    return {
        "min": float(series.min()),
        "median": float(series.median()),
        "max": float(series.max()),
    }

