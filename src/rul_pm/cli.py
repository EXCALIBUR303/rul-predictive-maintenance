from __future__ import annotations

import argparse
import json
from pathlib import Path

from rul_pm.config import load_config
from rul_pm.eda import run_eda
from rul_pm.experiment import evaluate_run, run_experiment, train_one_model


def main() -> None:
    parser = argparse.ArgumentParser(prog="rulpm")
    sub = parser.add_subparsers(dest="command", required=True)
    eda = sub.add_parser("eda", help="Run dataset validation and lightweight EDA summary.")
    eda.add_argument("--config", required=True)
    train = sub.add_parser("train", help="Train one model for one seed.")
    train.add_argument("--config", required=True)
    train.add_argument("--model", required=True, choices=["xgboost", "lstm", "gru", "transformer"])
    train.add_argument("--seed", type=int)
    evaluate = sub.add_parser("evaluate", help="Evaluate a run directory on the official test split.")
    evaluate.add_argument("--run-dir", required=True)
    experiment = sub.add_parser("experiment", help="Train all configured seeds, then evaluate and compare all models.")
    experiment.add_argument("--config", required=True)
    args = parser.parse_args()
    if args.command == "eda":
        print(json.dumps(run_eda(load_config(args.config)), indent=2))
    elif args.command == "train":
        run_dir = train_one_model(load_config(args.config), args.model, seed=args.seed)
        print(f"wrote run: {Path(run_dir)}")
    elif args.command == "evaluate":
        print(json.dumps(evaluate_run(args.run_dir), indent=2))
    elif args.command == "experiment":
        print(json.dumps(run_experiment(load_config(args.config)), indent=2))


if __name__ == "__main__":
    main()
