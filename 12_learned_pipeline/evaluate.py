"""Integrity checks and economic-evidence analysis.

Two things a real quant demands before believing an edge:

  1. **Label-permutation test** — retrain on SHUFFLED labels. If the pipeline
     were leaking future information, a model could still "predict" the shuffled
     labels out-of-sample. A leakage-free pipeline collapses to AUC≈0.5, IC≈0.
     This is the falsification test for the whole no-leakage claim.

  2. **Quantile / long-short analysis** — sort test samples by the model's score
     and bucket the realized forward returns. A genuine signal makes the buckets
     monotonic: high-score names really do earn more than low-score names. The
     top-minus-bottom spread is the tradable edge, before costs.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from models import information_coefficient

__all__ = ["permutation_null", "quantile_analysis"]


def permutation_null(
    fit_fn: Callable,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    fwd_test: np.ndarray,
    real_ic: float,
    n_perm: int = 12,
    seed: int = 7,
) -> dict:
    """Empirical significance of ``real_ic`` against a shuffled-label null.

    Retrains the model ``n_perm`` times on SHUFFLED train labels and records the
    out-of-sample IC each time. This builds the null distribution of IC given the
    (heavily overlapping, cross-sectionally correlated) sample structure — which
    is far wider than iid theory implies. A single permutation is noise; the
    distribution is the honest yardstick.

    Returns the null mean/std and a one-sided p-value: the fraction of null runs
    whose IC is at least as extreme (same sign) as the real model's IC.
    """
    rng = np.random.default_rng(seed)
    null_ics = []
    for _ in range(n_perm):
        y_shuf = y_train.copy()
        rng.shuffle(y_shuf)
        clf = fit_fn(X_train, y_shuf)
        proba = clf.predict_proba(X_test)[:, 1]
        null_ics.append(information_coefficient(proba, fwd_test))
    null = np.asarray(null_ics)
    if real_ic >= 0:
        p = float((null >= real_ic).mean())
    else:
        p = float((null <= real_ic).mean())
    return {
        "real_ic": float(real_ic),
        "null_ic_mean": float(null.mean()),
        "null_ic_std": float(null.std()),
        "null_ic_p95_abs": float(np.percentile(np.abs(null), 95)),
        "p_value": p,
        "significant": bool(p < 0.05 and abs(real_ic) > np.percentile(np.abs(null), 95)),
        "n_perm": n_perm,
    }


def quantile_analysis(scores: np.ndarray, fwd: np.ndarray, n_buckets: int = 5) -> dict:
    """Bucket realized forward returns by predicted score; report monotonicity."""
    order = np.argsort(scores)
    buckets = np.array_split(order, n_buckets)
    means = [float(fwd[b].mean()) for b in buckets]
    hit = [float((fwd[b] > 0).mean()) for b in buckets]
    # Is the sequence of bucket means non-decreasing (a monotone signal)?
    monotone = all(means[i] <= means[i + 1] + 1e-9 for i in range(len(means) - 1))
    return {
        "bucket_mean_fwd": means,          # low-score → high-score
        "bucket_hit_rate": hit,
        "long_short_spread": float(means[-1] - means[0]),
        "monotone_increasing": bool(monotone),
        "n_buckets": n_buckets,
    }
