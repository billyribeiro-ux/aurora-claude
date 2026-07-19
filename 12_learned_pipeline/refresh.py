"""Nightly incremental EOD refresh for every cached symbol.

Appends the latest daily bars to each existing CSV in the cache (re-fetching a
small overlap window and de-duplicating by date), so the certification and
research runs always see current data. Designed for the 24/7 autonomous loop:
gentle pacing, hard-honest reporting, and a non-zero exit if no key is available.

Usage:  python refresh.py            # refresh all cached symbols
        python refresh.py SPY NVDA   # refresh a subset
"""

from __future__ import annotations

import sys
import time
from datetime import date, timedelta

import pandas as pd

from data import DATA_DIR, fetch_symbol, get_api_key

OVERLAP_DAYS = 7  # re-fetch a week of overlap to heal any partial prior day


def refresh_symbol(sym: str, key: str) -> tuple[int, str]:
    """Fetch bars newer than the cache tail.

    Returns (rows_added, status) where status ∈ {ok, current, failed:<reason>} —
    a 24/7 loop must be able to distinguish "no new data" from "provider down".
    """
    path = DATA_DIR / f"{sym}.csv"
    if not path.exists():
        return 0, "failed:not-cached"
    old = pd.read_csv(path, parse_dates=["date"]).sort_values("date")
    last = old["date"].max().date()
    start = (last - timedelta(days=OVERLAP_DAYS)).isoformat()
    end = date.today().isoformat()
    if start >= end:
        return 0, "current"
    try:
        new = fetch_symbol(sym, start, end, key)
    except Exception as exc:  # noqa: BLE001 — reported, never swallowed silently
        return 0, f"failed:{str(exc)[:60]}"
    merged = (
        pd.concat([old, new])
        .drop_duplicates("date", keep="last")
        .sort_values("date")
        .reset_index(drop=True)
    )
    added = len(merged) - len(old)
    if added > 0:
        merged.to_csv(path, index=False)
    return added, "ok"


def main() -> None:
    key = get_api_key()
    if not key:
        print("REFRESH ABORTED: no FMP_API_KEY available (env or frontend/.env).")
        raise SystemExit(2)
    symbols = sys.argv[1:] or sorted(p.stem for p in DATA_DIR.glob("*.csv"))
    print(f"[refresh] {len(symbols)} symbols ...")
    total, touched, failures = 0, 0, []
    for i, sym in enumerate(symbols):
        added, status = refresh_symbol(sym, key)
        if added > 0:
            total += added
            touched += 1
        if status.startswith("failed"):
            failures.append((sym, status))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(symbols)}  updated={touched} rows={total} failed={len(failures)}")
        time.sleep(0.2)
    print(f"DONE: {touched}/{len(symbols)} symbols updated, {total} new rows, "
          f"{len(failures)} failures.")
    if failures:
        print("failures (first 10):", failures[:10])
    # Exit non-zero when the provider blocked most of the run — the autonomous
    # loop treats that as "retry later", not "market had no new data".
    if len(failures) > len(symbols) * 0.5:
        print("REFRESH DEGRADED: majority of symbols failed (likely rate limit).")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
