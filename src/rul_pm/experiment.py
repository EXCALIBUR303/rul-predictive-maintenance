from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rul_pm.config import config_hash, save_config
from rul_pm.data.io import load_subset, load_training_data
from rul_pm.data.preprocess import CmapssPreprocessor
from rul_pm.data.split import filter_units, grouped_train_val_units
from rul_pm.data.targets import add_train_rul, capped_test_last_rul
from rul_pm.data.windows import build_sequence_windows, build_xgb_window_features
from rul_pm.evaluation.metrics import regression_metrics
from rul_pm.evaluation.plots import save_evaluation_plots
from rul_pm.training.seed import set_seed
from rul_pm.training.torch_trainer import predict_torch_checkpoint, train_torch_model
from rul_pm.training.xgb_trainer import train_xgboost


def prepare_splits(config: dict[str, Any], seed: int) -> dict[str, Any]:
    subset = config["experiment"]["subset"].upper()
    train_raw = load_training_data(config["experiment"]["data_dir"], subset)
    train_labeled = add_train_rul(train_raw, rul_cap=float(config["data"].get("rul_cap", 125.0)))
    train_units, val_units = grouped_train_val_units(
        train_labeled,
        validation_fraction=float(config["data"].get("validation_fraction", 0.2)),
        seed=seed,
    )
    train_df = filter_units(train_labeled, train_units)
    val_df = filter_units(train_labeled, val_units)
    preprocessor = CmapssPreprocessor(
        scaler=str(config["data"].get("scaler", "minmax")),
        n_regimes=int(config["data"].get("n_regimes", 1)),
        low_variance_threshold=float(config["data"].get("low_variance_threshold", 1.0e-8)),
        low_unique_threshold=int(config["data"].get("low_unique_threshold", 2)),
        random_state=seed,
    )
    train_processed = preprocessor.fit_transform(train_df)
    val_processed = preprocessor.transform(val_df)
    return {
        "subset": subset,
        "train": train_processed,
        "val": val_processed,
        "preprocessor": preprocessor,
        "train_units": train_units.tolist(),
        "val_units": val_units.tolist(),
    }


def train_one_model(config: dict[str, Any], model_name: str, seed: int | None = None) -> Path:
    seed = int(seed if seed is not None else config["experiment"].get("seeds", [42])[0])
    set_seed(seed)
    model_name = model_name.lower()
    subset = config["experiment"]["subset"].upper()
    run_root = Path(config["experiment"].get("output_dir", "runs")) / subset / model_name / f"seed_{seed}"
    run_root.mkdir(parents=True, exist_ok=True)
    save_config(config, run_root / "config.yaml")
    splits = prepare_splits(config, seed=seed)
    preprocessor = splits["preprocessor"]
    preprocessor.save(run_root / "preprocessor.joblib")
    (run_root / "feature_list.json").write_text(json.dumps(preprocessor.feature_columns, indent=2), encoding="utf-8")
    metadata = {
        "subset": subset,
        "model": model_name,
        "seed": seed,
        "config_hash": config_hash(config),
        "train_units": splits["train_units"],
        "val_units": splits["val_units"],
        "preprocessor": preprocessor.metadata(),
    }
    (run_root / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    window_length = int(config["data"].get("window_length", 30))
    if model_name == "xgboost":
        train_x, train_y, feature_names, _ = build_xgb_window_features(
            splits["train"], preprocessor.feature_columns, window_length, target_column="RUL", last_only=False
        )
        val_x, val_y, _, _ = build_xgb_window_features(
            splits["val"], preprocessor.feature_columns, window_length, target_column="RUL", last_only=False
        )
        (run_root / "xgb_feature_names.json").write_text(json.dumps(feature_names, indent=2), encoding="utf-8")
        train_xgboost(train_x, train_y, val_x, val_y, config, run_root, seed)
    elif model_name in {"lstm", "gru", "transformer"}:
        train_arrays = build_sequence_windows(splits["train"], preprocessor.feature_columns, window_length, target_column="RUL")
        val_arrays = build_sequence_windows(splits["val"], preprocessor.feature_columns, window_length, target_column="RUL")
        summary = train_torch_model(model_name, train_arrays, val_arrays, config, run_root, seed)
        (run_root / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    latest = run_root.parent / "latest"
    if latest.exists() or latest.is_symlink():
        if latest.is_symlink() or latest.is_file():
            latest.unlink()
        else:
            shutil.rmtree(latest)
    shutil.copytree(run_root, latest)
    return run_root


def evaluate_run(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    config = _load_run_config(run_path)
    metadata = json.loads((run_path / "metadata.json").read_text(encoding="utf-8"))
    subset = config["experiment"]["subset"].upper()
    loaded = load_subset(config["experiment"]["data_dir"], subset)
    preprocessor = CmapssPreprocessor.load(run_path / "preprocessor.joblib")
    test_processed = preprocessor.transform(loaded.test)
    test_labels = capped_test_last_rul(loaded.test, loaded.test_rul, rul_cap=float(config["data"].get("rul_cap", 125.0)))
    window_length = int(config["data"].get("window_length", 30))
    model_name = metadata["model"]
    if model_name == "xgboost":
        from rul_pm.models.xgb_model import XGBoostRulModel

        x_test, _, _, meta = build_xgb_window_features(
            test_processed, preprocessor.feature_columns, window_length, target_column=None, last_only=True
        )
        model = XGBoostRulModel.load(run_path / "model.joblib")
        pred = model.predict(x_test)
    else:
        arrays = build_sequence_windows(
            test_processed, preprocessor.feature_columns, window_length, target_column=None, last_only=True
        )
        pred = predict_torch_checkpoint(run_path / "best.pt", arrays)
        meta = pd.DataFrame({"unit_number": arrays.unit_numbers, "time_in_cycles": arrays.end_cycles})
    scored = meta.merge(test_labels, on="unit_number", how="left")
    scored["prediction"] = np.clip(pred, 0.0, float(config["data"].get("rul_cap", 125.0)))
    metrics = regression_metrics(scored["RUL"].to_numpy(), scored["prediction"].to_numpy(), rul_cap=float(config["data"].get("rul_cap", 125.0)))
    scored["error"] = scored["prediction"] - scored["RUL"]
    scored["absolute_error"] = scored["error"].abs()
    scored.to_csv(run_path / "test_predictions.csv", index=False)
    save_evaluation_plots(scored, run_path / "plots")
    result = {
        "subset": subset,
        "model": model_name,
        "seed": metadata["seed"],
        "test_metrics": metrics.to_dict(),
        "n_test_engines": int(len(scored)),
    }
    (run_path / "test_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_experiment(config: dict[str, Any], model_names: tuple[str, ...] = ("xgboost", "lstm", "gru", "transformer")) -> dict[str, Any]:
    """Train every configured seed before touching the official test split."""
    seeds = tuple(int(seed) for seed in config["experiment"].get("seeds", [42]))
    if len(seeds) < 3:
        raise ValueError("The final comparison requires at least three evaluation seeds.")
    subset = config["experiment"]["subset"].upper()
    results_dir = Path("results") / subset
    results_dir.mkdir(parents=True, exist_ok=True)
    training_runs: list[dict[str, Any]] = []
    for model_name in model_names:
        for seed in seeds:
            training_runs.append({"model": model_name, "seed": seed, "run_dir": str(train_one_model(config, model_name, seed))})
    (results_dir / "training_runs.json").write_text(json.dumps(training_runs, indent=2), encoding="utf-8")

    # The official test files are read only after all training and selection are complete.
    evaluations = [evaluate_run(record["run_dir"]) for record in training_runs]
    records = []
    for result in evaluations:
        metrics = result["test_metrics"]
        records.append({"model": result["model"], "seed": result["seed"], **metrics, "n_test_engines": result["n_test_engines"]})
    per_seed = pd.DataFrame(records).sort_values(["model", "seed"])
    per_seed.to_csv(results_dir / "per_seed_metrics.csv", index=False)
    comparison = _aggregate_comparison(per_seed)
    comparison.to_csv(results_dir / "model_comparison.csv", index=False)
    payload = {
        "subset": subset,
        "seeds": list(seeds),
        "per_seed_metrics": records,
        "comparison": comparison.to_dict(orient="records"),
    }
    (results_dir / "model_comparison.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _save_comparison_plot(comparison, results_dir / "model_comparison.png")
    return payload


def _aggregate_comparison(per_seed: pd.DataFrame) -> pd.DataFrame:
    metrics = ["mae", "rmse", "nasa_score"]
    grouped = per_seed.groupby("model", sort=False)[metrics].agg(["mean", "std"]).reset_index()
    grouped.columns = ["model", *[f"{metric}_{stat}" for metric in metrics for stat in ("mean", "std")]]
    return grouped.sort_values("rmse_mean").reset_index(drop=True)


def _save_comparison_plot(comparison: pd.DataFrame, path: str | Path) -> None:
    metrics = [("mae", "MAE"), ("rmse", "RMSE"), ("nasa_score", "NASA/PHM08 Score")]
    fig, axes = plt.subplots(1, len(metrics), figsize=(13, 4))
    for ax, (key, label) in zip(axes, metrics, strict=True):
        ax.bar(comparison["model"], comparison[f"{key}_mean"], yerr=comparison[f"{key}_std"].fillna(0.0), capsize=4, color="#2563eb")
        ax.set_ylabel(label)
        ax.set_title(label + " across seeds")
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _load_run_config(run_path: Path) -> dict[str, Any]:
    from rul_pm.config import load_config

    return load_config(run_path / "config.yaml")
