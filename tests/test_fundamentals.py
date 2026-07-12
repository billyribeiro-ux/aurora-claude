"""Module 15 — fundamental factor leakage safety (no network)."""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

M15 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "15_fundamentals")
if M15 not in sys.path:
    sys.path.insert(0, M15)

from fundamental_factors import FUND_FACTORS, LAG_DAYS, build_factor_frame  # noqa: E402


def test_availability_lag_applied() -> None:
    """A quarter's factors become available exactly LAG_DAYS after period-end."""
    recs = [{"date": "2020-03-31", "period": "Q1", "earningsYield": 0.05, "marketCap": 1e11},
            {"date": "2020-06-30", "period": "Q2", "earningsYield": 0.04, "marketCap": 1.1e11}]
    fr = build_factor_frame(recs)
    assert fr is not None and len(fr) == 2
    expected = pd.Timestamp("2020-03-31") + pd.Timedelta(days=LAG_DAYS)
    assert fr["available_date"].iloc[0] == expected
    assert set(FUND_FACTORS).issubset(fr.columns)


def test_asof_merge_has_no_lookahead() -> None:
    """merge_asof(backward) must never attach a report before its available date."""
    recs = [{"date": "2021-12-31", "period": "Q4", "earningsYield": 0.06, "marketCap": 5e10}]
    fr = build_factor_frame(recs)
    avail = fr["available_date"].iloc[0]  # 2021-12-31 + 90d ≈ 2022-03-31

    daily = pd.DataFrame({"date": pd.bdate_range("2022-01-03", "2022-06-30")}).set_index("date")
    left = daily.reset_index()
    merged = pd.merge_asof(left.sort_values("date"), fr.sort_values("available_date"),
                           left_on="date", right_on="available_date", direction="backward")
    merged = merged.set_index("date")
    before = merged.loc[merged.index < avail, "f_earnings_yield"]
    after = merged.loc[merged.index >= avail, "f_earnings_yield"]
    assert before.isna().all()             # nothing known before it was public
    assert (after == 0.06).all()           # available from its release date on


def test_factor_orientation_higher_is_better() -> None:
    """EV/EBITDA and net-debt factors are inverted so higher = more attractive."""
    recs = [{"date": "2020-03-31", "evToEBITDA": 20.0, "netDebtToEBITDA": 3.0, "marketCap": 1e11}]
    fr = build_factor_frame(recs)
    assert fr["f_ev_ebitda_inv"].iloc[0] == -20.0
    assert fr["f_net_debt_ebitda_inv"].iloc[0] == -3.0
    assert fr["f_size"].iloc[0] == -np.log(1e11)
