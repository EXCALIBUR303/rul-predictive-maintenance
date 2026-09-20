from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np


@dataclass(frozen=True)
class RegressionMetrics:
    mae: float
    rmse: float
    nasa_score: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def clip_predictions(predictions: np.ndarray, rul_cap: float = 125.0) -> np.ndarray:
    return np.clip(np.asarray(predictions, dtype=float), 0.0, rul_cap)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y_pred, dtype=float) - np.asarray(y_true, dtype=float))))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(math.sqrt(np.mean((np.asarray(y_pred, dtype=float) - np.asarray(y_true, dtype=float)) ** 2)))


def nasa_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    errors = np.asarray(y_pred, dtype=float) - np.asarray(y_true, dtype=float)
    early = errors < 0
    scores = np.empty_like(errors, dtype=float)
    scores[early] = np.exp(-errors[early] / 13.0) - 1.0
    scores[~early] = np.exp(errors[~early] / 10.0) - 1.0
    return float(scores.sum())


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray, rul_cap: float = 125.0) -> RegressionMetrics:
    clipped = clip_predictions(y_pred, rul_cap=rul_cap)
    return RegressionMetrics(mae=mae(y_true, clipped), rmse=rmse(y_true, clipped), nasa_score=nasa_score(y_true, clipped))

