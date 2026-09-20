from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_evaluation_plots(scored: pd.DataFrame, output_dir: str | Path) -> None:
    """Save test-set diagnostic plots for one final model evaluation."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    true = scored["RUL"].to_numpy(dtype=float)
    prediction = scored["prediction"].to_numpy(dtype=float)
    error = scored["error"].to_numpy(dtype=float)
    limit = max(float(np.max(true)), float(np.max(prediction)), 1.0)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(true, prediction, alpha=0.7, edgecolors="none")
    ax.plot([0, limit], [0, limit], color="black", linewidth=1, linestyle="--")
    ax.set(xlabel="True capped RUL", ylabel="Predicted RUL", title="FD001: actual vs. predicted RUL")
    fig.tight_layout()
    fig.savefig(target / "actual_vs_predicted.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(error, bins=min(20, max(5, len(error) // 5)), color="#2563eb", edgecolor="white")
    ax.axvline(0.0, color="black", linewidth=1, linestyle="--")
    ax.set(xlabel="Prediction error (predicted - true)", ylabel="Test engines", title="FD001 residual distribution")
    fig.tight_layout()
    fig.savefig(target / "residual_distribution.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(true, error, alpha=0.7, edgecolors="none")
    ax.axhline(0.0, color="black", linewidth=1, linestyle="--")
    ax.set(xlabel="True capped RUL", ylabel="Prediction error", title="FD001 residuals by true RUL")
    fig.tight_layout()
    fig.savefig(target / "residuals_by_true_rul.png", dpi=160)
    plt.close(fig)
