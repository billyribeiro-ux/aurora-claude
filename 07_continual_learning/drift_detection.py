"""
AURORA-SWING

Market Drift Detection
======================

Detects when the market environment changes — a momentum strategy trained in an
AI bull market may fail in a rate shock. Uses latent distribution shift measured
by the Population Stability Index (PSI) against a reference window.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["DriftDetector"]


class DriftDetector:
    """Flags regime drift when the latent distribution moves past a threshold."""

    def __init__(self, threshold: float = 0.25) -> None:
        self.threshold = threshold

    def population_stability_index(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        bins: int = 20,
    ) -> float:
        """PSI between a reference and current latent distribution."""
        ref_hist, _ = np.histogram(reference, bins=bins, density=True)
        cur_hist, _ = np.histogram(current, bins=bins, density=True)

        ref_hist = ref_hist + 1e-8
        cur_hist = cur_hist + 1e-8

        psi = np.sum((cur_hist - ref_hist) * np.log(cur_hist / ref_hist))
        return float(psi)

    def detect(
        self,
        reference_latent: np.ndarray,
        current_latent: np.ndarray,
    ) -> dict[str, Any]:
        score = self.population_stability_index(reference_latent, current_latent)
        return {"drift": score > self.threshold, "score": score}
