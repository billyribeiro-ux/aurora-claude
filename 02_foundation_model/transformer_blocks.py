"""
AURORA-SWING

Transformer Blocks for Market Representation Learning
=====================================================

Core attention mechanism with enhancements over the vanilla Transformer:
pre-normalization, a GELU feed-forward network, residual pathways and dropout
stabilization.
"""

from __future__ import annotations

import torch
import torch.nn as nn

__all__ = ["MarketTransformerBlock"]


class MarketTransformerBlock(nn.Module):
    """A pre-norm multi-head self-attention + feed-forward residual block."""

    def __init__(
        self,
        embedding_dim: int = 256,
        heads: int = 8,
        ff_dim: int = 1024,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(embedding_dim)
        self.attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=heads,
            dropout=dropout,
            batch_first=True,
        )
        self.norm2 = nn.LayerNorm(embedding_dim)
        self.feed_forward = nn.Sequential(
            nn.Linear(embedding_dim, ff_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, embedding_dim),
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Pre-norm self-attention with a residual connection.
        residual = x
        x_norm = self.norm1(x)
        attention_output, _ = self.attention(x_norm, x_norm, x_norm)
        x = residual + self.dropout(attention_output)

        # Pre-norm feed-forward with a residual connection.
        residual = x
        x = residual + self.dropout(self.feed_forward(self.norm2(x)))
        return x
