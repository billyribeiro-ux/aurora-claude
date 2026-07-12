"""LEVEL 1 — Data Integrity Validation.

Runs BEFORE any model is trusted. Each check returns a verdict; the level gate is
the AND of the critical checks. Survivorship bias is treated as a first-class
check and, on the current fixed-universe design, it is reported as NOT CONTROLLED
— a disclosed limitation, not a hidden one. That honesty is the point of the
whole framework.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["run_level1"]


def _check(name: str, passed: bool, detail: str, critical: bool = True) -> dict:
    return {"check": name, "passed": bool(passed), "critical": critical, "detail": detail}


def run_level1(data: dict[str, pd.DataFrame], universe_is_current: bool = True) -> dict:
    checks: list[dict] = []

    # 1. Chronological ordering + no duplicate timestamps.
    ordering_ok, dup_ok = True, True
    for sym, df in data.items():
        d = pd.to_datetime(df["date"])
        if not d.is_monotonic_increasing:
            ordering_ok = False
        if d.duplicated().any():
            dup_ok = False
    checks.append(_check("timestamps_ordered", ordering_ok,
                         "all symbols strictly chronological" if ordering_ok else "out-of-order dates found"))
    checks.append(_check("no_duplicate_bars", dup_ok,
                         "no duplicate dates" if dup_ok else "duplicate dates found"))

    # 2. Missing data: NaNs in OHLCV.
    nan_syms = [s for s, df in data.items()
                if df[["open", "high", "low", "close", "volume"]].isna().any().any()]
    checks.append(_check("no_missing_ohlcv", len(nan_syms) == 0,
                         "no NaNs in OHLCV" if not nan_syms else f"NaNs in: {nan_syms}"))

    # 3. Corporate-action / split artifacts. Split-adjusted closes never contain
    #    the ~50-90% single-day gap an unadjusted split produces. We flag only
    #    moves > 60%: genuine earnings reactions can reach ~50% (e.g. AMD +52%
    #    Apr-2016, NFLX -35% Apr-2022) and must NOT be mistaken for split errors.
    #    A verified split (NVDA 10:1, 2024-06-10) appears smooth in this data.
    split_flags = {}
    for sym, df in data.items():
        r = df["close"].pct_change().abs()
        n_extreme = int((r > 0.60).sum())
        if n_extreme > 0:
            split_flags[sym] = n_extreme
    total_extreme = sum(split_flags.values())
    checks.append(_check("corporate_actions_adjusted", total_extreme == 0,
                         "split-adjusted closes — no split-like discontinuities (real earnings "
                         "moves up to ~50% retained)" if total_extreme == 0
                         else f"{total_extreme} split-like gaps (>60%) — check adjustment: {split_flags}"))

    # 4. OHLC sanity: high >= low, close within [low, high].
    ohlc_ok = all(
        bool((df["high"] >= df["low"]).all()
             and (df["close"] <= df["high"] + 1e-6).all()
             and (df["close"] >= df["low"] - 1e-6).all())
        for df in data.values()
    )
    checks.append(_check("ohlc_bounds_valid", ohlc_ok,
                         "high>=low and close in [low,high] for all bars" if ohlc_ok else "OHLC bound violations"))

    # 5. Survivorship bias — the honest one.
    surv_controlled = not universe_is_current
    checks.append(_check(
        "survivorship_bias_controlled", surv_controlled,
        "point-in-time constituents incl. delisted names"
        if surv_controlled else
        "NOT CONTROLLED: universe is fixed CURRENT constituents (2026 survivors) "
        "back-tested to 2015. This inflates results by excluding delisted names. "
        "Controlling it requires point-in-time index membership + delisted history.",
        critical=True,
    ))

    critical_fail = [c for c in checks if c["critical"] and not c["passed"]]
    return {
        "level": 1,
        "name": "Data Integrity Validation",
        "checks": checks,
        "passed": len(critical_fail) == 0,
        "failed_critical": [c["check"] for c in critical_fail],
    }
