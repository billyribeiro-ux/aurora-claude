"""Self-supervised market-sequence foundation encoder (compact, CPU-trainable).

A BERT-style **masked-reconstruction** objective: random timesteps of a feature
sequence are masked, a small Transformer encoder must reconstruct the original
feature values at the masked positions. No labels are used — the representation
is learned purely from the structure of market sequences.

After pretraining, the encoder is FROZEN and its mean-pooled hidden state is used
as a fixed representation for a linear probe (see ``models.py``). Beating the
hand-feature baseline with only a *linear* probe on this representation is the
E2 gate from ``00_architecture/evolution_roadmap.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

__all__ = ["EncoderConfig", "MaskedSeqAutoencoder", "pretrain_encoder", "encode"]


@dataclass
class EncoderConfig:
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 2
    ff: int = 128
    dropout: float = 0.1
    mask_ratio: float = 0.15
    epochs: int = 15
    batch_size: int = 256
    lr: float = 1e-3
    val_frac: float = 0.1
    seed: int = 7


def _set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


class MaskedSeqAutoencoder(nn.Module):
    """Transformer encoder + linear decoder trained by masked reconstruction."""

    def __init__(self, n_features: int, seq_len: int, cfg: EncoderConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.n_features = n_features
        self.seq_len = seq_len
        self.input_proj = nn.Linear(n_features, cfg.d_model)
        self.pos = nn.Parameter(torch.zeros(1, seq_len, cfg.d_model))
        nn.init.normal_(self.pos, std=0.02)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, cfg.d_model))
        nn.init.normal_(self.mask_token, std=0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=cfg.d_model, nhead=cfg.n_heads, dim_feedforward=cfg.ff,
            dropout=cfg.dropout, batch_first=True, activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=cfg.n_layers)
        self.decoder = nn.Linear(cfg.d_model, n_features)

    def encode_hidden(self, x: torch.Tensor) -> torch.Tensor:
        """Return per-position hidden states for an UNMASKED input (B, L, d)."""
        h = self.input_proj(x) + self.pos
        return self.encoder(h)

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """Reconstruct features; ``mask`` (B, L) marks masked (hidden) timesteps."""
        h = self.input_proj(x) + self.pos
        m = mask.unsqueeze(-1)  # (B, L, 1)
        h = torch.where(m, self.mask_token.expand_as(h), h)
        h = self.encoder(h)
        return self.decoder(h)

    def representation(self, x: torch.Tensor) -> torch.Tensor:
        """Mean-pooled frozen representation of a full sequence (B, d_model)."""
        return self.encode_hidden(x).mean(dim=1)


def pretrain_encoder(
    X_seq_train: np.ndarray, cfg: EncoderConfig | None = None
) -> tuple[MaskedSeqAutoencoder, dict]:
    """Self-supervised pretraining on TRAIN sequences only. Returns (model, history)."""
    cfg = cfg or EncoderConfig()
    _set_seed(cfg.seed)
    n, seq_len, n_feat = X_seq_train.shape

    X = torch.from_numpy(X_seq_train.astype(np.float32))
    # Deterministic val split off the tail of the (chronologically ordered) train set.
    n_val = max(1, int(n * cfg.val_frac))
    perm = torch.randperm(n, generator=torch.Generator().manual_seed(cfg.seed))
    val_idx, tr_idx = perm[:n_val], perm[n_val:]
    X_tr, X_val = X[tr_idx], X[val_idx]

    model = MaskedSeqAutoencoder(n_feat, seq_len, cfg)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    gen = torch.Generator().manual_seed(cfg.seed)

    def masked_loss(batch: torch.Tensor) -> torch.Tensor:
        mask = torch.rand(batch.shape[:2], generator=gen) < cfg.mask_ratio
        if not mask.any():
            mask[:, 0] = True
        recon = model(batch, mask)
        diff = (recon - batch) ** 2
        return (diff * mask.unsqueeze(-1)).sum() / (mask.sum() * batch.shape[-1] + 1e-8)

    history = {"train_loss": [], "val_loss": []}
    n_tr = X_tr.shape[0]
    for epoch in range(cfg.epochs):
        model.train()
        order = torch.randperm(n_tr, generator=gen)
        tot, nb = 0.0, 0
        for s in range(0, n_tr, cfg.batch_size):
            b = X_tr[order[s : s + cfg.batch_size]]
            opt.zero_grad()
            loss = masked_loss(b)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item()
            nb += 1
        model.eval()
        with torch.no_grad():
            vloss = float(masked_loss(X_val))
        history["train_loss"].append(tot / max(nb, 1))
        history["val_loss"].append(vloss)
        print(f"  [encoder] epoch {epoch+1:02d}/{cfg.epochs}  "
              f"train {history['train_loss'][-1]:.4f}  val {vloss:.4f}")
    return model, history


def encode(model: MaskedSeqAutoencoder, X_seq: np.ndarray, batch_size: int = 512) -> np.ndarray:
    """Extract the frozen mean-pooled representation for every sequence."""
    model.eval()
    X = torch.from_numpy(X_seq.astype(np.float32))
    out = []
    with torch.no_grad():
        for s in range(0, X.shape[0], batch_size):
            out.append(model.representation(X[s : s + batch_size]).cpu().numpy())
    return np.concatenate(out).astype(np.float32)
