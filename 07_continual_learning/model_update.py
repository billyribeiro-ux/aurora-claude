"""
AURORA-SWING

Autonomous Model Update Controller
==================================

Controls *when* models may change. The system does **not** update after every
trade — that creates instability. Updates require evidence: sufficient samples
plus either detected drift or material performance decay.
"""

from __future__ import annotations

from typing import Any

__all__ = ["AdaptiveModelUpdater"]


class AdaptiveModelUpdater:
    """Gate adaptation on statistical evidence, and describe the update plan."""

    def __init__(self, minimum_samples: int = 500) -> None:
        self.minimum_samples = minimum_samples

    def should_update(
        self,
        drift_result: dict[str, Any],
        performance_decay: float,
        samples: int,
    ) -> bool:
        if samples < self.minimum_samples:
            return False
        if drift_result["drift"]:
            return True
        if performance_decay > 0.15:
            return True
        return False

    def update_plan(self) -> dict[str, str]:
        return {
            "foundation_model": "small_lr_finetune",
            "world_model": "retrain_recent",
            "policy": "PPO_adaptation",
            "risk": "always_active",
        }
