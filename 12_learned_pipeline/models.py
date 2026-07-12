"""Estimators + honest out-of-sample metrics for the learned pipeline.

Three competitors on the SAME walk-forward split:
  * ``always_long``  — the null model (predict "up" every day). Because equities
    drift up, this is a deceptively strong accuracy baseline; a model only earns
    the word "signal" by beating it AND showing a positive Information
    Coefficient.
  * hand-feature Logistic / Gradient-Boosting — a competent human's feature model.
  * linear probe on the frozen self-supervised representation (the E2 gate).

Metrics (all strictly out-of-sample):
  * accuracy — directional hit rate,
  * roc_auc  — ranking quality of the up/down probability,
  * ic       — Spearman rank correlation between the model's score and the
    realized forward return: the classic alpha metric. IC≈0 means no edge.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

__all__ = [
    "information_coefficient",
    "score_metrics",
    "fit_logistic",
    "fit_gbm",
    "fit_probe",
    "always_long_metrics",
]


def information_coefficient(scores: np.ndarray, fwd_returns: np.ndarray) -> float:
    """Spearman rank IC between a predictive score and realized forward return."""
    if np.std(scores) < 1e-12:
        return 0.0
    ic, _ = spearmanr(scores, fwd_returns)
    return float(ic) if np.isfinite(ic) else 0.0


def score_metrics(proba_up: np.ndarray, y: np.ndarray, fwd: np.ndarray) -> dict:
    """Accuracy / AUC / IC for a probability-of-up score, out-of-sample."""
    pred = (proba_up >= 0.5).astype(int)
    auc = float(roc_auc_score(y, proba_up)) if len(np.unique(y)) > 1 else float("nan")
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "roc_auc": auc,
        "ic": information_coefficient(proba_up, fwd),
    }


def fit_logistic(X_train: np.ndarray, y_train: np.ndarray) -> Pipeline:
    """Standardize (train-fit) + logistic regression on hand features."""
    clf = Pipeline([
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(max_iter=2000, C=1.0)),
    ])
    clf.fit(X_train, y_train)
    return clf


def fit_gbm(X_train: np.ndarray, y_train: np.ndarray, seed: int = 7) -> HistGradientBoostingClassifier:
    """Gradient-boosted trees on hand features — a strong non-linear baseline."""
    clf = HistGradientBoostingClassifier(
        max_iter=300, max_depth=4, learning_rate=0.05,
        l2_regularization=1.0, random_state=seed, early_stopping=True,
    )
    clf.fit(X_train, y_train)
    return clf


def fit_probe(Z_train: np.ndarray, y_train: np.ndarray) -> Pipeline:
    """Frozen-representation LINEAR probe (standardize train-fit + logistic)."""
    clf = Pipeline([
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(max_iter=2000, C=1.0)),
    ])
    clf.fit(Z_train, y_train)
    return clf


def always_long_metrics(y: np.ndarray, fwd: np.ndarray) -> dict:
    """The null model: predict 'up' with probability 1 for every sample."""
    proba = np.ones_like(y, dtype=float)
    return {
        "accuracy": float((y == 1).mean()),
        "roc_auc": float("nan"),  # undefined for a constant score
        "ic": 0.0,
    }
