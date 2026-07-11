"""
AURORA-SWING

Latent Regime Detector
======================

Detects hidden market states from the foundation transformer's learned
representation ``z_t``. The core assumption: market regimes form clusters in
latent space, so a Gaussian Mixture Model over the latents recovers them.
"""

from __future__ import annotations

import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

__all__ = ["LatentRegimeDetector"]


class LatentRegimeDetector:
    """Cluster latent market states into regimes with a Gaussian Mixture Model."""

    def __init__(self, n_regimes: int = 5) -> None:
        self.n_regimes = n_regimes
        self.scaler = StandardScaler()
        self.model = GaussianMixture(
            n_components=n_regimes,
            covariance_type="full",
            max_iter=500,
            random_state=42,
        )
        self.trained = False

    def fit(self, latent_vectors: np.ndarray) -> None:
        scaled = self.scaler.fit_transform(latent_vectors)
        self.model.fit(scaled)
        self.trained = True

    def predict(self, latent_vector: np.ndarray) -> dict[str, object]:
        if not self.trained:
            raise RuntimeError("Regime model not trained")

        x = self.scaler.transform(latent_vector.reshape(1, -1))
        regime = self.model.predict(x)[0]
        probabilities = self.model.predict_proba(x)[0]

        return {"regime": int(regime), "probabilities": probabilities}

    def uncertainty(self, latent_vector: np.ndarray) -> float:
        """1 − max posterior probability: high when the regime is ambiguous."""
        x = self.scaler.transform(latent_vector.reshape(1, -1))
        probability = self.model.predict_proba(x)
        return float(1 - np.max(probability))
