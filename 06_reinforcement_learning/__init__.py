"""
AURORA-SWING — Module 06: Reinforcement Learning Engine.

The autonomous trading brain. A hybrid PPO (primary, stable) + SAC (exploration)
agent learns which actions maximise long-term risk-adjusted capital growth,
trained against risk-adjusted rewards with prioritized experience replay.
"""

from .actor_critic import ActorNetwork, CriticNetwork
from .ppo_agent import PPOAgent
from .replay_buffer import PrioritizedReplayBuffer
from .reward import TradingReward
from .sac_component import SACEntropyController

__all__ = [
    "ActorNetwork",
    "CriticNetwork",
    "TradingReward",
    "PrioritizedReplayBuffer",
    "PPOAgent",
    "SACEntropyController",
]
