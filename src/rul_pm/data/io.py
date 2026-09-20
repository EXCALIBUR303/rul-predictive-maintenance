from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SETTING_COLUMNS = [f"op_setting_{idx}" for idx in range(1, 4)]
SENSOR_COLUMNS = [f"sensor_{idx}" for idx in range(1, 22)]
COLUMNS = ["unit_number", "time_in_cycles", *SETTING_COLUMNS, *SENSOR_COLUMNS]


@dataclass(frozen=True)
class CmapssSubset:
    subset: str
    train: pd.DataFrame
    test: pd.DataFrame
    test_rul: pd.Series


def read_cmapss_table(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    frame = pd.read_csv(source, sep=r"\s+", header=None, engine="python")
    frame = frame.dropna(axis=1, how="all")
    if frame.shape[1] != len(COLUMNS):
        raise ValueError(f"{source} has {frame.shape[1]} columns after parsing; expected {len(COLUMNS)}.")
    frame.columns = COLUMNS
    frame["unit_number"] = frame["unit_number"].astype(int)
    frame["time_in_cycles"] = frame["time_in_cycles"].astype(int)
    float_columns = SETTING_COLUMNS + SENSOR_COLUMNS
    frame[float_columns] = frame[float_columns].astype(float)
    if frame.isna().any().any():
        raise ValueError(f"{source} contains NaN values after ingestion.")
    return frame


def read_rul_file(path: str | Path) -> pd.Series:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    values = pd.read_csv(source, sep=r"\s+", header=None, engine="python").dropna(axis=1, how="all")
    if values.shape[1] != 1:
        raise ValueError(f"{source} has {values.shape[1]} columns after parsing; expected 1.")
    return values.iloc[:, 0].astype(float).rename("provided_rul")


def load_training_data(data_dir: str | Path, subset: str) -> pd.DataFrame:
    """Load only the run-to-failure training trajectories for a subset.

    Training must not even read the official test files; those are reserved for
    final evaluation in ``load_subset``.
    """
    root = Path(data_dir)
    return read_cmapss_table(root / f"train_{subset.upper()}.txt")


def load_subset(data_dir: str | Path, subset: str) -> CmapssSubset:
    root = Path(data_dir)
    subset = subset.upper()
    train = read_cmapss_table(root / f"train_{subset}.txt")
    test = read_cmapss_table(root / f"test_{subset}.txt")
    test_rul = read_rul_file(root / f"RUL_{subset}.txt")
    n_test_units = test["unit_number"].nunique()
    if len(test_rul) != n_test_units:
        raise ValueError(f"{subset} RUL file has {len(test_rul)} rows but test data has {n_test_units} units.")
    return CmapssSubset(subset=subset, train=train, test=test, test_rul=test_rul)
