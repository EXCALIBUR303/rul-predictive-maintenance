# FD004 Experiment Report

## Outcome

The FD004 experimental pipeline completed across XGBoost, LSTM, GRU, and a
small Transformer, each evaluated over seeds `42`, `1337`, and `2026`.
Training and checkpoint selection used grouped train/validation splits only;
the 248-engine official test set was evaluated after all 12 training runs
finished.

| Model | MAE | RMSE | NASA/PHM08 Score |
| --- | ---: | ---: | ---: |
| XGBoost | 11.177 +/- 0.086 | 15.924 +/- 0.150 | 1442.499 +/- 166.958 |
| Transformer | 11.382 +/- 0.822 | 16.387 +/- 1.596 | 1706.756 +/- 679.180 |
| GRU | 10.787 +/- 0.518 | 16.447 +/- 1.009 | 1909.921 +/- 580.499 |
| LSTM | 11.331 +/- 0.936 | 17.963 +/- 2.509 | 4575.788 +/- 4984.534 |

XGBoost is the best model on aggregate RMSE and NASA/PHM08 Score. GRU achieves
the lowest average absolute error but has worse RMSE and asymmetric risk.
There is no support here for claiming that the deeper models outperform
XGBoost on FD004 under this fixed protocol.

## Data And Protocol

- 249 complete FD004 train engines; 248 official truncated test engines.
- RUL target and official-test labels capped at 125 cycles.
- 30-cycle windows, with left-padding and Transformer padding masks for the
  19-cycle minimum test trajectory.
- Train/validation split by engine before preprocessing or windowing.
- Six operating regimes discovered with KMeans fit only on training rows; one
  min-max sensor scaler persisted per regime.
- XGBoost uses summary features from the same 30-cycle context plus the final
  regime label. Neural models use the scaled sensor sequence.

## Important Warning

LSTM seed `2026` scored `10,326.047` on NASA/PHM08. This was independently
recomputed from its persisted predictions, not caused by a metric or artifact
loading bug. It severely underestimated several engines with a capped RUL of
125 cycles; the worst error was `-111.576` cycles. The aggregate table retains
the run and its large variance because excluding it would be selective
reporting.

## Reproduce

```bash
make install-all
make data-fd004
make eda-fd004
make experiment-fd004
```

The raw FD004 source fallback is a SHA-256-verified, pinned public mirror. See
the repository's `docs/EXPERIMENT_CARD_FD004.md` for the exact commit, hashes,
and limitations.
