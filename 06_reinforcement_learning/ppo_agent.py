"""
AURORA-SWING

Proximal Policy Optimization Agent
==================================

Primary decision optimizer — stable and robust for continuous actions.
Implements the clipped PPO objective:

    L = min( r_t · A_t, clip(r_t, 1−ε, 1+ε) · A_t )
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

__all__ = ["PPOAgent"]


class PPOAgent:
    """Clipped-objective PPO update over an actor and critic."""

    def __init__(
        self,
        actor: torch.nn.Module,
        critic: torch.nn.Module,
        lr: float = 3e-5,
        clip: float = 0.2,
    ) -> None:
        self.actor = actor
        self.critic = critic
        self.clip = clip
        self.optimizer = torch.optim.AdamW(
            list(actor.parameters()) + list(critic.parameters()),
            lr=lr,
        )

    def update(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        old_log_probs: torch.Tensor,
        advantages: torch.Tensor,
        returns: torch.Tensor,
    ) -> float:
        mean, std = self.actor(states)
        distribution = torch.distributions.Normal(mean, std)
        log_probs = distribution.log_prob(actions).sum(-1)

        ratio = torch.exp(log_probs - old_log_probs)
        clipped_ratio = torch.clamp(ratio, 1 - self.clip, 1 + self.clip)
        policy_loss = -torch.min(ratio * advantages, clipped_ratio * advantages).mean()

        values = self.critic(states).squeeze()
        value_loss = F.mse_loss(values, returns)

        loss = policy_loss + 0.5 * value_loss

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()
