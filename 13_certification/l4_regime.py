"""LEVEL 4 — Regime-Specific Validation.

A single blended Sharpe can hide a strategy that only works in bull markets and
bleeds everywhere else. This level classifies every out-of-sample day into a
market regime (from SPY) and reports the strategy's behaviour in each, so
weakness cannot be averaged away.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from metrics import perf_metrics
from panel import Panel

__all__ = ["classify_regimes", "run_level4"]


def classify_regimes(panel: Panel) -> pd.Series:
    """Label each date: high_volatility | bull | bear | sideways (SPY-based)."""
    spy = panel.close["SPY"].dropna()
    ret = spy.pct_change()
    sma50 = spy.rolling(50).mean()
    sma200 = spy.rolling(200).mean()
    vol = ret.rolling(20).std() * np.sqrt(252)
    vol_hi = vol.quantile(0.75)

    labels = pd.Series(index=spy.index, dtype=object)
    for d in spy.index:
        v, c, s50, s200 = vol.get(d), spy.get(d), sma50.get(d), sma200.get(d)
        if pd.isna(s200):
            labels[d] = "warmup"
        elif pd.notna(v) and v > vol_hi:
            labels[d] = "high_volatility"
        elif c > s200 and s50 > s200:
            labels[d] = "bull"
        elif c < s200:
            labels[d] = "bear"
        else:
            labels[d] = "sideways"
    return labels


def run_level4(strat_dates: np.ndarray, strat_returns: np.ndarray, panel: Panel) -> dict:
    regimes = classify_regimes(panel)
    reg_by_date = {np.datetime64(d): r for d, r in regimes.items()}

    buckets: dict[str, list[float]] = {}
    for d, r in zip(strat_dates, strat_returns):
        label = reg_by_date.get(np.datetime64(d), "warmup")
        buckets.setdefault(label, []).append(float(r))

    breakdown = {}
    for label, rets in buckets.items():
        if label == "warmup" or len(rets) < 5:
            continue
        m = perf_metrics(np.asarray(rets))
        breakdown[label] = {
            "days": len(rets),
            "total_return": round(m.total_return, 4),
            "sharpe": round(m.sharpe, 3),
            "max_drawdown": round(m.max_drawdown, 4),
            "ann_vol": round(m.ann_vol, 4),
        }

    # Soft gate: the strategy must not suffer a catastrophic (> 30%) drawdown in
    # any single regime — i.e., it degrades gracefully rather than blowing up.
    worst = min((v["max_drawdown"] for v in breakdown.values()), default=0.0)
    return {
        "level": 4,
        "name": "Regime-Specific Validation",
        "regime_breakdown": breakdown,
        "worst_regime_drawdown": round(worst, 4),
        "passed": bool(worst > -0.30),
    }
