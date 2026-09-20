from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from rul_pm.evaluation.metrics import regression_metrics
from rul_pm.models.xgb_model import XGBoostRulModel


def train_xgboost(
    train_x,
    train_y,
    val_x,
    val_y,
    config: dict[str, Any],
    run_dir: str | Path,
    seed: int,
) -> dict[str, Any]:
    start = time.time()
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    xgb_cfg = dict(config.get("xgboost", {}))
    early_stopping_rounds = xgb_cfg.pop("early_stopping_rounds", None)
    model = XGBoostRulModel(xgb_cfg, rul_cap=float(config["data"].get("rul_cap", 125.0)), seed=seed)
    model.fit(train_x, train_y, val_x, val_y, early_stopping_rounds=early_stopping_rounds)
    val_pred = model.predict(val_x)
    metrics = regression_metrics(val_y, val_pred, rul_cap=float(config["data"].get("rul_cap", 125.0)))
    artifact = run_path / "model.joblib"
    model.save(artifact)
    payload = {
        "model": "xgboost",
        "seed": seed,
        "val_metrics": metrics.to_dict(),
        "train_time_seconds": time.time() - start,
        "artifact": str(artifact),
    }
    (run_path / "training_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

