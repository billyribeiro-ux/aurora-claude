"""
AURORA-SWING

Soft Actor-Critic Exploration Helper
====================================

Secondary exploration optimizer. Entropy regularization encourages the agent to
discover alternative behaviours instead of collapsing onto a single policy.
"""

from __future__ import annotations

import torch

__all__ = ["SACEntropyController"]


class SACEntropyController:
    """Temperature-scaled entropy bonus for exploration."""

    def __init__(self, target_entropy: float = -5) -> None:
        self.target_entropy = target_entropy
        self.alpha = torch.tensor(0.2, requires_grad=True)

    def entropy_bonus(self, log_probability: torch.Tensor) -> torch.Tensor:
        return -self.alpha * log_probability
