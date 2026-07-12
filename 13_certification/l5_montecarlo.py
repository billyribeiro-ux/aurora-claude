"""LEVEL 5 — Monte Carlo Stress Testing.

The edge must survive randomness and friction:
  T1 Trade-order randomization — does the drawdown profile depend on luck of
     ordering? (final compounded return is order-invariant; max drawdown is not.)
  T2 Slippage stress — subtract turnover-scaled costs at 1x/2x/5x/10x; find where
     the strategy stops being profitable.
  T3 Gap stress — inject random ±5% overnight shocks; measure Sharpe degradation.
  T4 Missing data — randomly drop 5/10/20% of days; measure degradation.
"""

from __future__ import annotations

import numpy as np

from metrics import equity_curve, max_drawdown, perf_metrics

__all__ = ["run_level5"]

BASE_COST_BPS = 5.0  # one-way cost per unit turnover, in basis points


def _t1_order(returns: np.ndarray, n: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    base_dd = max_drawdown(equity_curve(returns))
    dds = np.empty(n)
    for i in range(n):
        dds[i] = max_drawdown(equity_curve(rng.permutation(returns)))
    return {
        "test": "trade_order_randomization",
        "simulations": n,
        "actual_max_drawdown": round(float(base_dd), 4),
        "p05_max_drawdown": round(float(np.percentile(dds, 5)), 4),
        "median_max_drawdown": round(float(np.percentile(dds, 50)), 4),
        "p95_max_drawdown": round(float(np.percentile(dds, 95)), 4),
    }


def _t2_slippage(returns: np.ndarray, turnover: np.ndarray) -> dict:
    rows = {}
    survived_at = None
    for mult in (1, 2, 5, 10):
        cost = turnover * (BASE_COST_BPS * mult / 1e4)
        net = returns - cost
        m = perf_metrics(net)
        rows[f"{mult}x"] = {"cagr": round(m.cagr, 4), "sharpe": round(m.sharpe, 3)}
        if m.sharpe > 0:
            survived_at = mult
    return {"test": "slippage_stress", "base_cost_bps": BASE_COST_BPS,
            "by_multiple": rows, "profitable_up_to_multiple": survived_at}


def _t3_gap(returns: np.ndarray, seed: int, shock: float = 0.05, frac: float = 0.05) -> dict:
    rng = np.random.default_rng(seed)
    base = perf_metrics(returns).sharpe
    sharpes = []
    for _ in range(200):
        r = returns.copy()
        k = max(1, int(len(r) * frac))
        idx = rng.choice(len(r), size=k, replace=False)
        r[idx] += rng.choice([-shock, shock], size=k)
        sharpes.append(perf_metrics(r).sharpe)
    return {"test": "gap_stress", "base_sharpe": round(base, 3),
            "stressed_sharpe_median": round(float(np.median(sharpes)), 3),
            "stressed_sharpe_p05": round(float(np.percentile(sharpes, 5)), 3)}


def _t4_missing(returns: np.ndarray, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    base = perf_metrics(returns).sharpe
    rows = {}
    for drop in (0.05, 0.10, 0.20):
        s = []
        for _ in range(100):
            keep = rng.random(len(returns)) > drop
            s.append(perf_metrics(returns[keep]).sharpe)
        rows[f"{int(drop*100)}pct"] = round(float(np.median(s)), 3)
    return {"test": "missing_data", "base_sharpe": round(base, 3), "median_sharpe_by_drop": rows}


def run_level5(returns: np.ndarray, turnover: np.ndarray, seed: int = 7, n_order: int = 10000) -> dict:
    t1 = _t1_order(returns, n_order, seed)
    t2 = _t2_slippage(returns, turnover)
    t3 = _t3_gap(returns, seed)
    t4 = _t4_missing(returns, seed)
    # Gate: survives at least normal costs (1x) and the P95 reordered drawdown is
    # not catastrophic (> -40%).
    passed = (t2["profitable_up_to_multiple"] is not None
              and t2["profitable_up_to_multiple"] >= 1
              and t1["p95_max_drawdown"] > -0.40)
    return {"level": 5, "name": "Monte Carlo Stress Testing",
            "tests": [t1, t2, t3, t4], "passed": bool(passed)}
