"""
AURORA-SWING

Advanced Market Feature Engineering
===================================

Transforms raw OHLCV and market context into normalized quantitative features
for the foundation transformer model.

Design goals
------------
* **No future leakage** — every feature is computed only from information
  available at or before the bar's close (``rolling`` / ``shift`` only look
  backwards).
* **Regime-aware** — volatility, trend and volume-anomaly features let the
  encoder distinguish market environments.
* **Stable across equities** — features are ratios / z-scores, not raw prices,
  so they generalise across instruments.
* **Transformer-friendly** — bounded, roughly-standardised numerical values.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = ["FeatureConfig", "FeatureEngineer"]


@dataclass
class FeatureConfig:
    """Look-back windows for the engineered features."""

    atr_period: int = 14
    rsi_period: int = 14
    volatility_window: int = 20
    volume_window: int = 50
    trend_window: int = 50


class FeatureEngineer:
    """Turn a raw OHLCV frame into a normalized, leakage-free feature frame."""

    def __init__(self, config: FeatureConfig | None = None) -> None:
        self.config = config or FeatureConfig()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return ``df`` augmented with engineered features.

        The input must contain ``open``, ``high``, ``low``, ``close`` and
        ``volume`` columns. Rows with undefined values (the warm-up window and
        any inf/NaN) are dropped, so the result is ready to tensorise.
        """
        data = df.copy()

        data["return"] = data["close"].pct_change()
        data["log_return"] = np.log(data["close"] / data["close"].shift(1))

        data["atr"] = self._atr(data)
        data["atr_pct"] = data["atr"] / data["close"]

        data["rsi"] = self._rsi(data["close"])

        data["volatility"] = data["return"].rolling(self.config.volatility_window).std()

        volume = data["volume"]
        vol_mean = volume.rolling(self.config.volume_window).mean()
        vol_std = volume.rolling(self.config.volume_window).std()
        data["volume_zscore"] = (volume - vol_mean) / vol_std

        trend_mean = data["close"].rolling(self.config.trend_window).mean()
        data["trend_strength"] = data["close"] / trend_mean - 1

        data["high_low_range"] = (data["high"] - data["low"]) / data["close"]

        data["close_position"] = (data["close"] - data["low"]) / (
            data["high"] - data["low"] + 1e-9
        )

        return data.replace([np.inf, -np.inf], np.nan).dropna()

    def _atr(self, df: pd.DataFrame) -> pd.Series:
        """Average True Range over ``atr_period`` bars."""
        prev_close = df["close"].shift(1)
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - prev_close).abs()
        low_close = (df["low"] - prev_close).abs()

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(self.config.atr_period).mean()

    def _rsi(self, close: pd.Series) -> pd.Series:
        """Relative Strength Index over ``rsi_period`` bars."""
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(self.config.rsi_period).mean()
        loss = (-delta.clip(upper=0)).rolling(self.config.rsi_period).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))
