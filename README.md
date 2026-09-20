# Intelligent Predictive Maintenance System

A leakage-safe Remaining Useful Life (RUL) pipeline for NASA C-MAPSS FD001 and
FD004.
It compares XGBoost against LSTM, GRU, and a small Transformer under one
engine-level experimental protocol, with the official test set held out until
final evaluation.

## Published FD001 Result

| Model | MAE | RMSE | NASA/PHM08 Score |
| --- | ---: | ---: | ---: |
| XGBoost | 9.263 +/- 0.368 | 12.369 +/- 0.161 | 239.092 +/- 9.234 |
| Transformer | 9.886 +/- 0.210 | 13.574 +/- 0.331 | 338.386 +/- 25.927 |
| LSTM | 10.019 +/- 0.174 | 13.805 +/- 0.294 | 356.955 +/- 38.283 |
| GRU | 10.038 +/- 0.410 | 13.856 +/- 0.465 | 340.976 +/- 47.797 |

These are the actual results from three seeds (`42`, `1337`, and `2026`), not
tuned showcase values. XGBoost was best on every reported aggregate metric.
See [the FD001 experiment card](docs/EXPERIMENT_CARD_FD001.md) for the full
protocol, leakage controls, and limitations.

## Published FD004 Result

| Model | MAE | RMSE | NASA/PHM08 Score |
| --- | ---: | ---: | ---: |
| XGBoost | 11.177 +/- 0.086 | 15.924 +/- 0.150 | 1442.499 +/- 166.958 |
| Transformer | 11.382 +/- 0.822 | 16.387 +/- 1.596 | 1706.756 +/- 679.180 |
| GRU | 10.787 +/- 0.518 | 16.447 +/- 1.009 | 1909.921 +/- 580.499 |
| LSTM | 11.331 +/- 0.936 | 17.963 +/- 2.509 | 4575.788 +/- 4984.534 |

These are the actual results from the fixed three-seed protocol. XGBoost has
the strongest aggregate RMSE and NASA Score; GRU has the lowest aggregate MAE.
The large LSTM NASA-Score variance is retained because one seed made several
severe RUL underestimates. See [the FD004 experiment card](docs/EXPERIMENT_CARD_FD004.md).

## Why This Is Trustworthy

- C-MAPSS files are validated against their 26-column schema.
- RUL labels are capped at 125 cycles.
- Train/validation partitions are split by engine, before preprocessing or
  window construction.
- Feature selection, scaling, and optional operating-regime handling fit only
  on training engines and persist with the run artifact.
- Windows are constructed per engine, never across engine boundaries.
- XGBoost summary features and neural inputs use the same 30-cycle context.
- The official test set is isolated from fitting, preprocessing, model
  selection, and early stopping.
- Training and serving load the same serialized preprocessor and window code.

## Quick Start

Requires Python 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
make install-all
make data-fd001
make eda-fd001
make data-fd004
make eda-fd004
make test
```

`make data-fd001` downloads NASA's original Turbofan Engine Degradation
Simulation archive and extracts only `train_FD001.txt`, `test_FD001.txt`, and
`RUL_FD001.txt` into `data/raw/CMAPSSData/`. The raw data is intentionally not
committed. Its provenance is NASA's [C-MAPSS data repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/).

NASA's full C-MAPSS download is currently unavailable. `make data-fd004` uses
a pinned raw-text mirror whose FD001 files were verified byte-for-byte against
the NASA archive used above; it verifies SHA-256 for each FD004 file. The
exact fallback provenance is recorded in the FD004 experiment card.

## Reproduce The Comparison

```bash
make experiment-fd001
make experiment-fd004
```

The comparison retrains 12 model/seed combinations, chooses checkpoints using
validation RMSE, and only then evaluates every completed run on the official
test set. It writes per-seed metrics, aggregate comparison tables, plots, and
run directories. The tracked aggregate results are in `results/FD001/`; raw
data, model checkpoints, and per-run artifacts live under ignored paths.

For one XGBoost run:

```bash
make train-xgboost-fd001
.venv/bin/python -m rul_pm.cli evaluate --run-dir runs/FD001/xgboost/latest
```

## Serve A Trained Model

```bash
export RULPM_ARTIFACT_DIR=runs/FD001/xgboost/latest
make serve
```

The FastAPI app loads the persisted preprocessor and model artifact from
`RULPM_ARTIFACT_DIR`. It returns a point prediction and stored historical
metrics; it does not claim per-prediction uncertainty.

## Repository Map

```text
configs/       Fixed FD001 and FD004 experiment configurations
docs/          Experiment cards and methodological boundaries
scripts/       Dataset acquisition helper
src/rul_pm/    Ingestion, preprocessing, windows, models, training, API
tests/         Leakage, boundary, persistence, and API-parity tests
results/       Versioned aggregate FD001 and FD004 experimental results
```

GitHub Actions runs the test suite without downloading the dataset or running
the expensive full experiment.
