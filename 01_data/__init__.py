"""
AURORA-SWING — Module 01: Data layer.

Leakage-free market-state construction. Every downstream component depends on the
schema and feature contracts defined here.
"""

from .data_pipeline import MarketDataPipeline
from .feature_engineering import FeatureConfig, FeatureEngineer
from .market_schema import (
    FeatureVector,
    MarketBar,
    MultiTimeframeState,
    PortfolioState,
    TradeExperience,
    TradingAction,
)
from .timeframe_builder import TimeframeBuilder

__all__ = [
    "MarketDataPipeline",
    "FeatureConfig",
    "FeatureEngineer",
    "FeatureVector",
    "MarketBar",
    "MultiTimeframeState",
    "PortfolioState",
    "TradeExperience",
    "TradingAction",
    "TimeframeBuilder",
]
