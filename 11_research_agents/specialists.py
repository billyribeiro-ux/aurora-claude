"""
AURORA-SWING — Research committee specialists (transparent-heuristic scaffold).

Each specialist reads the fields of a market-context dict it cares about and
emits an :class:`AgentOpinion`. Swap any one for a trained model / LLM reasoner
behind the same ``analyze(context) -> AgentOpinion`` contract.

Context fields (all normalised): ``trend`` [-1,1], ``momentum`` [-1,1],
``rel_strength`` [-1,1], ``breadth`` [0,1], ``volatility`` (annualised, e.g.
0.15), ``rate_trend`` [-1,1], ``dollar_trend`` [-1,1].
"""

from __future__ import annotations

from typing import Any

from .base import AgentOpinion, Stance, clamp

__all__ = ["MacroAgent", "TechnicalAgent", "RiskAnalystAgent"]


class MacroAgent:
    """Reads the macro backdrop — volatility, rates and the dollar."""

    name = "macro"

    def analyze(self, context: dict[str, Any]) -> AgentOpinion:
        vix = float(context.get("volatility", 0.15))
        rate_trend = float(context.get("rate_trend", 0.0))
        dollar_trend = float(context.get("dollar_trend", 0.0))

        score = clamp(0.4 * (0.18 - vix) / 0.18 - 0.3 * rate_trend - 0.3 * dollar_trend)
        confidence = clamp(0.4 + abs(score) * 0.5, 0.0, 1.0)
        rationale = [f"vol~{vix:.2f}, rates {rate_trend:+.2f}, dollar {dollar_trend:+.2f}"]
        return AgentOpinion("macro", Stance.from_score(score), confidence, rationale, {"score": round(score, 3)})


class TechnicalAgent:
    """Reads price structure — trend, momentum and relative strength."""

    name = "technical"

    def analyze(self, context: dict[str, Any]) -> AgentOpinion:
        trend = float(context.get("trend", 0.0))
        momentum = float(context.get("momentum", 0.0))
        rel_strength = float(context.get("rel_strength", 0.0))

        score = clamp(0.45 * trend + 0.35 * momentum + 0.2 * rel_strength)
        confidence = clamp(0.4 + abs(score) * 0.5, 0.0, 1.0)
        rationale = [f"trend {trend:+.2f}, momentum {momentum:+.2f}, RS {rel_strength:+.2f}"]
        return AgentOpinion("technical", Stance.from_score(score), confidence, rationale, {"score": round(score, 3)})


class RiskAnalystAgent:
    """The defensive voice — leans risk-off when volatility is high or breadth weak."""

    name = "risk"

    def analyze(self, context: dict[str, Any]) -> AgentOpinion:
        vix = float(context.get("volatility", 0.15))
        breadth = float(context.get("breadth", 0.5))

        stress = clamp((vix - 0.18) / 0.18 * 0.6 + (0.5 - breadth) * 0.8, -1.0, 1.0)
        score = -stress  # elevated stress => defensive lean
        confidence = clamp(0.5 + abs(stress) * 0.4, 0.0, 1.0)
        rationale = [f"vol~{vix:.2f}, breadth {breadth:.0%} -> stress {stress:+.2f}"]
        return AgentOpinion("risk", Stance.from_score(score), confidence, rationale, {"stress": round(stress, 3)})
