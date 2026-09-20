from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Any

import numpy as np

from rul_pm.config import config_hash
from rul_pm.evaluation.metrics import regression_metrics
from rul_pm.models.torch_models import build_torch_model, count_parameters
from rul_pm.training.seed import seed_worker, set_seed


def train_torch_model(
    model_name: str,
    train_arrays: Any,
    val_arrays: Any,
    config: dict[str, Any],
    run_dir: str | Path,
    seed: int,
) -> dict[str, Any]:
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    set_seed(seed)
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    data_cfg = config.get("data", {})
    train_cfg = config.get("training", {})
    rul_cap = float(data_cfg.get("rul_cap", 125.0))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_torch_model(model_name, input_size=train_arrays.x.shape[-1], config=config).to(device)
    loss_name = str(train_cfg.get("loss", "huber")).lower()
    criterion = torch.nn.SmoothL1Loss() if loss_name == "huber" else torch.nn.MSELoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(train_cfg.get("learning_rate", 1.0e-3)),
        weight_decay=float(train_cfg.get("weight_decay", 1.0e-4)),
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=5)
    train_ds = TensorDataset(
        torch.from_numpy(train_arrays.x),
        torch.from_numpy(train_arrays.mask),
        torch.from_numpy(train_arrays.y.astype(np.float32)),
    )
    val_ds = TensorDataset(
        torch.from_numpy(val_arrays.x),
        torch.from_numpy(val_arrays.mask),
        torch.from_numpy(val_arrays.y.astype(np.float32)),
    )
    generator = torch.Generator().manual_seed(seed)
    use_cuda = device.type == "cuda"
    train_loader = DataLoader(
        train_ds,
        batch_size=int(train_cfg.get("batch_size", 128)),
        shuffle=True,
        num_workers=int(train_cfg.get("num_workers", 0)),
        pin_memory=use_cuda,
        worker_init_fn=seed_worker,
        generator=generator,
    )
    val_loader = DataLoader(val_ds, batch_size=int(train_cfg.get("batch_size", 128)), shuffle=False, pin_memory=use_cuda)
    best_rmse = float("inf")
    best_epoch = -1
    bad_epochs = 0
    max_epochs = int(train_cfg.get("max_epochs", 100))
    patience = int(train_cfg.get("patience", 12))
    grad_clip = float(train_cfg.get("gradient_clip_norm", 1.0))
    log_path = run_path / "training_log.csv"
    start = time.time()
    with log_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["epoch", "train_loss", "val_mae", "val_rmse", "val_nasa_score"])
        writer.writeheader()
        for epoch in range(1, max_epochs + 1):
            model.train()
            train_losses = []
            for xb, mb, yb in train_loader:
                xb = xb.to(device, non_blocking=use_cuda)
                mb = mb.to(device, non_blocking=use_cuda)
                yb = yb.to(device, non_blocking=use_cuda)
                optimizer.zero_grad(set_to_none=True)
                pred = model(xb, mb)
                loss = criterion(pred, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                optimizer.step()
                train_losses.append(float(loss.detach().cpu()))
            val_pred, val_true = _predict_loader(model, val_loader, device, use_cuda)
            metrics = regression_metrics(val_true, val_pred, rul_cap=rul_cap)
            scheduler.step(metrics.rmse)
            writer.writerow(
                {
                    "epoch": epoch,
                    "train_loss": float(np.mean(train_losses)),
                    "val_mae": metrics.mae,
                    "val_rmse": metrics.rmse,
                    "val_nasa_score": metrics.nasa_score,
                }
            )
            checkpoint = {
                "model_name": model_name,
                "state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "epoch": epoch,
                "input_size": train_arrays.x.shape[-1],
                "config": config,
                "config_hash": config_hash(config),
                "seed": seed,
                "val_metrics": metrics.to_dict(),
                "parameter_count": count_parameters(model),
            }
            torch.save(checkpoint, run_path / "last.pt")
            if metrics.rmse < best_rmse:
                best_rmse = metrics.rmse
                best_epoch = epoch
                bad_epochs = 0
                torch.save(checkpoint, run_path / "best.pt")
            else:
                bad_epochs += 1
                if bad_epochs >= patience:
                    break
    return {
        "model": model_name,
        "seed": seed,
        "best_epoch": best_epoch,
        "best_val_rmse": best_rmse,
        "parameter_count": count_parameters(model),
        "train_time_seconds": time.time() - start,
        "artifact": str(run_path / "best.pt"),
        "last_artifact": str(run_path / "last.pt"),
    }


def predict_torch_checkpoint(checkpoint_path: str | Path, arrays: Any) -> np.ndarray:
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model = build_torch_model(checkpoint["model_name"], checkpoint["input_size"], checkpoint["config"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    ds = TensorDataset(torch.from_numpy(arrays.x), torch.from_numpy(arrays.mask), torch.zeros(len(arrays.x)))
    loader = DataLoader(ds, batch_size=256, shuffle=False)
    pred, _ = _predict_loader(model, loader, torch.device("cpu"), False)
    return pred


def _predict_loader(model: Any, loader: Any, device: Any, use_cuda: bool) -> tuple[np.ndarray, np.ndarray]:
    import torch

    preds = []
    targets = []
    model.eval()
    with torch.no_grad():
        for xb, mb, yb in loader:
            xb = xb.to(device, non_blocking=use_cuda)
            mb = mb.to(device, non_blocking=use_cuda)
            pred = model(xb, mb).detach().cpu().numpy()
            preds.append(pred)
            targets.append(yb.detach().cpu().numpy())
    return np.concatenate(preds), np.concatenate(targets)
