"""Rich, leakage-free feature engine for cross-sectional equity alpha research.

~24 features from daily OHLCV only — multi-horizon momentum & reversal, volatility
structure, trend, range/liquidity, and distribution shape. Every feature looks
strictly backwards (rolling/shift), so a feature at date t uses only bars <= t.

These are meant to be **cross-sectionally rank-normalized** per day (see
``alpha_research.py``): what matters for stock selection is a name's rank against
its peers that day, not its raw level.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["FEATURES", "compute_features"]

FEATURES: list[str] = [
    "mom_5", "mom_10", "mom_20", "mom_60", "mom_120",
    "rev_5", "accel_10",
    "vol_10", "vol_20", "vol_60", "downside_vol_20", "vol_of_vol",
    "rsi_14", "rsi_28",
    "px_sma20", "px_sma50", "px_sma200", "sma_50_200",
    "dist_52w_high", "dist_52w_low",
    "atr_pct_14", "range_20", "volume_z_20", "skew_20",
]


def _rsi(close: pd.Series, n: int) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).rolling(n).mean()
    loss = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + gain / (loss + 1e-9))


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a leakage-free feature frame (indexed by date) for one symbol.

    Input must have columns open/high/low/close/volume; index or a 'date' column.
    """
    d = df.copy()
    if "date" in d.columns:
        d = d.set_index("date")
    d = d.sort_index()
    close, high, low, vol = d["close"], d["high"], d["low"], d["volume"]
    ret = close.pct_change()
    out = pd.DataFrame(index=d.index)

    # Momentum (skip the most recent day to reduce microstructure noise on entry).
    for n in (5, 10, 20, 60, 120):
        out[f"mom_{n}"] = close.shift(1) / close.shift(n + 1) - 1.0
    out["rev_5"] = -(close / close.shift(5) - 1.0)          # short-term reversal
    out["accel_10"] = (close / close.shift(10) - 1.0) - (close.shift(10) / close.shift(20) - 1.0)

    # Volatility structure.
    out["vol_10"] = ret.rolling(10).std()
    out["vol_20"] = ret.rolling(20).std()
    out["vol_60"] = ret.rolling(60).std()
    out["downside_vol_20"] = ret.clip(upper=0).rolling(20).std()
    out["vol_of_vol"] = ret.rolling(20).std().rolling(60).std()

    out["rsi_14"] = _rsi(close, 14)
    out["rsi_28"] = _rsi(close, 28)

    # Trend / moving-average distances.
    out["px_sma20"] = close / close.rolling(20).mean() - 1.0
    out["px_sma50"] = close / close.rolling(50).mean() - 1.0
    out["px_sma200"] = close / close.rolling(200).mean() - 1.0
    out["sma_50_200"] = close.rolling(50).mean() / close.rolling(200).mean() - 1.0

    # Position within range.
    out["dist_52w_high"] = close / high.rolling(252).max() - 1.0
    out["dist_52w_low"] = close / low.rolling(252).min() - 1.0

    # Range / liquidity / shape.
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    out["atr_pct_14"] = tr.rolling(14).mean() / close
    out["range_20"] = ((high - low) / close).rolling(20).mean()
    out["volume_z_20"] = (vol - vol.rolling(20).mean()) / (vol.rolling(20).std() + 1e-9)
    out["skew_20"] = ret.rolling(20).skew()

    out["close"] = close  # kept for label construction, dropped from the model matrix
    return out.replace([np.inf, -np.inf], np.nan).dropna()
