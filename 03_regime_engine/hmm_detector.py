"""
AURORA-SWING

Hidden Markov Market Regime Detector
====================================

A traditional statistical regime detector. Pure neural systems can drift; an HMM
adds interpretability, stability and explicit probability transitions.

States: 0 Bull Trend · 1 Bear Trend · 2 Range Bound · 3 High Volatility ·
4 Crisis. Features: return, volatility, ATR%, volume anomaly, breadth, VIX.
"""

from __future__ import annotations

import numpy as np
from hmmlearn.hmm import GaussianHMM

__all__ = ["HMMRegimeDetector"]


class HMMRegimeDetector:
    """Gaussian HMM over macro/market features."""

    def __init__(self, states: int = 5) -> None:
        self.model = GaussianHMM(
            n_components=states,
            covariance_type="full",
            n_iter=500,
        )
        self.trained = False

    def fit(self, features: np.ndarray) -> None:
        self.model.fit(features)
        self.trained = True

    def predict(self, features: np.ndarray) -> dict[str, object]:
        if not self.trained:
            raise RuntimeError("HMM not trained")

        state = self.model.predict(features)[-1]
        probabilities = self.model.predict_proba(features)[-1]

        return {"state": int(state), "probabilities": probabilities}
