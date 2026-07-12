"""Leakage-safe point-in-time fundamental factors from cached key-metrics.

Each quarterly record is made available only ``LAG_DAYS`` after its period-end
date (a conservative filing lag — US large-caps file 10-Q within ~40 days, 10-K
within ~75), so a factor value at decision date D reflects only reports that were
public by D. An as-of merge attaches the latest-available quarter to each daily
observation. Factors are oriented so that HIGHER = more attractive (cheaper /
higher quality / safer), ready for cross-sectional rank-normalization.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent / "artifacts" / "keymetrics"
LAG_DAYS = 90

FUND_FACTORS = [
    "f_earnings_yield", "f_fcf_yield", "f_ev_ebitda_inv", "f_ev_sales_inv",
    "f_roe", "f_roic", "f_oroa", "f_income_quality",
    "f_net_debt_ebitda_inv", "f_current_ratio", "f_size",
]

__all__ = ["FUND_FACTORS", "build_factor_frame", "load_symbol_fundamentals",
           "attach_fundamentals", "coverage"]


def _num(v):
    return float(v) if isinstance(v, (int, float)) and np.isfinite(v) else np.nan


def build_factor_frame(recs: list) -> pd.DataFrame | None:
    """Pure: turn raw key-metrics records into a factor frame keyed by AVAILABLE
    date (period-end + LAG_DAYS). No IO — unit-testable for leakage safety."""
    rows = []
    for r in recs:
        d = r.get("date")
        if not d:
            continue
        try:
            avail = pd.Timestamp(d) + pd.Timedelta(days=LAG_DAYS)
        except Exception:
            continue
        mc = _num(r.get("marketCap"))
        rows.append({
            "available_date": avail,
            "f_earnings_yield": _num(r.get("earningsYield")),
            "f_fcf_yield": _num(r.get("freeCashFlowYield")),
            "f_ev_ebitda_inv": -_num(r.get("evToEBITDA")),
            "f_ev_sales_inv": -_num(r.get("evToSales")),
            "f_roe": _num(r.get("returnOnEquity")),
            "f_roic": _num(r.get("returnOnInvestedCapital")),
            "f_oroa": _num(r.get("operatingReturnOnAssets")),
            "f_income_quality": _num(r.get("incomeQuality")),
            "f_net_debt_ebitda_inv": -_num(r.get("netDebtToEBITDA")),
            "f_current_ratio": _num(r.get("currentRatio")),
            "f_size": -np.log(mc) if mc and mc > 0 else np.nan,
        })
    if not rows:
        return None
    df = pd.DataFrame(rows).dropna(subset=["available_date"]).sort_values("available_date")
    return df.drop_duplicates("available_date", keep="last").reset_index(drop=True)


def load_symbol_fundamentals(sym: str) -> pd.DataFrame | None:
    """Return factor time series indexed by AVAILABLE date (period-end + lag)."""
    path = CACHE / f"{sym}.json"
    if not path.exists():
        return None
    try:
        recs = json.loads(path.read_text())
    except Exception:
        return None
    return build_factor_frame(recs)


def attach_fundamentals(feat: pd.DataFrame, sym: str) -> pd.DataFrame:
    """As-of merge the latest PUBLIC fundamentals onto a daily feature frame.

    ``feat`` is indexed by date. Returns ``feat`` with FUND_FACTORS columns added
    (NaN where no report was yet public). No look-ahead: only records whose
    available_date <= the observation date are used.
    """
    fund = load_symbol_fundamentals(sym)
    base = feat.copy()
    if fund is None or fund.empty:
        for c in FUND_FACTORS:
            base[c] = np.nan
        return base
    left = base.reset_index().rename(columns={base.index.name or "index": "date"})
    if "date" not in left.columns:
        left = left.rename(columns={left.columns[0]: "date"})
    left["date"] = pd.to_datetime(left["date"])
    merged = pd.merge_asof(
        left.sort_values("date"), fund.sort_values("available_date"),
        left_on="date", right_on="available_date", direction="backward",
    )
    merged = merged.set_index("date")
    return merged.drop(columns=["available_date"], errors="ignore")


def coverage() -> dict:
    files = list(CACHE.glob("*.json"))
    return {"symbols_cached": len(files)}
