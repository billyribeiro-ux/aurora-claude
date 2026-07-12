"""
AURORA-SWING — Module 11: Research Agents (multi-agent scaffold).

Base interfaces for the research committee — the next evolutionary step from a
single decision engine toward an autonomous AI *research organization*.

Each agent is a specialist that forms an OPINION on a market context. A
committee aggregates those opinions into a decision that then flows into the
existing risk firewall + signal service (Module 05 / Module 10) — the risk
engine keeps its independent authority.

> This is a SCAFFOLD. The specialists shipped here use transparent heuristics
> (same philosophy as the console's decision engine) so the committee runs and
> is testable today. In production each agent is backed by a trained model or an
> LLM reasoner behind exactly this interface — a drop-in, contract-preserving
> upgrade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

__all__ = ["Stance", "AgentOpinion", "ResearchAgent", "clamp"]


def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


class Stance(Enum):
    """An agent's directional lean."""

    STRONG_SELL = -2
    SELL = -1
    NEUTRAL = 0
    BUY = 1
    STRONG_BUY = 2

    @classmethod
    def from_score(cls, score: float) -> "Stance":
        if score >= 0.5:
            return cls.STRONG_BUY
        if score >= 0.15:
            return cls.BUY
        if score <= -0.5:
            return cls.STRONG_SELL
        if score <= -0.15:
            return cls.SELL
        return cls.NEUTRAL


@dataclass
class AgentOpinion:
    """One specialist's view, with an explainability trail."""

    agent: str
    stance: Stance
    confidence: float  # [0, 1]
    rationale: list[str] = field(default_factory=list)
    features: dict[str, float] = field(default_factory=dict)

    @property
    def signed_conviction(self) -> float:
        """Stance in [-2, 2] mapped to [-1, 1] and scaled by confidence."""
        return (self.stance.value / 2.0) * self.confidence


@runtime_checkable
class ResearchAgent(Protocol):
    """Structural type every specialist implements."""

    name: str

    def analyze(self, context: dict[str, Any]) -> AgentOpinion: ...
