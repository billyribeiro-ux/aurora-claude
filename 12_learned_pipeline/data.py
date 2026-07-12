"""Real market-data acquisition for the learned pipeline.

Pulls daily OHLCV from the Financial Modeling Prep *stable* API and caches each
symbol to ``artifacts/data/<SYMBOL>.csv`` so training is reproducible and
offline after the first run. The API key is read from the environment
(``FMP_API_KEY``) or, as a convenience for local runs, from ``frontend/.env`` —
it is never hard-coded and never written to disk.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

MODULE_DIR = Path(__file__).resolve().parent
DATA_DIR = MODULE_DIR / "artifacts" / "data"
REPO_ROOT = MODULE_DIR.parent
BASE = "https://financialmodelingprep.com/stable"

__all__ = ["get_api_key", "fetch_symbol", "load_or_fetch", "load_universe"]


def get_api_key() -> str | None:
    """Resolve the FMP key from the environment or frontend/.env (never logged)."""
    key = os.environ.get("FMP_API_KEY")
    if key and key.strip():
        return key.strip()
    env_path = REPO_ROOT / "frontend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("FMP_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


def _get(url: str, tries: int = 5) -> list | dict | None:
    """GET JSON with exponential backoff on transient failures / rate limits."""
    delay = 2.0
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=40) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return None


def fetch_symbol(symbol: str, start: str, end: str, api_key: str) -> pd.DataFrame:
    """Fetch chronological daily OHLCV for one symbol from FMP (stable)."""
    url = (
        f"{BASE}/historical-price-eod/full?symbol={symbol}"
        f"&from={start}&to={end}&apikey={api_key}"
    )
    rows = _get(url)
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"no data returned for {symbol}")
    df = pd.DataFrame(rows)
    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)  # oldest -> newest
    return df


def load_or_fetch(
    symbol: str, start: str, end: str, api_key: str | None, refresh: bool = False
) -> pd.DataFrame:
    """Return cached CSV for ``symbol`` or fetch + cache it if absent."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{symbol}.csv"
    if path.exists() and not refresh:
        df = pd.read_csv(path, parse_dates=["date"])
        return df.sort_values("date").reset_index(drop=True)
    if not api_key:
        raise RuntimeError(
            f"{symbol} not cached and no FMP_API_KEY available to fetch it"
        )
    df = fetch_symbol(symbol, start, end, api_key)
    df.to_csv(path, index=False)
    return df


def load_universe(
    symbols: list[str],
    start: str,
    end: str,
    api_key: str | None,
    refresh: bool = False,
    pause: float = 0.4,
) -> dict[str, pd.DataFrame]:
    """Load (from cache or FMP) every symbol; skip any that fail, report which."""
    out: dict[str, pd.DataFrame] = {}
    for i, sym in enumerate(symbols):
        try:
            df = load_or_fetch(sym, start, end, api_key, refresh=refresh)
            if len(df) < 300:
                print(f"  [data] {sym}: only {len(df)} rows — skipping")
                continue
            out[sym] = df
            print(f"  [data] {sym}: {len(df)} rows {df['date'].iloc[0].date()} -> {df['date'].iloc[-1].date()}")
        except Exception as exc:  # noqa: BLE001 — report and continue
            print(f"  [data] {sym}: FAILED ({exc})")
        if api_key and not (DATA_DIR / f"{sym}.csv").exists():
            time.sleep(pause)
    return out
