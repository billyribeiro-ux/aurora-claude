"""
AURORA-SWING

Multi-Timeframe Synchronization Engine
======================================

Creates synchronized multi-timeframe sequences. This is critical because most ML
trading systems accidentally leak future information: every slice returned here
contains **only** bars at or before the decision timestamp.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

__all__ = ["TimeframeBuilder"]


class TimeframeBuilder:
    """Assemble aligned, leakage-free look-back windows across timeframes."""

    def __init__(
        self,
        daily_window: int = 128,
        four_hour_window: int = 256,
        hourly_window: int = 256,
    ) -> None:
        self.daily_window = daily_window
        self.four_hour_window = four_hour_window
        self.hourly_window = hourly_window

    def synchronize(
        self,
        daily: pd.DataFrame,
        four_hour: pd.DataFrame,
        hourly: pd.DataFrame,
        timestamp: datetime,
    ) -> dict[str, pd.DataFrame]:
        """Return the most recent window of each timeframe up to ``timestamp``.

        Each frame must be indexed by timestamp. Only rows with ``index <=
        timestamp`` are considered, so no future information can leak into the
        returned slices.
        """
        return {
            "daily": self._get_history(daily, timestamp, self.daily_window),
            "four_hour": self._get_history(four_hour, timestamp, self.four_hour_window),
            "hourly": self._get_history(hourly, timestamp, self.hourly_window),
        }

    @staticmethod
    def _get_history(
        dataframe: pd.DataFrame,
        timestamp: datetime,
        window: int,
    ) -> pd.DataFrame:
        past = dataframe[dataframe.index <= timestamp]
        return past.tail(window)
