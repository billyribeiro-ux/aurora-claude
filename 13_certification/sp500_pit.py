"""Point-in-time S&P 500 membership — the foundation of survivorship-bias control.

Reconstructs which tickers were index members on any past date by taking the
CURRENT constituents and replaying the historical add/remove event log backwards.
A name is investable in the backtest only while it was actually a member, and the
pool of "ever-members" explicitly includes companies that were later removed,
acquired or delisted — the very names a survivor-only universe omits.

Data source: FMP stable `sp500-constituent` and `historical-sp500-constituent`.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
CACHE = MODULE_DIR / "artifacts" / "sp500"
BASE = "https://financialmodelingprep.com/stable"

__all__ = ["MembershipTimeline", "build_timeline", "get_api_key"]


def get_api_key() -> str | None:
    key = os.environ.get("FMP_API_KEY")
    if key and key.strip():
        return key.strip()
    env = MODULE_DIR.parent / "frontend" / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("FMP_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


def _get(url: str, tries: int = 5):
    delay = 2.0
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(delay); delay *= 2; continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < tries - 1:
                time.sleep(delay); delay *= 2; continue
            raise
    return None


def _cached(name: str, url: str, key: str):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    if path.exists():
        return json.loads(path.read_text())
    data = _get(url)
    path.write_text(json.dumps(data))
    return data


def _parse_date(s: str) -> str | None:
    """FMP mixes ISO and 'June 29, 2026' formats; normalize to YYYY-MM-DD."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


@dataclass
class MembershipTimeline:
    """Per-ticker membership intervals [start, end] (end=None means still a member)."""
    intervals: dict[str, list[tuple[str, str | None]]] = field(default_factory=dict)
    current: set[str] = field(default_factory=set)

    def _add_interval(self, sym: str, start: str | None, end: str | None) -> None:
        self.intervals.setdefault(sym, []).append((start, end))

    def is_member(self, sym: str, date: str) -> bool:
        """Was `sym` an index member on `date`? (fast per-symbol interval check)"""
        for start, end in self.intervals.get(sym, []):
            lo = start or "0000-00-00"
            hi = end or "9999-12-31"
            if lo <= date < hi:
                return True
        return False

    def members_on(self, date: str) -> set[str]:
        out = set()
        for sym, ivs in self.intervals.items():
            for start, end in ivs:
                lo = start or "0000-00-00"
                hi = end or "9999-12-31"
                if lo <= date < hi or (end is None and (start is None or start <= date)):
                    out.add(sym); break
        return out

    def ever_members(self, start: str, end: str) -> set[str]:
        out = set()
        for sym, ivs in self.intervals.items():
            for s, e in ivs:
                s2 = s or "0000-00-00"
                e2 = e or "9999-12-31"
                if s2 <= end and e2 >= start:  # interval overlaps [start,end]
                    out.add(sym); break
        return out


def reconstruct_from_events(current: set[str], events: list[dict]) -> MembershipTimeline:
    """Pure reconstruction: replay normalized change events backward from `current`.

    Each event is ``{date, added, removed}``. Walking newest→oldest, an added
    ticker's current stint STARTED at that date; a removed ticker's stint ENDED
    there (and reopens further back). No network — unit-testable.
    """
    tl = MembershipTimeline()
    tl.current = set(current)
    evs = sorted(events, key=lambda e: e["date"], reverse=True)

    open_end: dict[str, str | None] = {s: None for s in current}  # current: open-ended
    for e in evs:
        d, added, removed = e["date"], e.get("added", ""), e.get("removed", "")
        if added:
            end = open_end.pop(added, None)
            tl._add_interval(added, d, end)     # this stint started at d
        if removed:
            if removed in open_end:             # re-added later; close the newer stint
                tl._add_interval(removed, d, open_end.pop(removed))
            open_end[removed] = d               # stint ends at d; start found earlier
    for sym, end in open_end.items():
        tl._add_interval(sym, None, end)        # member since before the window
    return tl


def build_timeline(api_key: str, window_start: str = "2015-01-01") -> MembershipTimeline:
    """Fetch current + historical constituents and reconstruct the membership timeline."""
    current = _cached("current_constituents.json", f"{BASE}/sp500-constituent?apikey={api_key}", api_key)
    events = _cached("historical_constituents.json", f"{BASE}/historical-sp500-constituent?apikey={api_key}", api_key)

    cur = {c["symbol"] for c in current if c.get("symbol")}
    norm = []
    for e in events:
        d = _parse_date(e.get("date") or e.get("dateAdded"))
        if d:
            norm.append({"date": d, "added": (e.get("symbol") or "").strip(),
                         "removed": (e.get("removedTicker") or "").strip()})
    return reconstruct_from_events(cur, norm)
