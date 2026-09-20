from __future__ import annotations

import json

import numpy as np
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from rul_pm.api.app import create_app
from rul_pm.config import save_config
from rul_pm.data.preprocess import CmapssPreprocessor
from rul_pm.data.targets import add_train_rul
from rul_pm.data.windows import build_xgb_window_features
from rul_pm.models.xgb_model import XGBoostRulModel


def test_api_uses_the_same_xgboost_preprocessing_and_window_features(tmp_path, monkeypatch, synthetic_cmapss_frame):
    raw = synthetic_cmapss_frame(n_units=4, cycles=8)
    labeled = add_train_rul(raw, rul_cap=10)
    preprocessor = CmapssPreprocessor(n_regimes=1, low_unique_threshold=2).fit(labeled)
    processed = preprocessor.transform(labeled)
    x, y, names, _ = build_xgb_window_features(processed, preprocessor.feature_columns, window_length=4)
    model = XGBoostRulModel({"n_estimators": 4, "max_depth": 2, "n_jobs": 1}, rul_cap=10, seed=3).fit(x, y)

    save_config({"data": {"rul_cap": 10, "window_length": 4}}, tmp_path / "config.yaml")
    (tmp_path / "metadata.json").write_text(json.dumps({"model": "xgboost"}), encoding="utf-8")
    (tmp_path / "xgb_feature_names.json").write_text(json.dumps(names), encoding="utf-8")
    preprocessor.save(tmp_path / "preprocessor.joblib")
    model.save(tmp_path / "model.joblib")

    request_frame = raw[raw["unit_number"] == 1].copy()
    offline = preprocessor.transform(request_frame)
    offline_x, _, _, _ = build_xgb_window_features(offline, preprocessor.feature_columns, window_length=4, target_column=None, last_only=True)
    expected = model.predict(offline_x)

    monkeypatch.setenv("RULPM_ARTIFACT_DIR", str(tmp_path))
    response = TestClient(create_app()).post("/predict", json={"rows": request_frame.to_dict(orient="records")})
    assert response.status_code == 200
    actual = np.array([item["predicted_rul"] for item in response.json()["predictions"]])
    np.testing.assert_allclose(actual, expected, rtol=0, atol=0)
