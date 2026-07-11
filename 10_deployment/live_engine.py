"""
AURORA-SWING

Live Autonomous Trading Engine
==============================

The main inference engine. It orchestrates the full decision pipeline for a
single market observation:

    LIVE MARKET DATA
          |
          v
    Foundation Encoder      ->  latent market intelligence
          |
          v
    World Model Forecast    ->  future latent + uncertainty
          |
          v
    Regime Detection        ->  operating environment
          |
          v
    RL Decision             ->  raw action proposal
          |
          v
    Risk Firewall           ->  approve / reject / resize

Design principle
----------------
The live system NEVER trades directly from the neural-network output. Every
proposed action must pass the risk firewall before it can become an approved
trade. This module produces an ``analysis`` record; the *signal service* and
*execution layer* consume it downstream.

All upstream components (encoder, world model, regime engine, policy, risk
manager) are injected via the constructor, so this engine has no hard
dependency on any particular module implementation.
"""

from __future__ import annotations

from typing import Any, Protocol

import torch

__all__ = ["AuroraLiveEngine"]


class _Module(Protocol):
    """Minimal structural type for the injected neural components."""

    def eval(self) -> Any: ...

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class AuroraLiveEngine:
    """Coordinate encoder, world model, regime engine, policy and risk manager.

    Parameters
    ----------
    encoder:
        Foundation model that maps a market tensor to a latent sequence of
        shape ``(batch, time, latent_dim)``.
    world_model:
        Consumes the latent sequence and returns a mapping that contains at
        least an ``"uncertainty"`` tensor.
    regime_engine:
        Object exposing ``evaluate(latent_np, regime_features, uncertainty)``
        and returning a mapping whose ``"regime"`` value has a ``.name``.
    policy:
        RL policy returning ``(action_mean, action_std_or_value)`` from the
        most recent latent step.
    risk_manager:
        Object exposing ``evaluate(action, portfolio, uncertainty, regime,
        confidence)`` and returning a mapping with an ``"approved"`` flag.
    """

    def __init__(
        self,
        encoder: _Module,
        world_model: _Module,
        regime_engine: Any,
        policy: _Module,
        risk_manager: Any,
    ) -> None:
        self.encoder = encoder
        self.world_model = world_model
        self.regime_engine = regime_engine
        self.policy = policy
        self.risk_manager = risk_manager

        # Inference-only components must be frozen into evaluation mode so that
        # dropout / batch-norm behave deterministically in production.
        self.encoder.eval()
        self.world_model.eval()
        self.policy.eval()

    def analyze_market(
        self,
        market_tensor: "torch.Tensor",
        regime_features: Any,
        portfolio: Any,
    ) -> dict[str, Any]:
        """Run the full inference pipeline for one market observation.

        Returns
        -------
        dict
            ``{"raw_action", "regime", "risk", "world"}`` — the complete,
            structured analysis record consumed by the signal service.
        """
        # ---- Neural forward passes (no gradient tracking in production) -----
        with torch.no_grad():
            latent = self.encoder(market_tensor)

            world_prediction = self.world_model(latent)

            # The policy acts on the most recent latent step only.
            action_mean, _ = self.policy(latent[:, -1])

        uncertainty = float(world_prediction["uncertainty"].item())

        # ---- Regime detection (operates on detached numpy features) --------
        latent_now = latent[:, -1].detach().cpu().numpy()
        regime = self.regime_engine.evaluate(
            latent_now,
            regime_features,
            uncertainty,
        )

        # ---- Risk firewall -------------------------------------------------
        # Confidence is passed as 1.0 here; the signal service derives the
        # calibrated confidence from world-model uncertainty for reporting.
        risk = self.risk_manager.evaluate(
            action_mean,
            portfolio,
            uncertainty,
            regime["regime"].name,
            1.0,
        )

        return {
            "raw_action": action_mean,
            "regime": regime,
            "risk": risk,
            "world": world_prediction,
        }

    @staticmethod
    def approve_trade(analysis: dict[str, Any]) -> bool:
        """Return the risk firewall's final approval decision for an analysis."""
        return bool(analysis["risk"]["approved"])
