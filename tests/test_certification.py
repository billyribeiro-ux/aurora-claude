"""Module 13 — certification harness correctness tests (no network needed).

Locks in the properties the certification's credibility rests on: correct
performance math, a working PBO (overfitting is detected), a no-look-ahead
strategy construction, and the honest survivorship-bias flag.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

CERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "13_certification")
M12_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "12_learned_pipeline")
for d in (CERT_DIR, M12_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

import metrics as met  # noqa: E402
import l6_significance as l6  # noqa: E402
from l1_data_integrity import run_level1  # noqa: E402
from panel import Panel  # noqa: E402
from strategy import build_long_short  # noqa: E402


def test_max_drawdown_known() -> None:
    eq = np.array([1.0, 1.1, 0.9, 1.0])
    assert abs(met.max_drawdown(eq) - (0.9 / 1.1 - 1.0)) < 1e-9


def test_perf_metrics_positive_series() -> None:
    # A drifting series WITH variance (constant returns have zero vol → Sharpe 0).
    rng = np.random.default_rng(11)
    r = rng.normal(0.001, 0.008, 1260)  # ~5y, positive drift
    m = met.perf_metrics(r)
    assert m.total_return > 0
    assert m.sharpe > 0            # positive mean + finite vol
    assert m.max_drawdown <= 0.0   # drawdown is non-positive by definition
    assert np.isfinite(m.cagr)

    flat = met.perf_metrics(np.full(252, 0.001))
    assert flat.sharpe == 0.0      # zero-variance series → undefined Sharpe → 0
    assert flat.max_drawdown == 0.0


def test_trade_stats_streak_and_profit_factor() -> None:
    t = np.array([0.02, -0.01, -0.01, -0.01, 0.03])
    s = met.trade_stats(t)
    assert s["trades"] == 5
    assert s["max_losing_streak"] == 3
    assert s["win_rate"] == 0.4
    assert abs(s["profit_factor"] - (0.05 / 0.03)) < 1e-9


def test_pbo_detects_overfitting_on_noise() -> None:
    """Pure-noise configs → selecting the IS-best overfits → PBO well above 0."""
    rng = np.random.default_rng(0)
    M = rng.normal(0, 0.01, size=(500, 20))  # 20 configs, no real edge
    out = l6.pbo_cscv(M, S=10)
    assert 0.2 < out["pbo"] <= 1.0


def test_pbo_low_when_one_config_truly_dominates() -> None:
    """A config that is genuinely best everywhere → low overfitting probability."""
    rng = np.random.default_rng(1)
    M = rng.normal(0, 0.01, size=(500, 10))
    M[:, 0] += 0.004  # config 0 has a persistent real edge
    out = l6.pbo_cscv(M, S=10)
    assert out["pbo"] < 0.2


def test_strategy_no_lookahead_shift() -> None:
    """Positions must use only prior-day scores — changing the LAST day's score
    must not alter any earlier day's strategy return."""
    dates = pd.bdate_range("2023-01-02", periods=60)
    syms = [f"S{i}" for i in range(8)]
    rng = np.random.default_rng(3)
    close = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0, 0.01, (60, 8)), axis=0),
                         index=dates, columns=syms)
    panel = Panel(close)
    scores = pd.DataFrame(rng.normal(0, 1, (60, 8)), index=dates, columns=syms)

    a = build_long_short(scores, panel, horizon=5, quantile=0.25)
    scores2 = scores.copy()
    scores2.iloc[-1] = rng.normal(0, 1, 8)  # perturb only the final day
    b = build_long_short(scores2, panel, horizon=5, quantile=0.25)
    # All but the last position day must be identical.
    assert np.allclose(a.daily_returns[:-1], b.daily_returns[:-1])


def test_strategy_is_dollar_neutral() -> None:
    """The long/short book must carry ~zero net market exposure every day."""
    dates = pd.bdate_range("2023-01-02", periods=60)
    syms = [f"S{i}" for i in range(10)]
    rng = np.random.default_rng(4)
    close = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0, 0.01, (60, 10)), axis=0),
                         index=dates, columns=syms)
    scores = pd.DataFrame(rng.normal(0, 1, (60, 10)), index=dates, columns=syms)
    res = build_long_short(scores, Panel(close), horizon=5, quantile=0.2)
    assert np.max(np.abs(res.net_exposure)) < 1e-9   # dollar-neutral
    assert res.gross_exposure.max() > 0.9            # both legs fully live at overlap


def test_level1_flags_survivorship() -> None:
    dates = pd.bdate_range("2016-01-01", periods=400)
    rng = np.random.default_rng(5)
    data = {}
    for i, s in enumerate(["AAA", "BBB", "CCC"]):
        close = 100 * np.cumprod(1 + rng.normal(0.0003, 0.012, 400))
        data[s] = pd.DataFrame({
            "date": dates, "open": close, "high": close * 1.01,
            "low": close * 0.99, "close": close, "volume": 1_000_000,
        })
    curr = run_level1(data, universe_is_current=True)
    hist = run_level1(data, universe_is_current=False)
    surv = {c["check"]: c["passed"] for c in curr["checks"]}["survivorship_bias_controlled"]
    assert surv is False and curr["passed"] is False
    surv2 = {c["check"]: c["passed"] for c in hist["checks"]}["survivorship_bias_controlled"]
    assert surv2 is True


def test_bootstrap_ci_structure() -> None:
    rng = np.random.default_rng(6)
    r = rng.normal(0.0005, 0.01, 500)
    ci = l6.block_bootstrap_ci(r, n_boot=200, block=10, seed=1)
    assert ci["sharpe_ci95"][0] <= ci["sharpe_mean"] <= ci["sharpe_ci95"][1]
    assert 0.0 <= ci["prob_sharpe_positive"] <= 1.0
