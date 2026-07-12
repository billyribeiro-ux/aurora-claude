"""Liquid US-equity + ETF universe for the learned-pipeline experiments.

A cross-sectional set (mega-caps across every sector + two broad ETFs) so the
encoder sees genuinely different regimes and the probe has cross-sectional
signal to learn, not one instrument's idiosyncrasies.
"""

from __future__ import annotations

UNIVERSE: list[str] = [
    # Broad market
    "SPY", "QQQ",
    # Technology
    "AAPL", "MSFT", "NVDA", "ADBE", "CRM", "ORCL", "CSCO", "INTC", "AMD", "QCOM",
    # Communication / consumer internet
    "GOOGL", "META", "NFLX", "DIS",
    # Consumer
    "AMZN", "TSLA", "HD", "WMT", "PG", "KO", "PEP",
    # Financials
    "JPM", "BAC", "V", "MA",
    # Health care
    "UNH", "JNJ", "PFE",
    # Energy
    "XOM", "CVX",
]

__all__ = ["UNIVERSE"]
