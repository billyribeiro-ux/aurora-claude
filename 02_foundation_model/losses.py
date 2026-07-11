"""
AURORA-SWING

Self-Supervised Learning Objectives
===================================

The foundation model trains against three simultaneous objectives:

1. **Masked Market Modeling** — hide pieces of market history and reconstruct
   them (BERT-style).
2. **Contrastive Learning** — similar environments should map to similar latent
   states; different environments should separate (NT-Xent).
3. **Future Latent Prediction** — predict ``z_{t+n}``.

Combined: ``L = 0.4·L_mask + 0.3·L_contrastive + 0.3·L_predictive``.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

__all__ = [
    "masked_prediction_loss",
    "contrastive_loss",
    "latent_prediction_loss",
    "total_foundation_loss",
]


def masked_prediction_loss(
    prediction: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
) -> torch.Tensor:
    """MSE over masked positions only."""
    return F.mse_loss(prediction[mask], target[mask])


def contrastive_loss(
    z1: torch.Tensor,
    z2: torch.Tensor,
    temperature: float = 0.07,
) -> torch.Tensor:
    """NT-Xent contrastive loss between two augmented views."""
    z1 = F.normalize(z1, dim=-1)
    z2 = F.normalize(z2, dim=-1)
    similarity = (z1 @ z2.T) / temperature
    labels = torch.arange(len(z1), device=z1.device)
    return F.cross_entropy(similarity, labels)


def latent_prediction_loss(
    predicted: torch.Tensor,
    actual: torch.Tensor,
) -> torch.Tensor:
    """MSE between predicted and realised future latent states."""
    return F.mse_loss(predicted, actual)


def total_foundation_loss(
    reconstruction: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
    z1: torch.Tensor,
    z2: torch.Tensor,
    future_prediction: torch.Tensor,
    future_actual: torch.Tensor,
) -> torch.Tensor:
    """Weighted sum of the three foundation objectives."""
    l_mask = masked_prediction_loss(reconstruction, target, mask)
    l_contrast = contrastive_loss(z1, z2)
    l_future = latent_prediction_loss(future_prediction, future_actual)
    return 0.4 * l_mask + 0.3 * l_contrast + 0.3 * l_future
