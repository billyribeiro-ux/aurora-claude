"""End-to-end deep decision model — the self-learning machine in the driver's seat.

A Transformer sequence encoder that is (1) pretrained self-supervised by masked
reconstruction (no labels), then (2) FINE-TUNED end-to-end on the actual trading
decision (cross-sectional outperformance). This is the modern self-supervised
paradigm — pretrain then fine-tune — with the neural net making the call directly,
not a downstream hand-feature model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

__all__ = ["DeepConfig", "DeepDecoder", "train_supervised", "predict_proba"]


@dataclass
class DeepConfig:
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 2
    ff: int = 128
    dropout: float = 0.1
    epochs: int = 6
    batch_size: int = 512
    lr: float = 5e-4
    weight_decay: float = 1e-5
    seed: int = 7


def _set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


class DeepDecoder(nn.Module):
    """Transformer encoder + prediction head; optionally warm-started from an
    unsupervised MaskedSeqAutoencoder (transfer learning)."""

    def __init__(self, n_features: int, seq_len: int, cfg: DeepConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.input_proj = nn.Linear(n_features, cfg.d_model)
        self.pos = nn.Parameter(torch.zeros(1, seq_len, cfg.d_model))
        nn.init.normal_(self.pos, std=0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=cfg.d_model, nhead=cfg.n_heads, dim_feedforward=cfg.ff,
            dropout=cfg.dropout, batch_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(layer, num_layers=cfg.n_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(cfg.d_model), nn.Linear(cfg.d_model, cfg.d_model), nn.GELU(),
            nn.Dropout(cfg.dropout), nn.Linear(cfg.d_model, 1))

    def load_pretrained(self, ssl_model) -> None:
        """Copy encoder weights from a pretrained masked-autoencoder (same dims)."""
        self.input_proj.load_state_dict(ssl_model.input_proj.state_dict())
        self.encoder.load_state_dict(ssl_model.encoder.state_dict())
        with torch.no_grad():
            self.pos.copy_(ssl_model.pos)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.encoder(self.input_proj(x) + self.pos).mean(dim=1)
        return self.head(h).squeeze(-1)  # logit


def train_supervised(model: DeepDecoder, X_tr: np.ndarray, y_tr: np.ndarray,
                     X_val: np.ndarray, y_val: np.ndarray, cfg: DeepConfig) -> dict:
    """Fine-tune end-to-end on the decision label; early-stop on val AUC-proxy."""
    _set_seed(cfg.seed)
    Xtr = torch.from_numpy(X_tr.astype(np.float32))
    ytr = torch.from_numpy(y_tr.astype(np.float32))
    Xva = torch.from_numpy(X_val.astype(np.float32))
    yva = torch.from_numpy(y_val.astype(np.float32))
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    lossf = nn.BCEWithLogitsLoss()
    gen = torch.Generator().manual_seed(cfg.seed)
    n = Xtr.shape[0]
    hist = {"train_loss": [], "val_loss": []}
    best_val, best_state = float("inf"), None
    for epoch in range(cfg.epochs):
        model.train()
        order = torch.randperm(n, generator=gen)
        tot, nb = 0.0, 0
        for s in range(0, n, cfg.batch_size):
            idx = order[s:s + cfg.batch_size]
            opt.zero_grad()
            loss = lossf(model(Xtr[idx]), ytr[idx])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item(); nb += 1
        model.eval()
        with torch.no_grad():
            vloss = float(lossf(model(Xva), yva))
        hist["train_loss"].append(tot / max(nb, 1))
        hist["val_loss"].append(vloss)
        if vloss < best_val:
            best_val = vloss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        print(f"  [deep] epoch {epoch+1:02d}/{cfg.epochs} train {hist['train_loss'][-1]:.4f} val {vloss:.4f}")
    if best_state is not None:
        model.load_state_dict(best_state)  # restore best-val weights
    return hist


def predict_proba(model: DeepDecoder, X: np.ndarray, batch_size: int = 1024) -> np.ndarray:
    model.eval()
    Xt = torch.from_numpy(X.astype(np.float32))
    out = []
    with torch.no_grad():
        for s in range(0, Xt.shape[0], batch_size):
            out.append(torch.sigmoid(model(Xt[s:s + batch_size])).cpu().numpy())
    return np.concatenate(out)
