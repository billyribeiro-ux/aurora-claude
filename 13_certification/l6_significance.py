"""LEVEL 6 — Statistical Significance Testing.

Bootstrap confidence intervals: block-bootstrap the daily returns to get a 95% CI
on annualized return and Sharpe. If the Sharpe CI straddles zero, the edge is not
statistically distinguishable from luck.

Probability of Backtest Overfitting (PBO) via CSCV (Combinatorially Symmetric
Cross-Validation, Bailey & López de Prado 2015): across many strategy
configurations, how often does the in-sample best rank below the OOS median?
A high PBO means the selection process is overfitting the backtest.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np

TRADING_DAYS = 252
EULER_GAMMA = 0.5772156649015329

__all__ = ["block_bootstrap_ci", "pbo_cscv", "deflated_sharpe_ratio", "run_level6"]


def _sharpe(r: np.ndarray) -> float:
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 1e-12 else 0.0


def block_bootstrap_ci(returns: np.ndarray, n_boot: int = 10000, block: int = 10, seed: int = 7) -> dict:
    """Moving-block bootstrap CI for annualized return and Sharpe."""
    rng = np.random.default_rng(seed)
    r = np.asarray(returns, dtype=float)
    T = len(r)
    if T < block * 2:
        return {"error": "series too short for bootstrap"}
    n_blocks = int(np.ceil(T / block))
    starts_pool = np.arange(0, T - block + 1)
    ann_rets, sharpes = np.empty(n_boot), np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.choice(starts_pool, size=n_blocks)
        sample = np.concatenate([r[s : s + block] for s in starts])[:T]
        eq = np.prod(1.0 + sample)
        ann_rets[i] = eq ** (TRADING_DAYS / T) - 1.0
        sharpes[i] = _sharpe(sample)
    return {
        "n_boot": n_boot,
        "ann_return_mean": round(float(ann_rets.mean()), 4),
        "ann_return_ci95": [round(float(np.percentile(ann_rets, 2.5)), 4),
                             round(float(np.percentile(ann_rets, 97.5)), 4)],
        "sharpe_mean": round(float(sharpes.mean()), 3),
        "sharpe_ci95": [round(float(np.percentile(sharpes, 2.5)), 3),
                        round(float(np.percentile(sharpes, 97.5)), 3)],
        "prob_sharpe_positive": round(float((sharpes > 0).mean()), 4),
    }


def pbo_cscv(M: np.ndarray, S: int = 10) -> dict:
    """PBO via CSCV. M is (T observations x N configurations) of returns."""
    T, N = M.shape
    if N < 2:
        return {"error": "need >=2 configurations for PBO"}
    S = S if S % 2 == 0 else S - 1
    bounds = np.linspace(0, T, S + 1).astype(int)
    blocks = [np.arange(bounds[i], bounds[i + 1]) for i in range(S)]

    logits = []
    for combo in combinations(range(S), S // 2):
        is_idx = np.concatenate([blocks[b] for b in combo])
        oos_idx = np.concatenate([blocks[b] for b in range(S) if b not in combo])
        is_perf = np.array([_sharpe(M[is_idx, n]) for n in range(N)])
        oos_perf = np.array([_sharpe(M[oos_idx, n]) for n in range(N)])
        n_star = int(np.argmax(is_perf))
        # Relative rank of the IS-best among OOS performances (1=best..N=worst→ω→1).
        rank = float((oos_perf <= oos_perf[n_star]).sum())  # how many it beats OOS
        omega = rank / (N + 1)
        omega = min(max(omega, 1e-6), 1 - 1e-6)
        logits.append(np.log(omega / (1 - omega)))
    logits = np.asarray(logits)
    pbo = float((logits <= 0).mean())  # IS-best falls below OOS median
    return {
        "pbo": round(pbo, 4),
        "n_configs": int(N),
        "n_splits": len(logits),
        "S": S,
        "interpretation": ("low overfitting risk" if pbo < 0.2
                           else "moderate" if pbo < 0.5 else "high overfitting risk"),
    }


def deflated_sharpe_ratio(returns: np.ndarray, trial_sharpes: np.ndarray) -> dict:
    """Deflated Sharpe Ratio (Bailey & López de Prado, 2014).

    Corrects the observed Sharpe for (a) selection across N strategy trials and
    (b) non-normality (skew/kurtosis) of the return series. Returns the
    probability that the TRUE Sharpe exceeds 0 after both corrections; the
    conventional significance bar is DSR > 0.95.

    All Sharpes here are PER-PERIOD (non-annualized), as the derivation requires.
    """
    from scipy.stats import norm, kurtosis, skew

    r = np.asarray(returns, dtype=float)
    T = len(r)
    sd = r.std(ddof=1)
    if T < 30 or sd < 1e-12:
        return {"error": "series too short or degenerate for DSR"}
    sr = float(r.mean() / sd)                       # per-period observed Sharpe
    g3 = float(skew(r))
    g4 = float(kurtosis(r, fisher=False))           # non-excess (normal = 3)

    trials = np.asarray(trial_sharpes, dtype=float)
    trials = trials[np.isfinite(trials)]
    N = len(trials)
    v = float(trials.var(ddof=1)) if N >= 2 else 0.0
    if N >= 2 and v > 0:
        # Expected maximum Sharpe across N zero-skill trials (E[max of N normals]).
        sr0 = float(np.sqrt(v) * ((1 - EULER_GAMMA) * norm.ppf(1 - 1 / N)
                                  + EULER_GAMMA * norm.ppf(1 - 1 / (N * np.e))))
    else:
        sr0 = 0.0                                   # reduces to the plain PSR

    denom_sq = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr ** 2
    denom = float(np.sqrt(max(denom_sq, 1e-12)))
    z = (sr - sr0) * np.sqrt(T - 1) / denom
    dsr = float(norm.cdf(z))
    return {
        "observed_sharpe_ann": round(sr * np.sqrt(TRADING_DAYS), 3),
        "expected_max_null_sharpe_ann": round(sr0 * np.sqrt(TRADING_DAYS), 3),
        "n_trials": int(N),
        "skew": round(g3, 3),
        "kurtosis": round(g4, 3),
        "dsr": round(dsr, 4),
        "significant": bool(dsr > 0.95),
    }


def run_level6(primary_returns: np.ndarray, config_matrix: np.ndarray,
               config_names: list[str], seed: int = 7) -> dict:
    ci = block_bootstrap_ci(primary_returns, seed=seed)
    pbo = pbo_cscv(config_matrix)
    # Per-period Sharpes of every configuration tried = the trial family for DSR.
    trial_srs = np.array([
        (config_matrix[:, n].mean() / config_matrix[:, n].std(ddof=1))
        if config_matrix[:, n].std(ddof=1) > 1e-12 else 0.0
        for n in range(config_matrix.shape[1])
    ])
    dsr = deflated_sharpe_ratio(primary_returns, trial_srs)
    sharpe_lb = ci.get("sharpe_ci95", [0, 0])[0]
    passed = bool(sharpe_lb > 0 and pbo.get("pbo", 1.0) < 0.5
                  and dsr.get("significant", False))
    return {
        "level": 6,
        "name": "Statistical Significance Testing",
        "bootstrap_ci": ci,
        "pbo_cscv": pbo,
        "deflated_sharpe": dsr,
        "config_names": config_names,
        "passed": passed,
    }
