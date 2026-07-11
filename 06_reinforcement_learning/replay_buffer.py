"""
AURORA-SWING

Prioritized Experience Replay
=============================

Not all trades matter equally — a critical mistake should be remembered, not
forgotten. Experiences are sampled in proportion to their priority
(``|TD error| + ε``).
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["PrioritizedReplayBuffer"]


class PrioritizedReplayBuffer:
    """A capacity-bounded buffer that samples by priority."""

    def __init__(self, capacity: int = 500_000) -> None:
        self.capacity = capacity
        self.memory: list[Any] = []
        self.priorities: list[float] = []

    def add(self, experience: Any, priority: float = 1.0) -> None:
        if len(self.memory) >= self.capacity:
            self.memory.pop(0)
            self.priorities.pop(0)
        self.memory.append(experience)
        self.priorities.append(priority)

    def sample(self, batch_size: int) -> list[Any]:
        probabilities = np.array(self.priorities) / sum(self.priorities)
        indices = np.random.choice(len(self.memory), batch_size, p=probabilities)
        return [self.memory[i] for i in indices]

    def __len__(self) -> int:
        return len(self.memory)
