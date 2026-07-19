"""Multi-year walk-forward robustness — no single lucky split.

Expanding-window, sequential one-year test folds on the survivorship-free
universe: train on everything before year Y (with the usual label embargo), test
on year Y alone — for Y = 2019 … 2026. Each fold reports out-of-sample IC and the
long/short strategy's Sharpe, so performance is visible regime by regime
(2019 bull, 2020 COVID crash, 2022 bear, 2023-25 recovery) and weakness cannot
hide behind one averaged number.

Usage:  python walkforward.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
M12, M13 = HERE.parent / "12_learned_pipeline", HERE.parent / "13_certification"
for p in (str(HERE), str(M12), str(M13)):
    if p not in sys.path:
        sys.path.insert(0, p)

from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402

from alpha_research import build_rich_pit  # noqa: E402
from metrics import perf_metrics  # noqa: E402
from panel import load_panel  # noqa: E402
from sp500_pit import build_timeline, get_api_key  # noqa: E402
from strategy import build_long_short  # noqa: E402

ARTIFACTS = HERE / "artifacts"
SEED, HORIZON = 7, 10
FOLD_YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]


def _ic(s, f):
    if np.std(s) < 1e-12:
        return 0.0
    ic, _ = spearmanr(s, f)
    return float(ic) if np.isfinite(ic) else 0.0


def _panel_scores(proba, dates, syms, mask):
    df = pd.DataFrame({"date": pd.to_datetime(dates[mask]), "sym": syms[mask], "score": proba[mask]})
    return df.pivot_table(index="date", columns="sym", values="score", aggfunc="mean")


def main() -> dict:
    t0 = time.time()
    print("[wf] building survivorship-free rank dataset (once) ...")
    tl = build_timeline(get_api_key())
    d = build_rich_pit(tl)
    X = d["X"]
    dates, syms = d["dates"], d["syms"]
    used_syms = sorted(set(syms.tolist()))
    panel = load_panel(used_syms + ["SPY"], "2015-01-01", "2026-07-10")

    folds = []
    for year in FOLD_YEARS:
        y0 = np.datetime64(f"{year}-01-01")
        y1 = np.datetime64(f"{year + 1}-01-01")
        embargo = y0 - np.timedelta64(int(HORIZON * 1.5), "D")
        tr = dates < embargo                      # expanding window, label-embargoed
        te = (dates >= y0) & (dates < y1)
        if tr.sum() < 50_000 or te.sum() < 10_000:
            continue
        clf = HistGradientBoostingClassifier(
            max_iter=300, max_depth=5, learning_rate=0.05, l2_regularization=1.0,
            random_state=SEED, early_stopping=True).fit(X[tr], d["y"][tr])
        proba = clf.predict_proba(X)[:, 1]
        ic = _ic(proba[te], d["fwd_xs"][te])

        te_start = str(pd.Timestamp(dates[te].min()).date())
        te_end = str(pd.Timestamp(dates[te].max()).date())
        sp = panel.slice(te_start, te_end)
        strat = build_long_short(_panel_scores(proba, dates, syms, te), sp, HORIZON, quantile=0.2)
        m = perf_metrics(strat.daily_returns)
        spy = perf_metrics(panel.spy_returns(te_start, te_end))
        folds.append({"year": year, "train_samples": int(tr.sum()), "test_samples": int(te.sum()),
                      "oos_ic": round(ic, 4), "strategy_sharpe": round(m.sharpe, 3),
                      "strategy_return": round(m.total_return, 4),
                      "strategy_maxdd": round(m.max_drawdown, 4),
                      "spy_sharpe": round(spy.sharpe, 3)})
        print(f"  [wf] {year}: IC {ic:+.4f}  L/S Sharpe {m.sharpe:+.2f}  SPY {spy.sharpe:+.2f}")

    ics = [f["oos_ic"] for f in folds]
    shs = [f["strategy_sharpe"] for f in folds]
    result = {
        "meta": {"folds": len(folds), "samples": d["n"], "symbols": d["used"],
                 "delisted_included": d["deaths"], "horizon": HORIZON, "seed": SEED,
                 "runtime_seconds": round(time.time() - t0, 1)},
        "folds": folds,
        "summary": {
            "mean_oos_ic": round(float(np.mean(ics)), 4),
            "ic_positive_years": int(sum(i > 0 for i in ics)),
            "mean_strategy_sharpe": round(float(np.mean(shs)), 3),
            "sharpe_positive_years": int(sum(s > 0 for s in shs)),
            "worst_year_sharpe": round(float(np.min(shs)), 3),
        },
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "walkforward.json").write_text(json.dumps(result, indent=2, default=float))
    (ARTIFACTS / "WALKFORWARD.md").write_text(render(result))
    print(f"\nDONE in {result['meta']['runtime_seconds']}s → artifacts/WALKFORWARD.md")
    return result


def render(r: dict) -> str:
    s = r["summary"]
    lines = [
        "# AURORA-SWING — Multi-Year Walk-Forward Robustness (Survivorship-Free)",
        "",
        f"*Expanding-window, one-year sequential test folds · {r['meta']['samples']:,} samples · "
        f"{r['meta']['symbols']} symbols ({r['meta']['delisted_included']} delisted incl.) · "
        f"{r['meta']['runtime_seconds']}s.*",
        "",
        "Every year is a true out-of-sample fold (train strictly before, label-embargoed).",
        "",
        "| Year | Train n | OOS IC | L/S Sharpe | L/S Return | L/S MaxDD | SPY Sharpe |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in r["folds"]:
        lines.append(f"| {f['year']} | {f['train_samples']:,} | {f['oos_ic']:+.4f} | "
                     f"{f['strategy_sharpe']:+.2f} | {f['strategy_return']:+.3f} | "
                     f"{f['strategy_maxdd']:+.3f} | {f['spy_sharpe']:+.2f} |")
    lines += [
        "",
        f"**Summary:** mean OOS IC {s['mean_oos_ic']:+.4f} "
        f"({s['ic_positive_years']}/{r['meta']['folds']} years positive) · "
        f"mean L/S Sharpe {s['mean_strategy_sharpe']:+.2f} "
        f"({s['sharpe_positive_years']}/{r['meta']['folds']} positive) · "
        f"worst year {s['worst_year_sharpe']:+.2f}.",
        "",
        "Read: a real edge shows positive IC in most years and no catastrophic year. "
        "Reported as-measured, survivorship-free. Reproducible via `python walkforward.py`.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
