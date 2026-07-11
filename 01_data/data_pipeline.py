"""
AURORA-SWING

Market Data Pipeline
====================

Unified ingestion pipeline. Handles equities, ETFs and market context, prepares
multi-timeframe data and normalizes it for the foundation model.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf
from sklearn.preprocessing import StandardScaler

from .feature_engineering import FeatureEngineer

__all__ = ["MarketDataPipeline"]


class MarketDataPipeline:
    """Download, feature-engineer, normalize and persist market data."""

    def __init__(self) -> None:
        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()

    def download_symbol(
        self,
        symbol: str,
        period: str = "10y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Download adjusted OHLCV for ``symbol`` with lower-cased columns."""
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
        )
        # yfinance can return a MultiIndex when several tickers are requested;
        # flatten to the price field for a single-symbol download.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df

    def build_dataset(self, symbols: list[str]) -> dict[str, pd.DataFrame]:
        """Download and feature-engineer each symbol into a feature frame."""
        datasets: dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            raw = self.download_symbol(symbol)
            datasets[symbol] = self.feature_engineer.transform(raw)
        return datasets

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standard-scale all numeric columns, preserving the index."""
        numeric = df.select_dtypes(include="number")
        scaled = self.scaler.fit_transform(numeric)
        return pd.DataFrame(scaled, columns=numeric.columns, index=df.index)

    @staticmethod
    def save(df: pd.DataFrame, path: str) -> None:
        """Persist ``df`` to Parquet, creating parent directories as needed."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path)
