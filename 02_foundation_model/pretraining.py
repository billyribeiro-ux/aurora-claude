"""
AURORA-SWING

Foundation Model Pretraining Engine
===================================

Trains the market brain **before** reinforcement learning begins. The model
first learns markets; only afterward does it learn trading. This ordering is
what prevents the RL stage from overfitting the representation.

The wrapped model is expected to return a mapping containing a ``"loss"`` key
(the combined self-supervised objective from ``losses.py``).
"""

from __future__ import annotations

from typing import Any, Iterable

import torch

__all__ = ["FoundationTrainer"]


class FoundationTrainer:
    """Single-epoch training loop with gradient clipping for the foundation model."""

    def __init__(self, model: torch.nn.Module, optimizer: Any, device: str = "cuda") -> None:
        self.model = model.to(device)
        self.optimizer = optimizer
        self.device = device

    def train_epoch(self, loader: Iterable[torch.Tensor]) -> float:
        """Run one epoch and return the mean batch loss."""
        self.model.train()
        total_loss = 0.0
        batches = 0

        for batch in loader:
            x = batch.to(self.device)
            output = self.model(x)
            loss = output["loss"]

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

            total_loss += loss.item()
            batches += 1

        return total_loss / max(batches, 1)
