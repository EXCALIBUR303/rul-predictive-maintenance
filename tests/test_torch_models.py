from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

import numpy as np

from rul_pm.data.windows import WindowArrays
from rul_pm.models.torch_models import build_torch_model
from rul_pm.training.torch_trainer import predict_torch_checkpoint, train_torch_model


def _config() -> dict:
    return {
        "data": {"rul_cap": 10},
        "training": {
            "batch_size": 2,
            "max_epochs": 2,
            "patience": 2,
            "learning_rate": 1.0e-3,
            "weight_decay": 1.0e-4,
            "gradient_clip_norm": 1.0,
            "loss": "huber",
            "num_workers": 0,
        },
        "neural": {"hidden_size": 8, "num_layers": 2, "dropout": 0.1, "d_model": 8, "nhead": 2, "dim_feedforward": 16},
    }


def _arrays() -> WindowArrays:
    x = np.arange(32, dtype=np.float32).reshape(4, 4, 2) / 32.0
    return WindowArrays(
        x=x,
        y=np.array([4.0, 3.0, 2.0, 1.0], dtype=np.float32),
        mask=np.ones((4, 4), dtype=bool),
        unit_numbers=np.array([1, 2, 3, 4]),
        end_cycles=np.array([4, 4, 4, 4]),
    )


@pytest.mark.parametrize("model_name", ["lstm", "gru", "transformer"])
def test_neural_models_accept_batch_time_feature_inputs(model_name):
    model = build_torch_model(model_name, input_size=2, config=_config()).eval()
    with torch.no_grad():
        prediction = model(torch.zeros((3, 4, 2)), torch.ones((3, 4), dtype=torch.bool))
    assert prediction.shape == (3,)


def test_transformer_mask_excludes_left_padding_from_attention_and_pooling():
    torch.manual_seed(7)
    model = build_torch_model("transformer", input_size=2, config=_config()).eval()
    mask = torch.tensor([[False, False, True, True]])
    valid_cycles = torch.tensor([[[0.25, 0.5], [0.75, 1.0]]])
    padded_a = torch.cat([torch.zeros((1, 2, 2)), valid_cycles], dim=1)
    padded_b = torch.cat([torch.full((1, 2, 2), 999.0), valid_cycles], dim=1)
    with torch.no_grad():
        first = model(padded_a, mask)
        second = model(padded_b, mask)
    torch.testing.assert_close(first, second)


def test_neural_training_writes_restorable_best_and_last_checkpoints(tmp_path):
    arrays = _arrays()
    summary = train_torch_model("lstm", arrays, arrays, _config(), tmp_path, seed=9)
    best = torch.load(tmp_path / "best.pt", map_location="cpu", weights_only=False)
    last = torch.load(tmp_path / "last.pt", map_location="cpu", weights_only=False)
    required = {"model_name", "state_dict", "optimizer_state_dict", "epoch", "config", "config_hash", "seed", "val_metrics"}
    assert required.issubset(best)
    assert required.issubset(last)
    assert summary["last_artifact"].endswith("last.pt")
    assert predict_torch_checkpoint(tmp_path / "best.pt", arrays).shape == (4,)
