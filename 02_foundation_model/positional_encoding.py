"""
AURORA-SWING

Learnable Market Time Encoding
==============================

Gives the transformer awareness of time. Markets are sequential — a candle from
yesterday is not equivalent to one from six months ago — so we add learnable
temporal position embeddings.
"""

from __future__ import annotations

import torch
import torch.nn as nn

__all__ = ["TemporalEmbedding"]


class TemporalEmbedding(nn.Module):
    """Add a learnable positional embedding to a market token sequence."""

    def __init__(self, max_sequence_length: int = 512, embedding_dim: int = 256) -> None:
        super().__init__()
        self.position_embedding = nn.Parameter(
            torch.zeros(1, max_sequence_length, embedding_dim)
        )
        nn.init.normal_(self.position_embedding, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seq_length = x.size(1)
        return x + self.position_embedding[:, :seq_length, :]
