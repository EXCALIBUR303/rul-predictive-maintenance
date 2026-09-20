import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from rul_pm.config import load_config
from rul_pm.data.preprocess import CmapssPreprocessor
from rul_pm.data.windows import build_sequence_windows, build_xgb_window_features
from rul_pm.evaluation.metrics import clip_predictions


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
    except Exception as exc:  # pragma: no cover - optional dependency guard
        raise ImportError("Install the 'api' extra to serve the app: uv pip install -e '.[api]'") from exc

    class PredictionRequest(BaseModel):
        rows: list[dict[str, Any]] = Field(..., description="One engine trajectory or the latest cycles for one engine.")

    artifact_dir = Path(os.environ.get("RULPM_ARTIFACT_DIR", "runs/FD001/xgboost/latest"))
    app = FastAPI(title="RUL Predictive Maintenance API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "artifact_dir": str(artifact_dir), "loaded": artifact_dir.exists()}

    @app.post("/predict")
    def predict(request: PredictionRequest) -> dict[str, Any]:
        try:
            bundle = _load_bundle(artifact_dir)
            frame = pd.DataFrame(request.rows)
            processed = bundle["preprocessor"].transform(frame)
            window_length = int(bundle["config"]["data"].get("window_length", 30))
            model_name = bundle["metadata"]["model"]
            if model_name == "xgboost":
                x, _, _, meta = build_xgb_window_features(
                    processed, bundle["preprocessor"].feature_columns, window_length, target_column=None, last_only=True
                )
                pred = bundle["model"].predict(x)
            else:
                arrays = build_sequence_windows(
                    processed, bundle["preprocessor"].feature_columns, window_length, target_column=None, last_only=True
                )
                pred = bundle["predict_torch"](artifact_dir / "best.pt", arrays)
                meta = pd.DataFrame({"unit_number": arrays.unit_numbers, "time_in_cycles": arrays.end_cycles})
            pred = clip_predictions(pred, rul_cap=float(bundle["config"]["data"].get("rul_cap", 125.0)))
            metrics = bundle.get("test_metrics") or bundle.get("training_summary", {}).get("val_metrics")
            return {
                "predictions": [
                    {
                        "unit_number": int(unit),
                        "time_in_cycles": int(cycle),
                        "predicted_rul": float(value),
                    }
                    for unit, cycle, value in zip(meta["unit_number"], meta["time_in_cycles"], np.ravel(pred), strict=True)
                ],
                "model": model_name,
                "typical_error_reference": metrics,
                "confidence": None,
                "confidence_note": "This point-regression model does not produce calibrated per-prediction confidence.",
            }
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


def _load_bundle(artifact_dir: Path) -> dict[str, Any]:
    if not artifact_dir.exists():
        raise FileNotFoundError(f"Artifact directory does not exist: {artifact_dir}")
    config = load_config(artifact_dir / "config.yaml")
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    preprocessor = CmapssPreprocessor.load(artifact_dir / "preprocessor.joblib")
    bundle: dict[str, Any] = {"config": config, "metadata": metadata, "preprocessor": preprocessor}
    if metadata["model"] == "xgboost":
        from rul_pm.models.xgb_model import XGBoostRulModel

        bundle["model"] = XGBoostRulModel.load(artifact_dir / "model.joblib")
    else:
        from rul_pm.training.torch_trainer import predict_torch_checkpoint

        bundle["predict_torch"] = predict_torch_checkpoint
    for name in ["test_metrics.json", "training_summary.json"]:
        path = artifact_dir / name
        if path.exists():
            bundle[name.removesuffix(".json")] = json.loads(path.read_text(encoding="utf-8"))
    return bundle
