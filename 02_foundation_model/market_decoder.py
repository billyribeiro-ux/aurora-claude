"""
AURORA-SWING

Market Reconstruction Decoder
=============================

The decoder forces the encoder to actually understand market structure. Without
a reconstruction objective the encoder can learn meaningless shortcuts. Given a
latent state it reconstructs the market feature vector:

    X̂_t = Decoder(z_t)

covering price structure, volatility, momentum, volume behaviour and market
context. Used for masked market modeling.
"""

from __future__ import annotations

import torch
import torch.nn as nn

__all__ = ["MarketDecoder"]


class MarketDecoder(nn.Module):
    """Reconstruct the market feature vector from a latent state."""

    def __init__(self, latent_dim: int = 512, output_features: int = 96) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(latent_dim, 1024),
            nn.GELU(),
            nn.LayerNorm(1024),
            nn.Linear(1024, 512),
            nn.GELU(),
            nn.Linear(512, output_features),
        )

    def forward(self, latent: torch.Tensor) -> torch.Tensor:
        return self.network(latent)
