from __future__ import annotations

import math
import sys
from typing import Any

try:
    import torch
    from torch import nn
except Exception as exc:  # pragma: no cover - exercised when optional extra is absent
    torch = None
    nn = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _require_torch() -> None:
    if torch is None or nn is None:
        raise ImportError("Install the 'models' extra to use neural models: uv pip install -e '.[models]'") from _IMPORT_ERROR
    # PyTorch 2.14 can segfault in TransformerEncoder on macOS CPU with its
    # default OpenMP thread count. C-MAPSS models are small, so one CPU thread
    # is the reliable default on that platform.
    if sys.platform == "darwin" and torch.get_num_threads() > 1:
        torch.set_num_threads(1)


class RecurrentRegressor(nn.Module if nn else object):
    def __init__(
        self,
        input_size: int,
        cell: str = "lstm",
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        _require_torch()
        super().__init__()
        rnn_cls = nn.LSTM if cell == "lstm" else nn.GRU
        recurrent_dropout = dropout if num_layers > 1 else 0.0
        self.rnn = rnn_cls(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=recurrent_dropout,
            batch_first=True,
        )
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x: "torch.Tensor", mask: "torch.Tensor | None" = None) -> "torch.Tensor":
        out, _ = self.rnn(x)
        last = out[:, -1, :]
        return self.head(last).squeeze(-1)


class PositionalEncoding(nn.Module if nn else object):
    def __init__(self, d_model: int, max_len: int = 512) -> None:
        _require_torch()
        super().__init__()
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return x + self.pe[:, : x.size(1)]


class TransformerRegressor(nn.Module if nn else object):
    def __init__(
        self,
        input_size: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
    ) -> None:
        _require_torch()
        super().__init__()
        self.projection = nn.Linear(input_size, d_model)
        self.position = PositionalEncoding(d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=num_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
        )

    def forward(self, x: "torch.Tensor", mask: "torch.Tensor | None" = None) -> "torch.Tensor":
        projected = self.position(self.projection(x))
        key_padding_mask = None if mask is None else ~mask.bool()
        encoded = self.encoder(projected, src_key_padding_mask=key_padding_mask)
        if mask is None:
            pooled = encoded.mean(dim=1)
        else:
            weights = mask.float().unsqueeze(-1)
            pooled = (encoded * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1.0)
        return self.head(pooled).squeeze(-1)


def build_torch_model(model_name: str, input_size: int, config: dict[str, Any]) -> Any:
    _require_torch()
    neural = config.get("neural", {})
    name = model_name.lower()
    if name in {"lstm", "gru"}:
        return RecurrentRegressor(
            input_size=input_size,
            cell=name,
            hidden_size=int(neural.get("hidden_size", 64)),
            num_layers=int(neural.get("num_layers", 2)),
            dropout=float(neural.get("dropout", 0.2)),
        )
    if name == "transformer":
        return TransformerRegressor(
            input_size=input_size,
            d_model=int(neural.get("d_model", 64)),
            nhead=int(neural.get("nhead", 4)),
            num_layers=int(neural.get("num_layers", 2)),
            dim_feedforward=int(neural.get("dim_feedforward", 128)),
            dropout=float(neural.get("dropout", 0.1)),
        )
    raise ValueError(f"Unsupported neural model: {model_name}")


def count_parameters(model: Any) -> int:
    _require_torch()
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))
