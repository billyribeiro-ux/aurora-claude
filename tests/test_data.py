"""Module 01 — data layer."""

from __future__ import annotations

import pandas as pd
from helpers import load_module


def test_schema_dataclasses() -> None:
    m = load_module("01_data/market_schema.py", "market_schema")
    action = m.TradingAction(
        direction=-1,
        position_fraction=0.5,
        stop_atr_multiple=2.0,
        target_multiple=3.0,
        trailing_strength=0.1,
    )
    assert action.direction == -1
    bar = m.MarketBar(timestamp=None, open=1, high=2, low=0.5, close=1.5, volume=1e6, timeframe="1d")
    assert bar.close == 1.5


def test_feature_engineer_produces_clean_features(ohlcv: pd.DataFrame) -> None:
    m = load_module("01_data/feature_engineering.py", "feature_engineering")
    out = m.FeatureEngineer().transform(ohlcv)
    for col in ["return", "atr", "rsi", "volatility", "volume_zscore", "trend_strength"]:
        assert col in out.columns
    assert out.notna().all().all(), "engineered features must be leakage/NaN-free after dropna"
    assert out["rsi"].between(0, 100).all()
    assert len(out) > 100


def test_timeframe_builder_no_future_leakage(ohlcv: pd.DataFrame) -> None:
    m = load_module("01_data/timeframe_builder.py", "timeframe_builder")
    decision_ts = ohlcv.index[200]
    out = m.TimeframeBuilder(daily_window=50).synchronize(ohlcv, ohlcv, ohlcv, decision_ts)
    # The critical property: no bar after the decision timestamp is ever returned.
    assert (out["daily"].index <= decision_ts).all()
    assert len(out["daily"]) == 50
