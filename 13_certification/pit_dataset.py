"""Point-in-time, survivorship-free dataset for the certification.

Unlike Module 12 (a fixed universe of current survivors), here a (symbol, date)
sample exists ONLY when the symbol was an actual S&P 500 member on that date, and
the pool includes every name that was ever a member in the window — including the
262 that were later removed, acquired or delisted. The cross-sectional label is
de-meaned across the names that were live members that day, so it measures
selection skill within the true, then-available universe.

Flat features only (no encoder sequences) — this pass isolates the survivorship
question, which is about the tradable universe, not the representation.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

MODULE12 = Path(__file__).resolve().parent.parent / "12_learned_pipeline"
if str(MODULE12) not in sys.path:
    sys.path.insert(0, str(MODULE12))

from dataset import FEATURE_COLS, FeatureEngineer  # noqa: E402  (Module 12)
from data import DATA_DIR  # noqa: E402

from sp500_pit import MembershipTimeline  # noqa: E402

__all__ = ["PitDataset", "build_pit_dataset"]


@dataclass
class PitDataset:
    X_flat: np.ndarray
    y_xs: np.ndarray
    fwd_xs: np.ndarray
    dates: np.ndarray
    label_dates: np.ndarray
    syms: np.ndarray
    train_mask: np.ndarray
    test_mask: np.ndarray
    feature_cols: list[str]
    n_symbols: int
    n_deaths_included: int

    def summary(self) -> dict:
        return {
            "samples": int(len(self.y_xs)),
            "train": int(self.train_mask.sum()),
            "test": int(self.test_mask.sum()),
            "symbols_used": self.n_symbols,
            "delisted_or_removed_included": self.n_deaths_included,
            "train_start": str(pd.Timestamp(self.dates[self.train_mask].min()).date()),
            "train_end": str(pd.Timestamp(self.dates[self.train_mask].max()).date()),
            "test_start": str(pd.Timestamp(self.dates[self.test_mask].min()).date()),
            "test_end": str(pd.Timestamp(self.dates[self.test_mask].max()).date()),
        }


def _load_close(sym: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{sym}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date")
    return df if len(df) > 60 else None


def build_pit_dataset(
    timeline: MembershipTimeline,
    start: str = "2015-01-01",
    end: str = "2026-07-10",
    horizon: int = 10,
    split_date: str = "2023-01-01",
    min_history: int = 60,
) -> PitDataset:
    pool = sorted(timeline.ever_members(start, end))
    current = timeline.current

    rows_X, ys_fwd, ds, lds, sy = [], [], [], [], []
    used, deaths = set(), set()
    for sym in pool:
        df = _load_close(sym)
        if df is None:
            continue
        feats = FeatureEngineer().transform(df.set_index("date"))
        if len(feats) <= horizon + 1:
            continue
        fmat = feats[FEATURE_COLS].to_numpy(np.float64)
        close = feats["close"].to_numpy(np.float64)
        idx = feats.index
        contributed = False
        for t in range(len(feats) - horizon):
            date = idx[t]
            dstr = str(date.date())
            if not timeline.is_member(sym, dstr):
                continue
            rows_X.append(fmat[t])
            ys_fwd.append(close[t + horizon] / close[t] - 1.0)
            ds.append(date.to_datetime64())
            lds.append(idx[t + horizon].to_datetime64())
            sy.append(sym)
            contributed = True
        if contributed:
            used.add(sym)
            if sym not in current:
                deaths.add(sym)

    X_flat = np.asarray(rows_X, dtype=np.float32)
    fwd = np.asarray(ys_fwd, dtype=np.float64)
    dates = np.asarray(ds)
    label_dates = np.asarray(lds)
    syms = np.asarray(sy)

    # Cross-sectional de-mean within each day's LIVE members.
    fwd_xs = np.empty_like(fwd)
    order = np.argsort(dates, kind="stable")
    d_sorted = dates[order]
    uniq, starts = np.unique(d_sorted, return_index=True)
    bounds = list(starts) + [len(dates)]
    for i in range(len(uniq)):
        blk = order[bounds[i]:bounds[i + 1]]
        fwd_xs[blk] = fwd[blk] - fwd[blk].mean()
    y_xs = (fwd_xs > 0).astype(np.int64)

    split = np.datetime64(split_date)
    train_mask = (dates < split) & (label_dates < split)
    test_mask = dates >= split

    return PitDataset(
        X_flat=X_flat, y_xs=y_xs, fwd_xs=fwd_xs, dates=dates, label_dates=label_dates,
        syms=syms, train_mask=train_mask, test_mask=test_mask,
        feature_cols=list(FEATURE_COLS), n_symbols=len(used), n_deaths_included=len(deaths),
    )
