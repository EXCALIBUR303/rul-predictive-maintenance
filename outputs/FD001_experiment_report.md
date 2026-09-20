# FD001 Experimental Report

## Protocol

- Data: NASA C-MAPSS FD001, validated at 100 training engines, 100 test engines, 20,631 training rows, and 13,096 test rows.
- Target: piecewise-linear RUL capped at 125 cycles; predictions were clipped to the same range.
- Splits: three seeded 80/20 train/validation engine-level partitions (`42`, `1337`, `2026`).
- Context: 30-cycle windows for every model. XGBoost used summary statistics over the identical windows.
- Selection: validation RMSE only. The official test data was evaluated only after every model and seed had finished training.
- Metrics: mean plus sample standard deviation across the three final test evaluations.

## Final Comparison

| Model | MAE | RMSE | NASA/PHM08 Score |
| --- | ---: | ---: | ---: |
| XGBoost | 9.263 +/- 0.368 | 12.369 +/- 0.161 | 239.092 +/- 9.234 |
| Transformer | 9.886 +/- 0.210 | 13.574 +/- 0.331 | 338.386 +/- 25.927 |
| LSTM | 10.019 +/- 0.174 | 13.805 +/- 0.294 | 356.955 +/- 38.283 |
| GRU | 10.038 +/- 0.410 | 13.856 +/- 0.465 | 340.976 +/- 47.797 |

## Interpretation

XGBoost was best on every reported aggregate metric under this fixed FD001 protocol. The neural models were not selectively retuned after seeing the test scores. The RMSE gap between XGBoost and the next model, Transformer, was about 1.21 cycles and larger than either model's observed seed standard deviation.

All 12 final evaluations generated exactly 100 predictions. Saved artifacts include the resolved config, feature list, train-only preprocessing artifact, split metadata, checkpoints or fitted tree model, training logs, test predictions, metrics, and diagnostic plots.

## Scope

These are FD001 results only. They establish a reproducible baseline but do not support conclusions about FD004 or about deep models in general.
