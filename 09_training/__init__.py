"""
AURORA-SWING — Module 09: Training Orchestration Engine.

Connects every intelligence component into a staged training lifecycle:
foundation pretraining → world-model training → RL training → validation →
deployment candidate.
"""

from .pipeline import AuroraTrainingPipeline
from .train_foundation import FoundationTrainingPipeline
from .train_rl import RLTrainingPipeline
from .train_world_model import WorldModelTrainer

__all__ = [
    "FoundationTrainingPipeline",
    "WorldModelTrainer",
    "RLTrainingPipeline",
    "AuroraTrainingPipeline",
]
