# FD001 Experiment Card

## Purpose

This card records the experimental boundary for the published FD001 comparison.
It is a reproducible baseline for C-MAPSS remaining-useful-life prediction, not
a claim that one model family universally dominates another.

## Data and Target

- Dataset: NASA C-MAPSS FD001, consisting of 100 run-to-failure training
  engines and 100 official test engines.
- Target: remaining useful life calculated from each training engine's final
  observed cycle, then capped at 125 cycles.
- Test labels: the official `RUL_FD001.txt` vector, paired with each test
  engine's final observed cycle and capped at the same 125-cycle bound.
- Source: NASA's Turbofan Engine Degradation Simulation Data Set. The helper
  script downloads the original archive and extracts only the three FD001
  files used by this repository.

## Leakage Controls

- Train/validation splits are made by engine identifier, never by row or
  temporal window.
- The preprocessor is fit only on the training-engine partition for each seed.
  Its selected features, low-variance decisions, and scaler are persisted and
  reused for validation, official testing, and serving.
- Windows are grouped by engine, so no sequence can cross an engine boundary.
- The official test set is not loaded by the training/split/preprocessing path.
  In the comparison runner it is evaluated only after all model-and-seed
  training runs have completed.

## Common Protocol

| Setting | Value |
| --- | --- |
| Seeds | 42, 1337, 2026 |
| Validation split | 20% of training engines per seed |
| Window length | 30 cycles |
| Scaling | Min-max, fit per training split |
| RUL cap | 125 cycles |
| Selection metric | Validation RMSE |
| Final metrics | MAE, RMSE, NASA/PHM08 asymmetric score |
| Models | XGBoost, LSTM, GRU, small Transformer |

XGBoost receives summary statistics computed from the same 30-cycle input
windows used by the sequence models. Each sequence model receives a left-pad
mask; the Transformer applies that mask in attention and pooling.

## Results

The final test metrics are means plus sample standard deviations across the
three independently seeded train/validation splits.

| Model | MAE | RMSE | NASA/PHM08 Score |
| --- | ---: | ---: | ---: |
| XGBoost | 9.263 +/- 0.368 | 12.369 +/- 0.161 | 239.092 +/- 9.234 |
| Transformer | 9.886 +/- 0.210 | 13.574 +/- 0.331 | 338.386 +/- 25.927 |
| LSTM | 10.019 +/- 0.174 | 13.805 +/- 0.294 | 356.955 +/- 38.283 |
| GRU | 10.038 +/- 0.410 | 13.856 +/- 0.465 | 340.976 +/- 47.797 |

XGBoost achieved the strongest aggregate result for every reported metric in
this fixed protocol. The result tables are versioned in
`results/FD001/model_comparison.csv` and `results/FD001/per_seed_metrics.csv`.

## Artifacts

Each model/seed run records its resolved configuration, engine split metadata,
feature list, serialized train-only preprocessor, trained model or checkpoints,
logs, final test predictions, metrics, and diagnostic plots under `runs/`.
Large run artifacts and raw source data are intentionally excluded from Git.

## Reproduce

```bash
make install-all
make data-fd001
make eda-fd001
make experiment-fd001
```

The full experiment retrains 12 model/seed combinations. It is deliberately
not part of CI; CI exercises the unit and integration tests without downloading
the data or using the official test split.

## Limitations

- These are FD001-only results. They do not establish performance on FD004,
  which has more operating conditions and fault modes.
- The three seed results quantify sensitivity to seeded train/validation
  partitions and training randomness. They are not confidence intervals over
  three independent official test datasets, because every run uses FD001's
  same 100 test engines.
- This is point prediction. The serving API does not provide calibrated
  uncertainty or maintenance decision thresholds.
