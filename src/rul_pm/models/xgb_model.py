from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# XGBoost 3.x's OpenMP runtime can crash on macOS after loading a persisted
# model unless its worker pool is constrained before xgboost is imported.
if sys.platform == "darwin":
    os.environ.setdefault("OMP_NUM_THREADS", "1")

try:
    from xgboost import XGBRegressor
except Exception as exc:  # pragma: no cover - exercised when optional extra is absent
    XGBRegressor = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _require_xgboost() -> None:
    if XGBRegressor is None:
        raise ImportError("Install the 'models' extra to use XGBoost: uv pip install -e '.[models]'") from _IMPORT_ERROR


class XGBoostRulModel:
    def __init__(self, params: dict[str, Any], rul_cap: float = 125.0, seed: int = 42) -> None:
        _require_xgboost()
        params = dict(params)
        params.setdefault("random_state", seed)
        # A single worker is reliable on macOS and sufficient for the modest
        # C-MAPSS training matrices. Callers can opt into more workers in config.
        params.setdefault("n_jobs", 1)
        self.rul_cap = rul_cap
        self.model = XGBRegressor(**params)

    def fit(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        early_stopping_rounds: int | None = None,
    ) -> "XGBoostRulModel":
        kwargs: dict[str, Any] = {}
        if x_val is not None and y_val is not None:
            kwargs["eval_set"] = [(x_val, y_val)]
            kwargs["verbose"] = False
            if early_stopping_rounds:
                # XGBoost 3.x removed this keyword from fit(); configuring the
                # estimator works in current and earlier supported releases.
                self.model.set_params(early_stopping_rounds=early_stopping_rounds)
        self.model.fit(x_train, y_train, **kwargs)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.clip(self.model.predict(x), 0.0, self.rul_cap)

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, target)

    @staticmethod
    def load(path: str | Path) -> "XGBoostRulModel":
        obj = joblib.load(path)
        if not isinstance(obj, XGBoostRulModel):
            raise TypeError(f"{path} did not contain an XGBoostRulModel.")
        return obj
