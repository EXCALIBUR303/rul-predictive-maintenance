from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rul_pm.data.io import COLUMNS, SENSOR_COLUMNS, SETTING_COLUMNS


@pytest.fixture
def synthetic_cmapss_frame():
    return _synthetic_cmapss_frame


@pytest.fixture
def write_cmapss_table():
    return _write_cmapss_table


def _synthetic_cmapss_frame(n_units: int = 6, cycles: int = 40) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(123)
    for unit in range(1, n_units + 1):
        unit_offset = unit * 0.05
        for cycle in range(1, cycles + 1):
            degradation = cycle / cycles
            settings = [0.0, 0.0, 100.0]
            sensors = []
            for idx in range(1, 22):
                if idx in {1, 5}:
                    sensors.append(1.0)
                else:
                    sensors.append(float(idx + unit_offset + degradation * idx * 0.1 + rng.normal(0, 0.01)))
            rows.append([unit, cycle, *settings, *sensors])
    return pd.DataFrame(rows, columns=COLUMNS)


def _write_cmapss_table(path, frame: pd.DataFrame) -> None:
    lines = []
    for row in frame.itertuples(index=False):
        lines.append(" ".join(str(value) for value in row) + "   ")
    path.write_text("\n".join(lines), encoding="utf-8")
