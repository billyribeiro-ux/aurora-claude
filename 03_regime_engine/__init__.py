"""
AURORA-SWING — Module 03: Regime Intelligence Engine.

Markets are non-stationary. Before asking "is this a good setup?" the system
asks "what environment am I operating in?" — a hybrid of a latent GMM detector,
a Hidden Markov Model and volatility rules — and uses the answer to govern
strategy selection, sizing, stops, holding period and aggression.
"""

from .hmm_detector import HMMRegimeDetector
from .latent_regime_detector import LatentRegimeDetector
from .regime_manager import MarketRegime, RegimeManager

__all__ = [
    "LatentRegimeDetector",
    "HMMRegimeDetector",
    "MarketRegime",
    "RegimeManager",
]
