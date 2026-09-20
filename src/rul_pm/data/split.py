from __future__ import annotations

import numpy as np
import pandas as pd


def grouped_train_val_units(
    frame: pd.DataFrame, validation_fraction: float = 0.2, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1.")
    units = np.array(sorted(frame["unit_number"].unique()))
    rng = np.random.default_rng(seed)
    shuffled = units.copy()
    rng.shuffle(shuffled)
    n_val = max(1, int(round(len(units) * validation_fraction)))
    val_units = np.sort(shuffled[:n_val])
    train_units = np.sort(shuffled[n_val:])
    if set(train_units).intersection(set(val_units)):
        raise AssertionError("Train and validation engine sets overlap.")
    return train_units, val_units


def filter_units(frame: pd.DataFrame, units: np.ndarray) -> pd.DataFrame:
    return frame[frame["unit_number"].isin(set(map(int, units)))].copy()

