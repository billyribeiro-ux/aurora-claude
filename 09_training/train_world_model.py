"""
AURORA-SWING

World Model Training Pipeline
============================

Stage 2 — train the simulator of future market behaviour. Given the current
latent state the world model predicts future latent states and the associated
reward.
"""

from __future__ import annotations

from typing import Any, Iterable

import torch
import torch.nn.functional as F

__all__ = ["WorldModelTrainer"]


class WorldModelTrainer:
    """Single-epoch trainer for the latent world model."""

    def __init__(self, model: torch.nn.Module, optimizer: Any, device: str = "cuda") -> None:
        self.model = model
        self.optimizer = optimizer
        self.device = device

    def train_epoch(self, loader: Iterable[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]) -> float:
        self.model.train()
        total = 0.0
        batches = 0

        for latent, future, reward in loader:
            latent = latent.to(self.device)
            future = future.to(self.device)
            reward = reward.to(self.device)

            output = self.model(latent)

            latent_loss = F.mse_loss(output["future_latent"], future)
            reward_loss = F.mse_loss(output["reward"], reward)
            loss = latent_loss + 0.5 * reward_loss

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total += loss.item()
            batches += 1

        return total / max(batches, 1)
