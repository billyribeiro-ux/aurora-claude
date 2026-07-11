"""Pytest fixtures for the AURORA-SWING module tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(1234)


@pytest.fixture
def ohlcv(rng: np.random.Generator) -> pd.DataFrame:
    """A synthetic, well-formed OHLCV frame long enough for all feature windows."""
    n = 300
    close = np.maximum(np.cumsum(rng.normal(0, 1, n)) + 100.0, 5.0)
    return pd.DataFrame(
        {
            "open": close + rng.normal(0, 1, n),
            "high": close + rng.uniform(0, 2, n),
            "low": close - rng.uniform(0, 2, n),
            "close": close,
            "volume": rng.uniform(1e6, 5e6, n),
        },
        index=pd.date_range("2023-01-01", periods=n, freq="D"),
    )


@pytest.fixture
def returns(rng: np.random.Generator) -> np.ndarray:
    """A synthetic per-trade return series with a small positive drift."""
    return rng.normal(0.0008, 0.012, 500)
