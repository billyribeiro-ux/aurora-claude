"""
AURORA-SWING

Actor / Critic Networks
=======================

The networks that generate actions and estimate value. The actor consumes the
combined state (latent market state + regime probability + portfolio state +
world-model forecast, ~2048 dims) and outputs a Gaussian over the continuous
action ``[direction, position_size, stop, target, trail]``.
"""

from __future__ import annotations

import torch
import torch.nn as nn

__all__ = ["ActorNetwork", "CriticNetwork"]


class ActorNetwork(nn.Module):
    """Policy network → (mean, std) over the continuous action space."""

    def __init__(self, state_dim: int, action_dim: int = 5) -> None:
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, 1024),
            nn.LayerNorm(1024),
            nn.GELU(),
            nn.Linear(1024, 512),
            nn.GELU(),
        )
        self.mean_head = nn.Linear(512, action_dim)
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(self, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.backbone(state)
        mean = self.mean_head(x)
        std = torch.exp(self.log_std)
        return mean, std


class CriticNetwork(nn.Module):
    """Value network → scalar state value."""

    def __init__(self, state_dim: int) -> None:
        super().__init__()
        self.value = nn.Sequential(
            nn.Linear(state_dim, 1024),
            nn.GELU(),
            nn.Linear(1024, 512),
            nn.GELU(),
            nn.Linear(512, 1),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.value(state)
