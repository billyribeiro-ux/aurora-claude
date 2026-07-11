"""
AURORA-SWING

Latent Market World Model
=========================

One of the most important components. Rather than predicting a point estimate
("tomorrow = $187.32"), it predicts *possible future market states* from the
current latent state, together with an expected reward and an **uncertainty**
estimate — so the system knows when it is confused.

Inspired by MuZero and DreamerV3.
"""

from __future__ import annotations

import torch
import torch.nn as nn

__all__ = ["LatentDynamicsBlock", "MarketWorldModel"]


class LatentDynamicsBlock(nn.Module):
    """Transformer over the latent sequence that rolls dynamics forward."""

    def __init__(self, latent_dim: int = 512, heads: int = 16) -> None:
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=latent_dim,
            nhead=heads,
            dim_feedforward=2048,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=6)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.transformer(x)


class MarketWorldModel(nn.Module):
    """Predict the next latent state, expected reward and uncertainty."""

    def __init__(self, latent_dim: int = 512) -> None:
        super().__init__()
        self.dynamics = LatentDynamicsBlock(latent_dim)
        self.future_projection = nn.Linear(latent_dim, latent_dim)

        self.reward_head = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.GELU(),
            nn.Linear(256, 1),
        )
        # Softplus keeps the predicted uncertainty strictly positive.
        self.uncertainty_head = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.GELU(),
            nn.Linear(256, 1),
            nn.Softplus(),
        )

    def forward(self, latent_sequence: torch.Tensor) -> dict[str, torch.Tensor]:
        hidden = self.dynamics(latent_sequence)
        future_latent = self.future_projection(hidden[:, -1])
        predicted_reward = self.reward_head(future_latent)
        uncertainty = self.uncertainty_head(future_latent)

        return {
            "future_latent": future_latent,
            "reward": predicted_reward,
            "uncertainty": uncertainty,
        }
