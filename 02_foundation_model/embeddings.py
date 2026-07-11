"""
AURORA-SWING

Market Feature Embedding Layer
==============================

Converts numerical market observations into transformer token representations.
A transformer cannot consume raw values like ``RSI = 64.3`` or ``Volume =
12,500,000`` directly — it needs dense, learned embeddings.

Flow: linear projection → layer norm → GELU → dropout.
"""

from __future__ import annotations

import torch
import torch.nn as nn

__all__ = ["MarketEmbedding"]


class MarketEmbedding(nn.Module):
    """Project raw market features into a normalized embedding space."""

    def __init__(
        self,
        input_features: int,
        embedding_dim: int = 256,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.projection = nn.Linear(input_features, embedding_dim)
        self.norm = nn.LayerNorm(embedding_dim)
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """``[batch, sequence, features]`` → ``[batch, sequence, embedding_dim]``."""
        x = self.projection(x)
        x = self.norm(x)
        x = self.activation(x)
        x = self.dropout(x)
        return x
