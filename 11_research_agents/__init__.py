"""
AURORA-SWING — Module 11: Research Agents.

A multi-agent research committee: specialist agents (macro, technical, risk, …)
form independent opinions that a committee aggregates into an advisory decision,
which then flows into the existing risk firewall. This is the scaffold for the
"autonomous AI quant organization" evolution — see
``00_architecture/evolution_roadmap.md``.
"""

from .base import AgentOpinion, ResearchAgent, Stance, clamp
from .committee import CommitteeDecision, ResearchCommittee
from .specialists import MacroAgent, RiskAnalystAgent, TechnicalAgent

__all__ = [
    "Stance",
    "AgentOpinion",
    "ResearchAgent",
    "clamp",
    "MacroAgent",
    "TechnicalAgent",
    "RiskAnalystAgent",
    "CommitteeDecision",
    "ResearchCommittee",
]
