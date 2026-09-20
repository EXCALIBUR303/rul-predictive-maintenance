from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from rul_pm.data.io import SENSOR_COLUMNS, SETTING_COLUMNS


@dataclass
class PreprocessorState:
    scaler: str = "minmax"
    n_regimes: int = 1
    low_variance_threshold: float = 1.0e-8
    low_unique_threshold: int = 2


class CmapssPreprocessor:
    def __init__(
        self,
        scaler: str = "minmax",
        n_regimes: int = 1,
        low_variance_threshold: float = 1.0e-8,
        low_unique_threshold: int = 2,
        random_state: int = 42,
    ) -> None:
        self.state = PreprocessorState(
            scaler=scaler,
            n_regimes=n_regimes,
            low_variance_threshold=low_variance_threshold,
            low_unique_threshold=low_unique_threshold,
        )
        self.random_state = random_state
        self.kmeans_: KMeans | None = None
        self.scalers_: dict[int, MinMaxScaler | StandardScaler] = {}
        self.retained_sensors_: list[str] = []
        self.dropped_sensors_: list[str] = []
        self.feature_columns_: list[str] = []
        self.fitted_ = False

    @property
    def feature_columns(self) -> list[str]:
        self._check_fitted()
        return list(self.feature_columns_)

    def fit(self, frame: pd.DataFrame) -> "CmapssPreprocessor":
        self._validate_frame(frame)
        data = frame.copy()
        regimes = self._fit_regimes(data)
        scaled = self._fit_scalers_and_transform(data, regimes)
        retained = []
        dropped = []
        for sensor in SENSOR_COLUMNS:
            variance = float(scaled[sensor].var(ddof=0))
            unique_count = int(scaled[sensor].nunique(dropna=False))
            if variance <= self.state.low_variance_threshold or unique_count <= self.state.low_unique_threshold:
                dropped.append(sensor)
            else:
                retained.append(sensor)
        if not retained:
            raise ValueError("All sensors were dropped by low-information filtering.")
        self.retained_sensors_ = retained
        self.dropped_sensors_ = dropped
        self.feature_columns_ = retained
        self.fitted_ = True
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        self._check_fitted()
        self._validate_frame(frame)
        data = frame.copy()
        regimes = self._predict_regimes(data)
        scaled = self._transform_with_scalers(data, regimes)
        scaled["regime_id"] = regimes.astype(int)
        keep = ["unit_number", "time_in_cycles", *SETTING_COLUMNS, *self.retained_sensors_, "regime_id"]
        if "RUL" in scaled.columns:
            keep.append("RUL")
        return scaled[keep].copy()

    def fit_transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        return self.fit(frame).transform(frame)

    def metadata(self) -> dict[str, Any]:
        self._check_fitted()
        return {
            **asdict(self.state),
            "random_state": self.random_state,
            "retained_sensors": list(self.retained_sensors_),
            "dropped_sensors": list(self.dropped_sensors_),
            "feature_columns": list(self.feature_columns_),
        }

    def save(self, path: str | Path) -> None:
        self._check_fitted()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, target)

    @staticmethod
    def load(path: str | Path) -> "CmapssPreprocessor":
        obj = joblib.load(path)
        if not isinstance(obj, CmapssPreprocessor):
            raise TypeError(f"{path} did not contain a CmapssPreprocessor.")
        return obj

    def _new_scaler(self) -> MinMaxScaler | StandardScaler:
        if self.state.scaler == "minmax":
            return MinMaxScaler(feature_range=(0.0, 1.0))
        if self.state.scaler in {"standard", "zscore"}:
            return StandardScaler()
        raise ValueError(f"Unsupported scaler: {self.state.scaler}")

    def _fit_regimes(self, frame: pd.DataFrame) -> np.ndarray:
        if self.state.n_regimes <= 1:
            self.kmeans_ = None
            return np.zeros(len(frame), dtype=int)
        self.kmeans_ = KMeans(n_clusters=self.state.n_regimes, random_state=self.random_state, n_init=20)
        return self.kmeans_.fit_predict(frame[SETTING_COLUMNS].to_numpy(dtype=float))

    def _predict_regimes(self, frame: pd.DataFrame) -> np.ndarray:
        if self.state.n_regimes <= 1:
            return np.zeros(len(frame), dtype=int)
        if self.kmeans_ is None:
            raise RuntimeError("KMeans regime model is missing.")
        return self.kmeans_.predict(frame[SETTING_COLUMNS].to_numpy(dtype=float)).astype(int)

    def _fit_scalers_and_transform(self, frame: pd.DataFrame, regimes: np.ndarray) -> pd.DataFrame:
        transformed = frame.copy()
        self.scalers_ = {}
        for regime in sorted(set(map(int, regimes))):
            mask = regimes == regime
            scaler = self._new_scaler()
            transformed.loc[mask, SENSOR_COLUMNS] = scaler.fit_transform(frame.loc[mask, SENSOR_COLUMNS])
            self.scalers_[regime] = scaler
        return transformed

    def _transform_with_scalers(self, frame: pd.DataFrame, regimes: np.ndarray) -> pd.DataFrame:
        transformed = frame.copy()
        for regime in sorted(set(map(int, regimes))):
            if regime not in self.scalers_:
                raise ValueError(f"No scaler was fitted for regime {regime}.")
            mask = regimes == regime
            transformed.loc[mask, SENSOR_COLUMNS] = self.scalers_[regime].transform(frame.loc[mask, SENSOR_COLUMNS])
        return transformed

    @staticmethod
    def _validate_frame(frame: pd.DataFrame) -> None:
        missing = {"unit_number", "time_in_cycles", *SETTING_COLUMNS, *SENSOR_COLUMNS}.difference(frame.columns)
        if missing:
            raise ValueError(f"Input frame is missing columns: {sorted(missing)}")
        if frame[["unit_number", "time_in_cycles", *SETTING_COLUMNS, *SENSOR_COLUMNS]].isna().any().any():
            raise ValueError("Input frame contains NaN values.")

    def _check_fitted(self) -> None:
        if not self.fitted_:
            raise RuntimeError("Preprocessor has not been fitted.")

