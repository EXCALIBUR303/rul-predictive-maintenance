# FD004 Experiment Card

## Purpose

This card records the FD004 comparison under the same leakage-safe protocol as
the published FD001 baseline. FD004 has six operating conditions and two fault
modes, so condition-wise preprocessing is central to this experiment.

## Data And Provenance

- Dataset: NASA C-MAPSS FD004, with 249 run-to-failure training engines and
  248 official test engines.
- Raw rows: 61,249 train and 41,214 test. The shortest test trajectory has 19
  cycles, so the 30-cycle window path left-pads short trajectories and retains
  every test engine.
- Target: training RUL and final-cycle official test labels are capped at 125
  cycles.
- NASA's full C-MAPSS download is currently unavailable. The acquisition
  helper therefore uses the raw-text `PunVas/nasa-c-mapss` mirror, pinned to
  commit `2b562334f2114d9dadfc0861dededc16cf2550d9`. Its FD001 files exactly
  matched the NASA-sourced FD001 archive already used in this project.
- Verified FD004 SHA-256: `train_FD004.txt`
  `27ef6160b6a1dcb2613a88de9c239f763b223f02cdc41dc5cdedc5dc189b6218`,
  `test_FD004.txt`
  `1dc675fff0624bac10786927c6715b37d1297657137400d2b1a3138d777a3ba5`,
  and `RUL_FD004.txt`
  `196b836b85a95ac7fdbbf29c5fdf1657382eafa445644d114ffaaf50dc2975e1`.

## Leakage Controls

- Train/validation partitioning occurs by engine identifier before any fit or
  window creation.
- KMeans with six clusters and one min-max scaler per regime are fit only on
  training-engine rows. Sensor selection is then fit on the normalized
  training data and all artifacts persist with each run.
- Sequence and XGBoost windows are grouped by engine. No window crosses an
  engine boundary; short test trajectories are left-padded.
- XGBoost receives the same 30-cycle context as the neural models, plus the
  KMeans regime label at the final cycle.
- The official test set is not loaded during training. It is evaluated once
  all twelve model/seed training runs are complete.

## Common Protocol

| Setting | Value |
| --- | --- |
| Seeds | 42, 1337, 2026 |
| Validation split | 20% of training engines per seed |
| Window length | 30 cycles |
| Regimes | 6, discovered by train-only KMeans |
| Scaling | Per-regime min-max, fit per training split |
| RUL cap | 125 cycles |
| Selection metric | Validation RMSE |
| Final metrics | MAE, RMSE, NASA/PHM08 asymmetric score |
| Models | XGBoost, LSTM, GRU, small Transformer |

The Transformer receives the left-padding mask in both attention and masked
mean pooling. Checkpoints are selected by validation RMSE, never test metrics.

## Results

Values are mean plus sample standard deviation over three seeded
train/validation partitions. Each run evaluates the same 248 official test
engines after checkpoint selection.

| Model | MAE | RMSE | NASA/PHM08 Score |
| --- | ---: | ---: | ---: |
| XGBoost | 11.177 +/- 0.086 | 15.924 +/- 0.150 | 1442.499 +/- 166.958 |
| Transformer | 11.382 +/- 0.822 | 16.387 +/- 1.596 | 1706.756 +/- 679.180 |
| GRU | 10.787 +/- 0.518 | 16.447 +/- 1.009 | 1909.921 +/- 580.499 |
| LSTM | 11.331 +/- 0.936 | 17.963 +/- 2.509 | 4575.788 +/- 4984.534 |

XGBoost is best on aggregate RMSE and NASA Score. GRU has the lowest aggregate
MAE, but its RMSE and risk score are worse than XGBoost. LSTM seed 2026 made
several severe underestimates of engines whose capped target was 125 cycles;
the largest was -111.576 cycles. Its NASA Score was 10,326.047, so the high
LSTM score variance is a real stability warning, not an omitted outlier.

## Artifacts And Reproduction

Run artifacts under `runs/FD004/` include the resolved config, engine split,
serialized preprocessor, feature list, XGBoost feature names, checkpoints,
training logs, final predictions, metrics, and plots. Versioned aggregate
results are in `results/FD004/`.

```bash
make install-all
make data-fd004
make eda-fd004
make experiment-fd004
```

## Limitations

- The three seed results measure sensitivity to training randomness and the
  grouped validation split. They are not independent-test-set confidence
  intervals because every run uses the same FD004 official test set.
- The raw FD004 fallback is a verified public mirror, not a currently
  downloadable NASA-hosted full archive; its provenance must remain explicit.
- This is point regression, so the serving API does not provide calibrated
  per-prediction uncertainty or maintenance decision thresholds.
