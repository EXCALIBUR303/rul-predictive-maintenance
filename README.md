# Intelligent Predictive Maintenance System

This repository implements a leakage-safe Remaining Useful Life (RUL) pipeline for the NASA C-MAPSS turbofan dataset. It follows the supplied technical spec: FD001 first, capped RUL labels, grouped engine splits, train-only preprocessing, identical temporal windows for XGBoost and sequence models, and shared preprocessing between training and serving.

## What Is Implemented

- C-MAPSS ingestion with explicit 26-column validation.
- Piecewise-linear capped RUL target construction.
- Engine-level train/validation splits.
- Train-only preprocessing with persisted feature order, scalers, low-variance sensor drops, and optional KMeans operating-regime normalization for FD002/FD004.
- Sliding sequence windows and matching XGBoost summary-window features.
- Metrics: MAE, RMSE, NASA/PHM08 asymmetric score.
- Model wrappers for XGBoost, LSTM, GRU, and a small Transformer encoder.
- Training/evaluation CLI entry points.
- FastAPI inference app that loads persisted preprocessing and uses the same transform/window code as offline training.
- Tests for ingestion, RUL construction, window boundaries, metrics, and preprocessing leakage invariants.

## Dataset Layout

Download C-MAPSS separately and place the files like this:

```text
data/raw/CMAPSSData/
  train_FD001.txt
  test_FD001.txt
  RUL_FD001.txt
  train_FD004.txt
  test_FD004.txt
  RUL_FD004.txt
```

The dataset is intentionally not committed.

## Setup

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev,models,api]"
```

For data/preprocessing tests only, `uv pip install -e ".[dev]"` is enough.

## Run FD001

```bash
rulpm eda --config configs/fd001.yaml
rulpm train --config configs/fd001.yaml --model xgboost
rulpm evaluate --run-dir runs/FD001/xgboost/latest
```

Run the fixed three-seed comparison only after the FD001 data gate passes:

```bash
rulpm experiment --config configs/fd001.yaml
```

This command trains all model/seed combinations before reading the official
test split, then saves per-seed metrics, mean and standard deviation comparison
tables, and diagnostic plots under `results/FD001/`.

Neural models require the `models` extra:

```bash
rulpm train --config configs/fd001.yaml --model lstm
rulpm train --config configs/fd001.yaml --model gru
rulpm train --config configs/fd001.yaml --model transformer
```

## Serve A Model

```bash
uvicorn rul_pm.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Set `RULPM_ARTIFACT_DIR` to the run directory containing `preprocessor.joblib`, model artifacts, and metadata. The API returns a point prediction plus the model's historical validation/test metrics when available; it does not fabricate per-prediction confidence.

## Reproducibility Notes

Each run directory stores the resolved config, feature list, preprocessing artifact, metrics, and model artifact. The official test set is only used in `evaluate`, not during fitting, preprocessing, tuning, or early stopping.
