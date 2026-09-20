from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class WindowArrays:
    x: np.ndarray
    y: np.ndarray | None
    mask: np.ndarray
    unit_numbers: np.ndarray
    end_cycles: np.ndarray


def build_sequence_windows(
    frame: pd.DataFrame,
    feature_columns: list[str],
    window_length: int,
    target_column: str | None = "RUL",
    last_only: bool = False,
    pad_value: float = 0.0,
) -> WindowArrays:
    windows: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    targets: list[float] = []
    units: list[int] = []
    end_cycles: list[int] = []
    for unit, group in frame.sort_values(["unit_number", "time_in_cycles"]).groupby("unit_number", sort=True):
        values = group[feature_columns].to_numpy(dtype=np.float32)
        cycles = group["time_in_cycles"].to_numpy(dtype=int)
        target_values = group[target_column].to_numpy(dtype=np.float32) if target_column and target_column in group else None
        end_indices = [len(group) - 1] if last_only else list(range(window_length - 1, len(group)))
        if len(group) < window_length:
            end_indices = [len(group) - 1] if last_only else [len(group) - 1]
        for end_idx in end_indices:
            start = max(0, end_idx - window_length + 1)
            raw_window = values[start : end_idx + 1]
            window, mask = left_pad(raw_window, window_length, pad_value=pad_value)
            windows.append(window)
            masks.append(mask)
            units.append(int(unit))
            end_cycles.append(int(cycles[end_idx]))
            if target_values is not None:
                targets.append(float(target_values[end_idx]))
    y = np.asarray(targets, dtype=np.float32) if targets else None
    return WindowArrays(
        x=np.asarray(windows, dtype=np.float32),
        y=y,
        mask=np.asarray(masks, dtype=bool),
        unit_numbers=np.asarray(units, dtype=int),
        end_cycles=np.asarray(end_cycles, dtype=int),
    )


def build_xgb_window_features(
    frame: pd.DataFrame,
    feature_columns: list[str],
    window_length: int,
    target_column: str | None = "RUL",
    last_only: bool = False,
) -> tuple[np.ndarray, np.ndarray | None, list[str], pd.DataFrame]:
    seq = build_sequence_windows(
        frame=frame,
        feature_columns=feature_columns,
        window_length=window_length,
        target_column=target_column,
        last_only=last_only,
    )
    names = _xgb_feature_names(feature_columns)
    rows = []
    for idx in range(seq.x.shape[0]):
        valid = seq.x[idx][seq.mask[idx]]
        rows.append(_window_stats(valid))
    matrix = np.asarray(rows, dtype=np.float32)
    meta = pd.DataFrame({"unit_number": seq.unit_numbers, "time_in_cycles": seq.end_cycles})
    return matrix, seq.y, names, meta


def left_pad(window: np.ndarray, window_length: int, pad_value: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    if window.ndim != 2:
        raise ValueError("window must have shape (time, features).")
    if len(window) > window_length:
        raise ValueError("window is longer than requested length.")
    out = np.full((window_length, window.shape[1]), pad_value, dtype=np.float32)
    mask = np.zeros(window_length, dtype=bool)
    out[-len(window) :] = window
    mask[-len(window) :] = True
    return out, mask


def _window_stats(window: np.ndarray) -> np.ndarray:
    t = np.arange(window.shape[0], dtype=np.float32)
    t_centered = t - t.mean()
    denom = float(np.sum(t_centered**2)) or 1.0
    centered = window - window.mean(axis=0, keepdims=True)
    slope = (t_centered[:, None] * centered).sum(axis=0) / denom
    stats = [
        window.mean(axis=0),
        window.std(axis=0),
        window.min(axis=0),
        window.max(axis=0),
        window[-1],
        slope,
        window[-1] - window[0],
    ]
    return np.concatenate(stats, axis=0)


def _xgb_feature_names(feature_columns: list[str]) -> list[str]:
    stats = ["mean", "std", "min", "max", "last", "slope", "delta"]
    return [f"{column}__{stat}" for stat in stats for column in feature_columns]

