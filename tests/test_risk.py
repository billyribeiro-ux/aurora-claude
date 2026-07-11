"""Module 05 — risk engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
from helpers import load_module


def test_position_sizer_risk_budget() -> None:
    m = load_module("05_risk_engine/position_sizing.py", "position_sizing")
    shares = m.PositionSizer(max_risk_per_trade=0.02).calculate(
        capital=100_000, entry_price=100, stop_price=96, confidence=0.8, regime_multiplier=1.0
    )
    assert isinstance(shares, int) and shares > 0


def test_position_sizer_zero_stop_distance() -> None:
    m = load_module("05_risk_engine/position_sizing.py", "position_sizing")
    assert m.PositionSizer().calculate(100_000, 100, 100, 1.0) == 0


def test_gap_risk_multiplier_tiers() -> None:
    m = load_module("05_risk_engine/gap_risk.py", "gap_risk")
    g = m.GapRiskModel()
    assert g.risk_multiplier(0.06) == 0.25
    assert g.risk_multiplier(0.04) == 0.50
    assert g.risk_multiplier(0.01) == 1.0


def test_volatility_model_positive(rng: np.random.Generator) -> None:
    m = load_module("05_risk_engine/volatility_model.py", "volatility_model")
    rets = pd.Series(rng.normal(0, 0.01, 300))
    vol = m.VolatilityModel().realized_volatility(rets).dropna()
    assert (vol > 0).all()


class _FakePortfolio:
    starting_capital = 100_000.0

    def __init__(self, equity_value: float) -> None:
        self._equity = equity_value

    def equity(self) -> float:
        return self._equity


def test_risk_manager_denies_in_crisis() -> None:
    m = load_module("05_risk_engine/risk_manager.py", "risk_manager")
    decision = m.RiskManager().evaluate(
        proposed_position=0.05,
        portfolio=_FakePortfolio(100_000),
        volatility=0.02,
        regime="CRISIS",
        gap_multiplier=1.0,
    )
    assert decision["approved"] is False
    assert "Market crisis" in decision["reason"]


def test_risk_manager_throttles_on_drawdown_and_vol() -> None:
    m = load_module("05_risk_engine/risk_manager.py", "risk_manager")
    decision = m.RiskManager().evaluate(
        proposed_position=0.05,
        portfolio=_FakePortfolio(80_000),  # 20% drawdown
        volatility=0.06,  # high vol
        regime="BULL_TREND",
        gap_multiplier=0.5,
    )
    assert decision["approved"] is True
    assert decision["size_multiplier"] < 1.0
    assert "Drawdown reduction" in decision["reason"]
    assert "High volatility" in decision["reason"]
