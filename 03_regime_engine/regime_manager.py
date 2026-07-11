"""
AURORA-SWING

Unified Regime Intelligence Layer
=================================

Combines the neural latent regime (40%), the HMM regime (40%) and volatility
rules (20%) into a single decision, and maps each regime to a trading profile
(sizing, stop distance, holding period).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import numpy as np

__all__ = ["MarketRegime", "RegimeManager"]


class MarketRegime(Enum):
    BULL_TREND = 0
    BEAR_TREND = 1
    RANGE = 2
    HIGH_VOLATILITY = 3
    CRISIS = 4


class RegimeManager:
    """Ensemble the latent + HMM detectors with a volatility override."""

    def __init__(self, latent_detector: Any, hmm_detector: Any) -> None:
        self.latent = latent_detector
        self.hmm = hmm_detector

    def evaluate(
        self,
        latent_state: np.ndarray,
        hmm_features: np.ndarray,
        volatility: float,
    ) -> dict[str, Any]:
        latent_result = self.latent.predict(latent_state)
        hmm_result = self.hmm.predict(hmm_features)

        combined = (
            0.4 * np.asarray(latent_result["probabilities"])
            + 0.4 * np.asarray(hmm_result["probabilities"])
        )

        # Volatility override — the 20% statistical-rules component.
        if volatility > 0.05:
            combined[3] += 0.2

        regime = int(combined.argmax())
        confidence = float(combined.max())

        return {
            "regime": MarketRegime(regime),
            "confidence": confidence,
            "distribution": combined,
        }

    def trading_profile(self, regime: MarketRegime) -> dict[str, float]:
        """Sizing / stop / holding profile for a regime."""
        profiles: dict[MarketRegime, dict[str, float]] = {
            MarketRegime.BULL_TREND: {"position_multiplier": 1.0, "stop_multiplier": 2.5, "holding_days": 20},
            MarketRegime.BEAR_TREND: {"position_multiplier": 0.7, "stop_multiplier": 2.0, "holding_days": 15},
            MarketRegime.RANGE: {"position_multiplier": 0.5, "stop_multiplier": 1.2, "holding_days": 5},
            MarketRegime.HIGH_VOLATILITY: {"position_multiplier": 0.25, "stop_multiplier": 3.5, "holding_days": 7},
            MarketRegime.CRISIS: {"position_multiplier": 0.0, "stop_multiplier": 5.0, "holding_days": 0},
        }
        return profiles[regime]
