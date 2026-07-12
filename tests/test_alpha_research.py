"""Module 14 — rich feature engine leakage-safety (no network)."""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

M14 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "14_alpha_research")
if M14 not in sys.path:
    sys.path.insert(0, M14)

from features_plus import FEATURES, compute_features  # noqa: E402


def _synth(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2016-01-01", periods=n)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, n)))
    openp = close * (1 + rng.normal(0, 0.003, n))
    high = np.maximum(openp, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(openp, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    return pd.DataFrame({"date": dates, "open": openp, "high": high, "low": low,
                         "close": close, "volume": rng.integers(1e6, 5e6, n)})


def test_features_no_look_ahead() -> None:
    """Perturbing a FUTURE bar must not change any earlier feature row."""
    df = _synth(400, seed=1)
    f1 = compute_features(df)
    df2 = df.copy()
    df2.loc[df2.index[-1], "close"] *= 1.15  # change only the last bar
    f2 = compute_features(df2)
    common = f1.index.intersection(f2.index)[:-1]
    assert np.allclose(f1.loc[common, FEATURES].to_numpy(),
                       f2.loc[common, FEATURES].to_numpy())


def test_features_are_finite_and_complete() -> None:
    f = compute_features(_synth(400, seed=2))
    assert len(f) > 100
    assert not f[FEATURES].isna().any().any()
    assert np.isfinite(f[FEATURES].to_numpy()).all()
    assert len(FEATURES) == 24
