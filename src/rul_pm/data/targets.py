from __future__ import annotations

import numpy as np
import pandas as pd


def add_train_rul(frame: pd.DataFrame, rul_cap: float = 125.0, column: str = "RUL") -> pd.DataFrame:
    data = frame.copy()
    max_cycle = data.groupby("unit_number")["time_in_cycles"].transform("max")
    data[column] = np.minimum(max_cycle - data["time_in_cycles"], rul_cap).astype(float)
    return data


def capped_test_last_rul(test: pd.DataFrame, provided_rul: pd.Series, rul_cap: float = 125.0) -> pd.DataFrame:
    units = sorted(test["unit_number"].unique())
    provided = np.asarray(provided_rul, dtype=float)
    if len(units) != len(provided):
        raise ValueError("Provided RUL count does not match number of test engines.")
    return pd.DataFrame(
        {
            "unit_number": units,
            "RUL": np.minimum(provided, rul_cap),
            "provided_RUL_uncapped": provided,
        }
    )


def add_reconstructed_test_rul(
    test: pd.DataFrame, provided_rul: pd.Series, rul_cap: float = 125.0, column: str = "RUL"
) -> pd.DataFrame:
    data = test.copy()
    last_cycles = data.groupby("unit_number")["time_in_cycles"].transform("max")
    units = sorted(data["unit_number"].unique())
    rul_by_unit = dict(zip(units, np.asarray(provided_rul, dtype=float), strict=True))
    data[column] = [
        min(rul_by_unit[int(unit)] + (last_cycle - cycle), rul_cap)
        for unit, last_cycle, cycle in zip(data["unit_number"], last_cycles, data["time_in_cycles"], strict=True)
    ]
    return data
