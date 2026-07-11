"""
AURORA-SWING

Swing Trading Reinforcement Learning Environment
================================================

The core Gymnasium environment the RL agent interacts with. The agent observes a
combined state (latent market state + regime probability + portfolio condition +
world-model prediction) and emits a continuous action.

Action space (Box):
    [direction, position_size, stop_distance, target_distance, trail]
    direction ∈ [-1, 1] · size ∈ [0, 1] · stop ∈ [0.5, 5] ATR ·
    target ∈ [0.5, 8] R · trail ∈ [0, 1]
"""

from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np

__all__ = ["SwingTradingEnvironment"]


class SwingTradingEnvironment(gym.Env):
    """A Gym-compatible multi-day swing-trading simulator."""

    def __init__(self, market_data: Any, starting_capital: float = 100_000) -> None:
        super().__init__()

        self.market_data = market_data
        self.capital = starting_capital
        self.current_step = 0

        self.action_space = gym.spaces.Box(
            low=np.array([-1, 0, 0.5, 0.5, 0], dtype=np.float32),
            high=np.array([1, 1, 5, 8, 1], dtype=np.float32),
        )

        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(2048,),
            dtype=np.float32,
        )

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        self.current_step = 0
        return self._get_state(), {}

    def step(
        self, action: np.ndarray
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        previous_equity = self.capital
        self.current_step += 1

        reward = self._calculate_reward(previous_equity)
        terminated = self.current_step >= len(self.market_data) - 1

        return self._get_state(), reward, terminated, False, {}

    def _get_state(self) -> np.ndarray:
        row = self.market_data.iloc[self.current_step]
        return row.values.astype(np.float32)

    def _calculate_reward(self, previous_equity: float) -> float:
        change = self.capital - previous_equity
        return change / previous_equity
