"""Module 11 — research committee scaffold."""

from __future__ import annotations

from helpers import load_package


def _committee():
    ra = load_package("11_research_agents")
    return ra, ra.ResearchCommittee([ra.MacroAgent(), ra.TechnicalAgent(), ra.RiskAnalystAgent()])


def test_bullish_context_forwards_a_long() -> None:
    ra, committee = _committee()
    ctx = {
        "trend": 0.8, "momentum": 0.7, "rel_strength": 0.5,
        "volatility": 0.13, "breadth": 0.72, "rate_trend": -0.1, "dollar_trend": -0.1,
    }
    d = committee.deliberate(ctx)
    assert d.score > 0
    assert d.stance.value > 0
    assert d.approved_to_signal is True
    assert len(d.opinions) == 3
    assert 0.0 <= d.confidence <= 1.0
    assert 0.0 <= d.consensus <= 1.0


def test_stressed_context_leans_defensive() -> None:
    _, committee = _committee()
    ctx = {
        "trend": -0.6, "momentum": -0.5, "rel_strength": -0.3,
        "volatility": 0.42, "breadth": 0.2, "rate_trend": 0.5, "dollar_trend": 0.4,
    }
    d = committee.deliberate(ctx)
    assert d.score < 0
    assert d.stance.value < 0


def test_weak_mixed_signal_holds() -> None:
    _, committee = _committee()
    ctx = {"trend": 0.1, "momentum": -0.05, "rel_strength": 0.0, "volatility": 0.18, "breadth": 0.5}
    d = committee.deliberate(ctx)
    assert d.approved_to_signal is False


def test_empty_committee_is_neutral() -> None:
    ra = load_package("11_research_agents")
    d = ra.ResearchCommittee([]).deliberate({"trend": 0.9})
    assert d.stance is ra.Stance.NEUTRAL
    assert d.approved_to_signal is False


def test_weights_shift_the_aggregate() -> None:
    ra = load_package("11_research_agents")
    agents = [ra.MacroAgent(), ra.TechnicalAgent(), ra.RiskAnalystAgent()]
    ctx = {"trend": 0.6, "momentum": 0.5, "rel_strength": 0.4, "volatility": 0.35, "breadth": 0.35}
    tech_heavy = ra.ResearchCommittee(agents, weights={"technical": 3.0, "macro": 1.0, "risk": 1.0})
    risk_heavy = ra.ResearchCommittee(agents, weights={"technical": 1.0, "macro": 1.0, "risk": 3.0})
    assert tech_heavy.deliberate(ctx).score > risk_heavy.deliberate(ctx).score
