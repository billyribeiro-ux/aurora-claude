"""Fetch quarterly key-metrics for the survivorship-free universe (cached).

One call per symbol. Leakage is handled downstream by only using a quarterly
record 90 days after its period-end date (conservative filing lag), so this
fetch just needs the raw per-period metrics + their period `date`.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "artifacts" / "keymetrics"
BASE = "https://financialmodelingprep.com/stable"
sys.path.insert(0, str(HERE.parent / "13_certification"))
from sp500_pit import build_timeline, get_api_key  # noqa: E402

FIELDS = [
    "date", "period", "earningsYield", "freeCashFlowYield", "evToEBITDA", "evToSales",
    "returnOnEquity", "returnOnInvestedCapital", "operatingReturnOnAssets",
    "incomeQuality", "netDebtToEBITDA", "currentRatio", "marketCap",
]


def _get(url, tries=5):
    delay = 2.0
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=50) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < tries - 1:
                time.sleep(delay); delay *= 2; continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if a < tries - 1:
                time.sleep(delay); delay *= 2; continue
            raise
    return None


def fetch_symbol(sym: str, key: str) -> int:
    path = CACHE / f"{sym}.json"
    if path.exists():
        return -1
    url = f"{BASE}/key-metrics?symbol={sym}&period=quarter&limit=60&apikey={key}"
    data = _get(url)
    if not isinstance(data, list):
        return 0
    slim = [{k: rec.get(k) for k in FIELDS} for rec in data]
    path.write_text(json.dumps(slim))
    return len(slim)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    key = get_api_key()
    tl = build_timeline(key)
    pool = sorted(tl.ever_members("2015-01-01", "2026-07-10"))
    print(f"fetching key-metrics for {len(pool)} symbols ...")
    ok, empty, fail = 0, 0, []
    for i, sym in enumerate(pool):
        try:
            n = fetch_symbol(sym, key)
            if n == 0:
                empty += 1
            else:
                ok += 1
        except Exception as e:
            fail.append((sym, str(e)[:24]))
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(pool)}  ok={ok} empty={empty} fail={len(fail)}")
        time.sleep(0.25)
    print(f"DONE ok={ok} empty={empty} fail={len(fail)}; fail sample {fail[:15]}")


if __name__ == "__main__":
    main()
