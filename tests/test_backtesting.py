"""Module 08 — backtesting & validation (incl. the Monte Carlo fix)."""

from __future__ import annotations

import numpy as np
from helpers import load_module


def test_performance_evaluator(returns: np.ndarray) -> None:
    m = load_module("08_backtesting/evaluation.py", "evaluation")
    r = m.PerformanceEvaluator().calculate(returns)
    assert {"return", "max_drawdown", "volatility", "sharpe", "sortino"} <= set(r)
    assert r["max_drawdown"] <= 0.0


def test_walk_forward_runs_every_window() -> None:
    m = load_module("08_backtesting/walk_forward.py", "walk_forward")
    windows = [
        m.WalkForwardWindow("2015-01-01", "2018-12-31", "2019-01-01", "2019-12-31"),
        m.WalkForwardWindow("2016-01-01", "2019-12-31", "2020-01-01", "2020-12-31"),
    ]
    calls: list[str] = []

    def train(a: str, b: str) -> dict:
        calls.append("train")
        return {"trained": (a, b)}

    def evaluate(model: dict, a: str, b: str) -> dict:
        return {"sharpe": 1.4}

    results = m.WalkForwardEngine(windows).run(train, evaluate)
    assert len(results) == 2
    assert calls == ["train", "train"]
    assert results[0]["result"]["sharpe"] == 1.4


def test_monte_carlo_shuffle_final_invariant_but_drawdown_varies(returns: np.ndarray) -> None:
    """The core fix: shuffling trade order leaves the final return invariant
    (it is a commutative product) but the drawdown path must vary."""
    m = load_module("08_backtesting/monte_carlo.py", "monte_carlo")
    sim = m.MonteCarloSimulator(simulations=400)
    res = sim.shuffle_returns(returns)

    assert np.std(res["final_return"]) < 1e-9, "final return is order-invariant"
    assert np.std(res["max_drawdown"]) > 0.0, "max drawdown must depend on trade order"

    stats = sim.statistics(res)
    assert stats["max_drawdown"]["worst"] <= stats["max_drawdown"]["median"]


def test_monte_carlo_bootstrap_varies_final_return(returns: np.ndarray) -> None:
    """Bootstrap resampling (with replacement) must vary the final return too."""
    m = load_module("08_backtesting/monte_carlo.py", "monte_carlo")
    sim = m.MonteCarloSimulator(simulations=400)
    res = sim.bootstrap_returns(returns)
    assert np.std(res["final_return"]) > 0.0
    assert np.std(res["max_drawdown"]) > 0.0
