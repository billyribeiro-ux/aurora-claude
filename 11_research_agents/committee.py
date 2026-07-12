"""
AURORA-SWING — Research Committee.

Runs every specialist over a market context, then aggregates their opinions into
a single :class:`CommitteeDecision` via a confidence- and weight-scaled vote.
The committee only *forwards* a directional signal when conviction and consensus
clear thresholds — otherwise it holds. The decision is advisory: it flows into
the existing risk firewall, which retains final authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .base import AgentOpinion, ResearchAgent, Stance, clamp

__all__ = ["CommitteeDecision", "ResearchCommittee"]


@dataclass
class CommitteeDecision:
    stance: Stance
    score: float  # aggregate conviction [-1, 1]
    confidence: float  # mean agent confidence [0, 1]
    consensus: float  # fraction agreeing with the majority sign [0, 1]
    approved_to_signal: bool
    opinions: list[AgentOpinion] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)


class ResearchCommittee:
    """Aggregate specialist opinions into an advisory committee decision."""

    def __init__(
        self,
        agents: Iterable[ResearchAgent],
        weights: Mapping[str, float] | None = None,
        entry_threshold: float = 0.2,
        min_consensus: float = 0.5,
    ) -> None:
        self.agents = list(agents)
        self.weights = dict(weights) if weights else {a.name: 1.0 for a in self.agents}
        self.entry_threshold = entry_threshold
        self.min_consensus = min_consensus

    def deliberate(self, context: dict[str, Any]) -> CommitteeDecision:
        opinions = [agent.analyze(context) for agent in self.agents]
        if not opinions:
            return CommitteeDecision(Stance.NEUTRAL, 0.0, 0.0, 0.0, False)

        total_weight = sum(self.weights.get(o.agent, 1.0) for o in opinions) or 1.0
        score = clamp(
            sum(self.weights.get(o.agent, 1.0) * o.signed_conviction for o in opinions) / total_weight
        )
        confidence = sum(o.confidence for o in opinions) / len(opinions)

        signs = [1 if o.stance.value > 0 else -1 if o.stance.value < 0 else 0 for o in opinions]
        consensus = max(signs.count(1), signs.count(-1), signs.count(0)) / len(signs)

        approved = abs(score) >= self.entry_threshold and consensus >= self.min_consensus

        rationale = [f"{o.agent}: {o.stance.name} @ {o.confidence:.0%}" for o in opinions]
        rationale.append(
            f"aggregate {score:+.2f}, consensus {consensus:.0%} -> {'FORWARD' if approved else 'HOLD'}"
        )

        return CommitteeDecision(
            stance=Stance.from_score(score),
            score=round(score, 3),
            confidence=round(confidence, 3),
            consensus=round(consensus, 3),
            approved_to_signal=approved,
            opinions=opinions,
            rationale=rationale,
        )
