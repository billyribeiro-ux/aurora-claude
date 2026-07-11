"""
AURORA-SWING

RL Training Pipeline
====================

Stage 3 — connect the foundation model, world model, regime engine, environment
and risk engine, and let the agent learn trading decisions by rolling out
episodes in the simulator.
"""

from __future__ import annotations

from typing import Any

import torch

__all__ = ["RLTrainingPipeline"]


class RLTrainingPipeline:
    """Roll out episodes and accumulate reward from the actor policy."""

    def __init__(self, agent: Any, environment: Any) -> None:
        self.agent = agent
        self.environment = environment

    def train_episode(self) -> float:
        state, _ = self.environment.reset()
        done = False
        total_reward = 0.0

        while not done:
            state_tensor = torch.tensor(state, dtype=torch.float32)

            with torch.no_grad():
                mean, std = self.agent.actor(state_tensor)
                distribution = torch.distributions.Normal(mean, std)
                action = distribution.sample()

            next_state, reward, done, _, _ = self.environment.step(action.numpy())

            total_reward += reward
            state = next_state

        return total_reward
