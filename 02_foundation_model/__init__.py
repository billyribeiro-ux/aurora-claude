"""
AURORA-SWING — Module 02: Foundation Model.

The market-perception brain. A hierarchical transformer encoder compresses
multi-timeframe observations into a latent market state; a latent world model
rolls that state forward with reward and uncertainty estimates. Trained with
self-supervised objectives (masked modeling, contrastive, future-latent).
"""

from .embeddings import MarketEmbedding
from .hierarchical_encoder import HierarchicalMarketEncoder
from .losses import (
    contrastive_loss,
    latent_prediction_loss,
    masked_prediction_loss,
    total_foundation_loss,
)
from .market_decoder import MarketDecoder
from .positional_encoding import TemporalEmbedding
from .pretraining import FoundationTrainer
from .transformer_blocks import MarketTransformerBlock
from .world_model import LatentDynamicsBlock, MarketWorldModel

__all__ = [
    "MarketEmbedding",
    "TemporalEmbedding",
    "MarketTransformerBlock",
    "HierarchicalMarketEncoder",
    "MarketDecoder",
    "LatentDynamicsBlock",
    "MarketWorldModel",
    "masked_prediction_loss",
    "contrastive_loss",
    "latent_prediction_loss",
    "total_foundation_loss",
    "FoundationTrainer",
]
