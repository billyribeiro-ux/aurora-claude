"""Aligned price/return panel built from the cached market data.

Loads the same on-disk CSVs Module 12 fetched and assembles a date x symbol
matrix of closes and simple daily returns, so the strategy and the baselines are
all measured on one consistent calendar.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

MODULE12 = Path(__file__).resolve().parent.parent / "12_learned_pipeline"
if str(MODULE12) not in sys.path:
    sys.path.insert(0, str(MODULE12))

__all__ = ["Panel", "load_panel"]


class Panel:
    def __init__(self, close: pd.DataFrame):
        self.close = close.sort_index()
        self.ret = self.close.pct_change()  # simple daily returns, date x symbol

    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.close.index

    def slice(self, start: str, end: str) -> "Panel":
        m = (self.close.index >= np.datetime64(start)) & (self.close.index <= np.datetime64(end))
        return Panel(self.close.loc[m])

    def spy_returns(self, start: str, end: str) -> np.ndarray:
        r = self.ret["SPY"].loc[
            (self.ret.index >= np.datetime64(start)) & (self.ret.index <= np.datetime64(end))
        ]
        return r.fillna(0.0).to_numpy()


def load_panel(symbols: list[str], start: str, end: str) -> Panel:
    """Assemble the close-price panel from Module 12's cached CSVs."""
    from data import DATA_DIR  # reuse the same cache location

    series = {}
    for sym in symbols:
        path = DATA_DIR / f"{sym}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
        series[sym] = df["close"]
    if not series:
        raise RuntimeError("no cached price data found — run Module 12 first")
    close = pd.DataFrame(series)
    close = close.loc[(close.index >= np.datetime64(start)) & (close.index <= np.datetime64(end))]
    return Panel(close)
