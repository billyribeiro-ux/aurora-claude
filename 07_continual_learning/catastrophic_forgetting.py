"""
AURORA-SWING

Elastic Weight Consolidation
============================

Prevents the AI from forgetting old market behaviour when it adapts to new
conditions. Important parameters are anchored to their previous values; new
learning is allowed *around* them via a quadratic penalty.
"""

from __future__ import annotations

import torch

__all__ = ["EWC"]


class EWC:
    """Anchor model parameters to protect prior knowledge during adaptation."""

    def __init__(self, model: torch.nn.Module, importance: float = 0.4) -> None:
        self.model = model
        self.importance = importance
        self.parameters = {
            name: param.clone().detach()
            for name, param in model.named_parameters()
        }

    def penalty(self) -> torch.Tensor:
        loss: torch.Tensor = torch.zeros(())
        for name, param in self.model.named_parameters():
            old = self.parameters[name]
            loss = loss + torch.sum((param - old) ** 2)
        return self.importance * loss
