"""
AURORA-SWING — Module 07: Continual Learning Engine.

Turns a static trained model into a continually adapting research system.
Live experience → permanent memory → drift detection → *selective* adaptation →
knowledge preservation (EWC) → improved model. Nothing retrains blindly.
"""

from .catastrophic_forgetting import EWC
from .drift_detection import DriftDetector
from .experience_database import ExperienceDatabase, ExperienceRecord
from .model_update import AdaptiveModelUpdater

__all__ = [
    "ExperienceRecord",
    "ExperienceDatabase",
    "DriftDetector",
    "EWC",
    "AdaptiveModelUpdater",
]
