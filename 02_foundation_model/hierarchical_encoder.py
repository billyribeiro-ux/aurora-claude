"""
AURORA-SWING

Hierarchical Market Transformer Encoder
=======================================

The main perception network. A local transformer learns candles, swings and
momentum; temporal compression lifts the representation; a global transformer
learns regimes, cycles and macro structure. The output is the latent market
state of shape ``(batch, sequence, latent_dim)``.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .embeddings import MarketEmbedding
from .positional_encoding import TemporalEmbedding
from .transformer_blocks import MarketTransformerBlock

__all__ = ["HierarchicalMarketEncoder"]


class HierarchicalMarketEncoder(nn.Module):
    """Two-stage (local → global) transformer encoder for market sequences."""

    def __init__(self, input_features: int, latent_dim: int = 512) -> None:
        super().__init__()

        self.embedding = MarketEmbedding(input_features, 256)
        self.position = TemporalEmbedding(512, 256)

        # Local encoder: short-term swing structure.
        self.local_layers = nn.ModuleList(
            [MarketTransformerBlock(256, heads=8, ff_dim=1024) for _ in range(6)]
        )

        # Temporal compression to the latent dimension.
        self.compress = nn.Linear(256, latent_dim)

        # Global encoder: regimes, cycles, macro structure.
        self.global_layers = nn.ModuleList(
            [MarketTransformerBlock(latent_dim, heads=16, ff_dim=2048) for _ in range(8)]
        )

        self.output_norm = nn.LayerNorm(latent_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.embedding(x)
        x = self.position(x)

        for layer in self.local_layers:
            x = layer(x)

        x = self.compress(x)

        for layer in self.global_layers:
            x = layer(x)

        return self.output_norm(x)
