from __future__ import annotations

import pandas as pd

from rul_pm.evaluation.plots import save_evaluation_plots
from rul_pm.experiment import _aggregate_comparison


def test_comparison_aggregates_mean_and_sample_standard_deviation():
    per_seed = pd.DataFrame(
        [
            {"model": "xgboost", "seed": 1, "mae": 4.0, "rmse": 5.0, "nasa_score": 6.0},
            {"model": "xgboost", "seed": 2, "mae": 6.0, "rmse": 7.0, "nasa_score": 8.0},
            {"model": "gru", "seed": 1, "mae": 1.0, "rmse": 2.0, "nasa_score": 3.0},
            {"model": "gru", "seed": 2, "mae": 3.0, "rmse": 4.0, "nasa_score": 5.0},
        ]
    )
    result = _aggregate_comparison(per_seed)
    assert result["model"].tolist() == ["gru", "xgboost"]
    assert result.loc[0, "rmse_mean"] == 3.0
    assert result.loc[1, "mae_std"] > 0.0


def test_evaluation_plots_are_saved(tmp_path):
    scored = pd.DataFrame({"RUL": [1.0, 2.0, 3.0], "prediction": [1.5, 1.5, 2.5], "error": [0.5, -0.5, -0.5]})
    save_evaluation_plots(scored, tmp_path)
    assert (tmp_path / "actual_vs_predicted.png").is_file()
    assert (tmp_path / "residual_distribution.png").is_file()
    assert (tmp_path / "residuals_by_true_rul.png").is_file()
