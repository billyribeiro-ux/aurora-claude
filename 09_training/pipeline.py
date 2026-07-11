"""
AURORA-SWING

Master Training Pipeline
========================

Coordinates the full staged lifecycle: foundation → world model → RL →
validation. The system is trained in stages ("learn market language → learn
market evolution → learn trading decisions → validate → deploy carefully"),
never data-straight-to-RL-and-hope.
"""

from __future__ import annotations

from typing import Any

__all__ = ["AuroraTrainingPipeline"]


class AuroraTrainingPipeline:
    """Orchestrate the staged training of the whole system."""

    def __init__(
        self,
        foundation: Any,
        world_model: Any,
        rl_agent: Any,
        evaluator: Any,
    ) -> None:
        self.foundation = foundation
        self.world_model = world_model
        self.rl_agent = rl_agent
        self.evaluator = evaluator

    def run_training_cycle(self, data: Any) -> Any:
        print("Stage 1: Foundation Training")
        self.foundation.train()

        print("Stage 2: World Model Training")
        self.world_model.train()

        print("Stage 3: RL Adaptation")
        self.rl_agent.train()

        print("Stage 4: Validation")
        return self.evaluator.calculate(data)
