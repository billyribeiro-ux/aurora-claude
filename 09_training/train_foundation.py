"""
AURORA-SWING

Foundation Model Training
=========================

Stage 1 of the training lifecycle — pretrain the market foundation model into a
general market-intelligence representation before any trading objective is
introduced.
"""

from __future__ import annotations

from typing import Any, Iterable

import torch

__all__ = ["FoundationTrainingPipeline"]


class FoundationTrainingPipeline:
    """Multi-epoch self-supervised pretraining loop with gradient clipping."""

    def __init__(self, model: torch.nn.Module, optimizer: Any, device: str = "cuda") -> None:
        self.model = model.to(device)
        self.optimizer = optimizer
        self.device = device

    def train(self, dataloader: Iterable[torch.Tensor], epochs: int) -> list[float]:
        history: list[float] = []

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0.0
            batches = 0

            for batch in dataloader:
                batch = batch.to(self.device)
                output = self.model(batch)
                loss = output["loss"]

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()

                epoch_loss += loss.item()
                batches += 1

            avg_loss = epoch_loss / max(batches, 1)
            history.append(avg_loss)
            print(f"Epoch {epoch}: {avg_loss}")

        return history
