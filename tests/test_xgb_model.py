from __future__ import annotations

import numpy as np

from rul_pm.models.xgb_model import XGBoostRulModel


def test_xgboost_uses_configured_early_stopping_and_safe_default_workers():
    x = np.arange(40, dtype=np.float32).reshape(20, 2)
    y = np.linspace(0.0, 10.0, 20, dtype=np.float32)
    model = XGBoostRulModel({"n_estimators": 10, "max_depth": 2}, rul_cap=10, seed=5)
    model.fit(x[:15], y[:15], x[15:], y[15:], early_stopping_rounds=2)
    assert model.model.get_params()["n_jobs"] == 1
    assert model.model.get_params()["early_stopping_rounds"] == 2
    assert np.all((0.0 <= model.predict(x[15:])) & (model.predict(x[15:]) <= 10.0))
