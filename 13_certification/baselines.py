"""Required baselines the strategy must beat (Level 3).

All are computed on SPY over the same out-of-sample window and returned as daily
return series, so they are directly comparable on risk-adjusted terms (Sharpe,
Calmar, drawdown) even though a market-neutral book and a long-only index have
different absolute-return profiles — which the report states explicitly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from panel import Panel

__all__ = ["buy_and_hold", "momentum", "ma_cross", "random_agent", "all_baselines"]


def buy_and_hold(panel: Panel, start: str, end: str) -> np.ndarray:
    return panel.spy_returns(start, end)


def _spy_close(panel: Panel) -> pd.Series:
    return panel.close["SPY"].dropna()


def momentum(panel: Panel, start: str, end: str, lookback: int = 20) -> np.ndarray:
    """Long SPY when it is above its `lookback`-day high, else flat (next-day)."""
    close = _spy_close(panel)
    roll_high = close.rolling(lookback).max()
    signal = (close >= roll_high).astype(float).shift(1)  # decide on prior close
    ret = close.pct_change() * signal
    m = (ret.index >= np.datetime64(start)) & (ret.index <= np.datetime64(end))
    return ret.loc[m].fillna(0.0).to_numpy()


def ma_cross(panel: Panel, start: str, end: str, fast: int = 50, slow: int = 200) -> np.ndarray:
    """Long SPY when SMA(fast) > SMA(slow), else flat (classic trend filter)."""
    close = _spy_close(panel)
    sig = (close.rolling(fast).mean() > close.rolling(slow).mean()).astype(float).shift(1)
    ret = close.pct_change() * sig
    m = (ret.index >= np.datetime64(start)) & (ret.index <= np.datetime64(end))
    return ret.loc[m].fillna(0.0).to_numpy()


def random_agent(panel: Panel, start: str, end: str, seed: int = 7) -> np.ndarray:
    """Random ±1 SPY exposure each day — the 'must massively outperform' floor."""
    spy = panel.spy_returns(start, end)
    rng = np.random.default_rng(seed)
    pos = rng.choice([-1.0, 1.0], size=len(spy))
    return spy * pos


def all_baselines(panel: Panel, start: str, end: str) -> dict[str, np.ndarray]:
    return {
        "buy_and_hold_spy": buy_and_hold(panel, start, end),
        "momentum_20d": momentum(panel, start, end),
        "ma_cross_50_200": ma_cross(panel, start, end),
        "random_agent": random_agent(panel, start, end),
    }
