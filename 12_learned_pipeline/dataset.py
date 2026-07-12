"""Leakage-safe supervised dataset construction for the learned pipeline.

Turns raw OHLCV into:
  * ``X_seq``  — (N, L, F) sequences of the last L days of engineered features
                 (input to the self-supervised encoder),
  * ``X_flat`` — (N, F) the decision-day feature vector (input to baselines),
  * ``y``      — (N,) binary label: did the forward H-day return exceed 0,
  * ``fwd``    — (N,) the continuous forward H-day return (for IC + trading sim),
  * ``dates`` / ``syms`` — provenance for every row.

Leakage guarantees (all enforced here, all tested):
  1. Features are computed by ``FeatureEngineer`` which only looks backwards.
  2. The label uses future bars (that is the prediction *target*, not leakage),
     but the WALK-FORWARD split applies a label-embargo: no training row's
     label window may overlap the test period. A training sample is kept only
     if BOTH its decision date AND its label date fall before the split.
  3. Feature standardization is fit on TRAIN ROWS ONLY (see scale_splits).
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

MODULE_DIR = Path(__file__).resolve().parent
REPO_ROOT = MODULE_DIR.parent

# Reuse the platform's leakage-free feature engineer (digit-prefixed dir → load by path).
_fe_spec = importlib.util.spec_from_file_location(
    "aurora_feature_engineering", REPO_ROOT / "01_data" / "feature_engineering.py"
)
assert _fe_spec and _fe_spec.loader
_fe_mod = importlib.util.module_from_spec(_fe_spec)
# Register before exec so @dataclass can resolve the module via sys.modules.
sys.modules["aurora_feature_engineering"] = _fe_mod
_fe_spec.loader.exec_module(_fe_mod)
FeatureEngineer = _fe_mod.FeatureEngineer

# The normalized, bounded feature subset the models consume (raw prices excluded).
FEATURE_COLS: list[str] = [
    "log_return",
    "atr_pct",
    "rsi",
    "volatility",
    "volume_zscore",
    "trend_strength",
    "high_low_range",
    "close_position",
]

__all__ = ["DatasetConfig", "Dataset", "build_dataset", "scale_splits", "FEATURE_COLS"]


@dataclass
class DatasetConfig:
    seq_len: int = 32          # days of history fed to the encoder
    horizon: int = 10          # forward trading days the label looks ahead
    split_date: str = "2023-01-01"  # walk-forward boundary (test = on/after)


@dataclass
class Dataset:
    X_seq: np.ndarray      # (N, L, F)
    X_flat: np.ndarray     # (N, F) decision-day features
    y: np.ndarray          # (N,) binary — absolute forward return > 0
    fwd: np.ndarray        # (N,) absolute forward return
    y_xs: np.ndarray       # (N,) binary — outperforms same-day cross-section
    fwd_xs: np.ndarray     # (N,) cross-sectionally de-meaned forward return
    dates: np.ndarray      # (N,) datetime64 — decision date
    label_dates: np.ndarray  # (N,) datetime64 — date the label resolves
    syms: np.ndarray       # (N,) symbol
    train_mask: np.ndarray  # (N,) bool
    test_mask: np.ndarray   # (N,) bool
    feature_cols: list[str]

    def summary(self) -> dict:
        return {
            "samples": int(len(self.y)),
            "train": int(self.train_mask.sum()),
            "test": int(self.test_mask.sum()),
            "features": self.feature_cols,
            "seq_len": int(self.X_seq.shape[1]),
            "abs_pos_rate_test": float(self.y[self.test_mask].mean()),
            "xs_pos_rate_test": float(self.y_xs[self.test_mask].mean()),
            "train_start": str(pd.Timestamp(self.dates[self.train_mask].min()).date())
            if self.train_mask.any() else None,
            "train_end": str(pd.Timestamp(self.dates[self.train_mask].max()).date())
            if self.train_mask.any() else None,
            "test_start": str(pd.Timestamp(self.dates[self.test_mask].min()).date())
            if self.test_mask.any() else None,
        }


def _one_symbol(sym: str, df: pd.DataFrame, cfg: DatasetConfig):
    """Build all (window, label) samples for a single symbol."""
    feats = FeatureEngineer().transform(df.set_index("date"))
    if len(feats) <= cfg.seq_len + cfg.horizon:
        return None
    fmat = feats[FEATURE_COLS].to_numpy(dtype=np.float64)
    close = feats["close"].to_numpy(dtype=np.float64)
    fdates = feats.index.to_numpy()  # datetime64
    n = len(feats)

    rows_seq, rows_flat, ys, fwds, ds, lds = [], [], [], [], [], []
    # t = decision day index; need seq_len history behind it and horizon ahead.
    for t in range(cfg.seq_len - 1, n - cfg.horizon):
        fwd_ret = close[t + cfg.horizon] / close[t] - 1.0
        rows_seq.append(fmat[t - cfg.seq_len + 1 : t + 1])
        rows_flat.append(fmat[t])
        ys.append(1 if fwd_ret > 0 else 0)
        fwds.append(fwd_ret)
        ds.append(fdates[t])
        lds.append(fdates[t + cfg.horizon])
    return (
        np.asarray(rows_seq), np.asarray(rows_flat), np.asarray(ys),
        np.asarray(fwds), np.asarray(ds), np.asarray(lds),
        np.array([sym] * len(ys)),
    )


def build_dataset(data: dict[str, pd.DataFrame], cfg: DatasetConfig | None = None) -> Dataset:
    cfg = cfg or DatasetConfig()
    parts = [p for p in (_one_symbol(s, d, cfg) for s, d in sorted(data.items())) if p]
    if not parts:
        raise RuntimeError("no usable samples built from the provided data")

    X_seq = np.concatenate([p[0] for p in parts]).astype(np.float32)
    X_flat = np.concatenate([p[1] for p in parts]).astype(np.float32)
    y = np.concatenate([p[2] for p in parts]).astype(np.int64)
    fwd = np.concatenate([p[3] for p in parts]).astype(np.float64)
    dates = np.concatenate([p[4] for p in parts])
    label_dates = np.concatenate([p[5] for p in parts])
    syms = np.concatenate([p[6] for p in parts])

    # Cross-sectional (market-neutral) target: de-mean each day's forward returns
    # across the universe, so the label isolates stock SELECTION from market drift.
    # Uses only same-date contemporaneous returns — it defines the target, and is
    # never fed back as a feature, so it introduces no look-ahead into the inputs.
    fwd_xs = np.empty_like(fwd)
    order = np.argsort(dates, kind="stable")
    d_sorted = dates[order]
    uniq, starts = np.unique(d_sorted, return_index=True)
    bounds = list(starts) + [len(dates)]
    for i in range(len(uniq)):
        idx = order[bounds[i] : bounds[i + 1]]
        fwd_xs[idx] = fwd[idx] - fwd[idx].mean()
    y_xs = (fwd_xs > 0).astype(np.int64)

    split = np.datetime64(cfg.split_date)
    # Train: decision AND label both strictly before the split (label-embargo).
    train_mask = (dates < split) & (label_dates < split)
    # Test: decision on/after the split (its history may precede it — that's fine,
    # history is past data; what matters is no train label enters the test period).
    test_mask = dates >= split

    return Dataset(
        X_seq=X_seq, X_flat=X_flat, y=y, fwd=fwd, y_xs=y_xs, fwd_xs=fwd_xs,
        dates=dates, label_dates=label_dates, syms=syms,
        train_mask=train_mask, test_mask=test_mask, feature_cols=list(FEATURE_COLS),
    )


def scale_splits(X_train: np.ndarray, X_test: np.ndarray):
    """Standardize using TRAIN statistics only (returns scaled train, test, stats)."""
    mu = X_train.reshape(-1, X_train.shape[-1]).mean(axis=0)
    sd = X_train.reshape(-1, X_train.shape[-1]).std(axis=0) + 1e-8
    return (X_train - mu) / sd, (X_test - mu) / sd, (mu, sd)
