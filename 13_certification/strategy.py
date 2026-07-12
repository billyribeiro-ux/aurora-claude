"""Turn a cross-sectional signal into a tradable daily return series.

Construction (the standard way to trade an H-day cross-sectional signal without
look-ahead and without pretending to zero turnover):

  * each day, rank names by the signal and form a dollar-neutral book — long the
    top quintile, short the bottom quintile, equal weight within each leg;
  * hold each day's book for H days, so on any given day the live portfolio is
    the average of the last H daily books (overlapping tranches, ~1/H turnover);
  * the strategy's daily return is the weighted sum of next-day name returns.

The signal at date t uses only information available at t (it comes from the
leakage-safe Module 12 dataset), and it is applied to the return from t to t+1 —
no future information enters the position.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from panel import Panel

__all__ = ["StrategyResult", "build_long_short"]


@dataclass
class StrategyResult:
    daily_returns: np.ndarray      # aligned to `dates`
    dates: np.ndarray
    trade_returns: np.ndarray      # per (name, tranche) realized H-day return
    gross_exposure: np.ndarray     # daily gross (sum |w|) — for turnover/cost sizing
    turnover: np.ndarray           # daily one-way turnover
    net_exposure: np.ndarray       # daily net (sum w) — ~0 for a dollar-neutral book


def _daily_books(scores: pd.DataFrame, quantile: float) -> pd.DataFrame:
    """Dollar-neutral target weights per day from cross-sectional score ranks."""
    books = pd.DataFrame(0.0, index=scores.index, columns=scores.columns)
    for d, row in scores.iterrows():
        s = row.dropna()
        if len(s) < 5:
            continue
        k = max(1, int(len(s) * quantile))
        ranked = s.sort_values()
        shorts, longs = ranked.index[:k], ranked.index[-k:]
        books.loc[d, longs] = 0.5 / len(longs)     # +0.5 gross on the long leg
        books.loc[d, shorts] = -0.5 / len(shorts)  # -0.5 gross on the short leg
    return books


def build_long_short(
    scores: pd.DataFrame, panel: Panel, horizon: int, quantile: float = 0.2
) -> StrategyResult:
    """Overlapping H-day dollar-neutral quantile long/short from a score panel."""
    # Align scores to the panel's trading calendar and forward returns.
    scores = scores.reindex(panel.close.index)
    books = _daily_books(scores, quantile)

    # Effective held weights = average of the last H daily books (overlap).
    eff = books.rolling(window=horizon, min_periods=1).mean().shift(1).fillna(0.0)
    ret = panel.ret.reindex(columns=eff.columns).fillna(0.0)
    daily = (eff * ret).sum(axis=1)

    # Turnover / gross / net for cost modelling and the neutrality check.
    gross = eff.abs().sum(axis=1)
    net = eff.sum(axis=1)
    turnover = eff.diff().abs().sum(axis=1).fillna(0.0)

    # Per-tranche realized trades (for trade statistics): each name entered on
    # day t earns its H-day forward return (sign by book side).
    fwd = panel.close.pct_change(horizon).shift(-horizon)  # t -> t+H return
    trades = []
    for d in books.index:
        w = books.loc[d]
        held = w[w != 0]
        for sym, weight in held.items():
            f = fwd.loc[d, sym] if (d in fwd.index and sym in fwd.columns) else np.nan
            if np.isfinite(f):
                trades.append(np.sign(weight) * f)

    valid = daily.notna().to_numpy()
    return StrategyResult(
        daily_returns=daily.fillna(0.0).to_numpy()[valid],
        dates=daily.index.to_numpy()[valid],
        trade_returns=np.asarray(trades, dtype=float),
        gross_exposure=gross.to_numpy()[valid],
        turnover=turnover.to_numpy()[valid],
        net_exposure=net.to_numpy()[valid],
    )
