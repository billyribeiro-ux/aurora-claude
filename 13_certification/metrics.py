"""Performance and risk metrics — the measurement bedrock of the certification.

All functions operate on a **daily return series** (a 1-D array of per-period
fractional returns) or an explicit list of per-trade returns. Annualization uses
252 trading days. Everything here is deliberately simple and auditable: a
reviewer must be able to read each formula and agree it is correct, because every
downstream gate depends on these numbers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

TRADING_DAYS = 252

__all__ = ["PerfMetrics", "equity_curve", "perf_metrics", "trade_stats", "max_drawdown"]


def equity_curve(daily_returns: np.ndarray) -> np.ndarray:
    """Compounded equity path starting at 1.0 (length N+1)."""
    r = np.asarray(daily_returns, dtype=float)
    return np.concatenate([[1.0], np.cumprod(1.0 + r)])


def max_drawdown(eq: np.ndarray) -> float:
    """Worst peak-to-trough fractional decline of an equity curve (<= 0)."""
    eq = np.asarray(eq, dtype=float)
    peak = np.maximum.accumulate(eq)
    return float((eq / peak - 1.0).min()) if len(eq) else 0.0


def _cagr(eq: np.ndarray, n_days: int) -> float:
    if n_days <= 0 or eq[-1] <= 0:
        return 0.0
    years = n_days / TRADING_DAYS
    return float(eq[-1] ** (1.0 / years) - 1.0) if years > 0 else 0.0


def _sharpe(r: np.ndarray) -> float:
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 1e-12 else 0.0


def _sortino(r: np.ndarray) -> float:
    downside = r[r < 0]
    dd = downside.std(ddof=1) if len(downside) > 1 else 0.0
    return float(r.mean() / dd * np.sqrt(TRADING_DAYS)) if dd > 1e-12 else 0.0


@dataclass
class PerfMetrics:
    n_days: int
    total_return: float
    cagr: float
    ann_vol: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float

    def to_dict(self) -> dict:
        return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in asdict(self).items()}


def perf_metrics(daily_returns: np.ndarray) -> PerfMetrics:
    """Full risk/return summary from a daily return series."""
    r = np.asarray(daily_returns, dtype=float)
    if len(r) == 0:
        return PerfMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    eq = equity_curve(r)
    mdd = max_drawdown(eq)
    cagr = _cagr(eq, len(r))
    return PerfMetrics(
        n_days=len(r),
        total_return=float(eq[-1] - 1.0),
        cagr=cagr,
        ann_vol=float(r.std(ddof=1) * np.sqrt(TRADING_DAYS)),
        sharpe=_sharpe(r),
        sortino=_sortino(r),
        calmar=float(cagr / abs(mdd)) if mdd < -1e-9 else 0.0,
        max_drawdown=mdd,
    )


def trade_stats(trade_returns: np.ndarray, holding_days: np.ndarray | None = None) -> dict:
    """Win rate, profit factor, expectancy, streaks — from per-trade returns."""
    t = np.asarray(trade_returns, dtype=float)
    if len(t) == 0:
        return {"trades": 0}
    wins, losses = t[t > 0], t[t < 0]
    gross_win, gross_loss = float(wins.sum()), float(-losses.sum())
    # Longest run of consecutive losing trades.
    max_losing_streak, streak = 0, 0
    for x in t:
        streak = streak + 1 if x < 0 else 0
        max_losing_streak = max(max_losing_streak, streak)
    return {
        "trades": int(len(t)),
        "win_rate": float((t > 0).mean()),
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 1e-12 else float("inf"),
        "expectancy": float(t.mean()),
        "max_losing_streak": int(max_losing_streak),
        "avg_holding_days": float(np.mean(holding_days)) if holding_days is not None and len(holding_days) else None,
    }
