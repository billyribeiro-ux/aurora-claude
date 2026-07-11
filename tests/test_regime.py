"""Module 03 — regime engine (requires scikit-learn + hmmlearn)."""

from __future__ import annotations

import numpy as np
import pytest
from helpers import load_module


def test_regime_ensemble_end_to_end(rng: np.random.Generator) -> None:
    pytest.importorskip("sklearn")
    pytest.importorskip("hmmlearn")

    lat = load_module("03_regime_engine/latent_regime_detector.py", "latent_regime_detector")
    hmm = load_module("03_regime_engine/hmm_detector.py", "hmm_detector")
    mgr = load_module("03_regime_engine/regime_manager.py", "regime_manager")

    latents = rng.normal(0, 1, (400, 8))
    ld = lat.LatentRegimeDetector(n_regimes=5)
    ld.fit(latents)

    features = rng.normal(0, 1, (400, 6))
    hd = hmm.HMMRegimeDetector(states=5)
    hd.fit(features)

    manager = mgr.RegimeManager(ld, hd)
    out = manager.evaluate(latents[-1], features, volatility=0.03)

    assert out["regime"] in list(mgr.MarketRegime)
    assert 0.0 <= out["confidence"] <= 1.5
    profile = manager.trading_profile(out["regime"])
    assert {"position_multiplier", "stop_multiplier", "holding_days"} <= set(profile)


def test_latent_detector_requires_fit(rng: np.random.Generator) -> None:
    pytest.importorskip("sklearn")
    lat = load_module("03_regime_engine/latent_regime_detector.py", "latent_regime_detector")
    with pytest.raises(RuntimeError):
        lat.LatentRegimeDetector().predict(rng.normal(0, 1, 8))
