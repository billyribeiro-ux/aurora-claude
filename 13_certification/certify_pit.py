"""Survivorship-free certification — the same gauntlet on a point-in-time universe.

Rebuilds the strategy on the true, then-available S&P 500 (including 260+ names
later removed/acquired/delisted, each tradable only while it was a member) and
re-runs Levels 1, 3, 4, 5, 6. Level 2 (representation quality) is universe-
agnostic and already certified on Module 12, so it is not repeated here.

The headline is the BEFORE/AFTER: how much of the survivor-only strategy's
apparent edge was survivorship bias.

Usage:  python certify_pit.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MODULE12 = HERE.parent / "12_learned_pipeline"
for p in (str(HERE), str(MODULE12)):
    if p not in sys.path:
        sys.path.insert(0, p)

from data import DATA_DIR  # noqa: E402
from models import fit_logistic  # noqa: E402

import baselines as base_mod  # noqa: E402
from l1_data_integrity import run_level1  # noqa: E402
from l4_regime import run_level4  # noqa: E402
from l5_montecarlo import run_level5  # noqa: E402
from l6_significance import run_level6  # noqa: E402
from metrics import perf_metrics, trade_stats  # noqa: E402
from panel import load_panel  # noqa: E402
from pit_dataset import build_pit_dataset  # noqa: E402
from sp500_pit import build_timeline, get_api_key  # noqa: E402
from strategy import build_long_short  # noqa: E402

ARTIFACTS = HERE / "artifacts"
SEED = 7
START, END = "2015-01-01", "2026-07-10"


def _score_panel(proba, dates, syms, mask) -> pd.DataFrame:
    df = pd.DataFrame({"date": pd.to_datetime(dates[mask]), "sym": syms[mask], "score": proba[mask]})
    return df.pivot_table(index="date", columns="sym", values="score", aggfunc="mean")


def _load_data_dict(symbols: list[str]) -> dict:
    out = {}
    for s in symbols:
        p = DATA_DIR / f"{s}.csv"
        if p.exists():
            df = pd.read_csv(p, parse_dates=["date"]).sort_values("date")
            if len(df) > 60:
                out[s] = df
    return out


def main() -> dict:
    t0 = time.time()
    print("[pit] building point-in-time membership + dataset ...")
    tl = build_timeline(get_api_key())
    ds = build_pit_dataset(tl, START, END)
    tr, te = ds.train_mask, ds.test_mask
    oos_start = str(pd.Timestamp(ds.dates[te].min()).date())
    oos_end = str(pd.Timestamp(ds.dates[te].max()).date())
    horizon = 10
    used_syms = sorted(set(ds.syms.tolist()))
    print(f"[pit] {ds.summary()}")

    # ---- L1 (survivorship now controlled) ---------------------------------
    print("[L1] data integrity on point-in-time universe ...")
    L1 = run_level1(_load_data_dict(used_syms), universe_is_current=False,
                    delisted_included=ds.n_deaths_included)

    # ---- signal + strategy on the PIT universe ----------------------------
    print("[fit] logistic signal + PIT long/short strategy ...")
    logit = fit_logistic(ds.X_flat[tr], ds.y_xs[tr])
    proba = logit.predict_proba(ds.X_flat)[:, 1]
    scores = _score_panel(proba, ds.dates, ds.syms, te)

    panel = load_panel(used_syms + ["SPY"], START, END)
    strat_panel = panel.slice(oos_start, oos_end)
    primary = build_long_short(scores, strat_panel, horizon, quantile=0.2)
    strat_m = perf_metrics(primary.daily_returns)

    # ---- L3 vs baselines ---------------------------------------------------
    print("[L3] strategy vs baselines ...")
    bl = base_mod.all_baselines(panel, oos_start, oos_end)
    baseline_metrics = {name: perf_metrics(r).to_dict() for name, r in bl.items()}
    best_baseline_sharpe = max(m["sharpe"] for m in baseline_metrics.values())
    L3 = {
        "level": 3, "name": "Strategy Validation (point-in-time universe)",
        "strategy": strat_m.to_dict(), "trade_stats": trade_stats(primary.trade_returns),
        "baselines": baseline_metrics,
        "passed": bool(strat_m.sharpe > best_baseline_sharpe and strat_m.max_drawdown > -0.25),
    }

    # ---- L4 / L5 / L6 ------------------------------------------------------
    print("[L4/L5/L6] regime, monte carlo, significance ...")
    L4 = run_level4(primary.dates, primary.daily_returns, panel)
    L5 = run_level5(primary.daily_returns, primary.turnover, seed=SEED)

    cfg_names, cfg_cols = [], []
    for q in (0.1, 0.2, 0.3):
        for h in (5, 10, 20):
            res = build_long_short(scores, strat_panel, h, quantile=q)
            cfg_names.append(f"logistic_q{int(q*100)}_h{h}")
            cfg_cols.append(res.daily_returns)
    T = min(len(c) for c in cfg_cols)
    L6 = run_level6(primary.daily_returns, np.column_stack([c[-T:] for c in cfg_cols]), cfg_names, seed=SEED)

    # ---- BEFORE/AFTER vs the survivor-only run ----------------------------
    survivor = {}
    sp = ARTIFACTS / "certification.json"
    if sp.exists():
        prev = json.loads(sp.read_text())
        s3 = next(l for l in prev["levels"] if l["level"] == 3)["strategy"]
        survivor = {"sharpe": s3["sharpe"], "cagr": s3["cagr"], "max_drawdown": s3["max_drawdown"]}

    levels = [L1, L3, L4, L5, L6]
    result = {
        "meta": {
            "mode": "survivorship-free point-in-time S&P 500",
            "oos_window": [oos_start, oos_end],
            "symbols_used": ds.n_symbols,
            "delisted_or_removed_included": ds.n_deaths_included,
            "samples": int(len(ds.y_xs)),
            "runtime_seconds": round(time.time() - t0, 1), "seed": SEED,
        },
        "dataset": ds.summary(),
        "levels": levels,
        "survivor_only_comparison": {
            "survivor_only": survivor,
            "survivorship_free": {"sharpe": strat_m.sharpe, "cagr": strat_m.cagr,
                                  "max_drawdown": strat_m.max_drawdown},
        },
        "levels_passed": [l["level"] for l in levels if l["passed"]],
        "levels_failed": [l["level"] for l in levels if not l["passed"]],
        "certified_1_3_4_5_6": all(l["passed"] for l in levels),
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "certification_pit.json").write_text(json.dumps(result, indent=2, default=float))
    (ARTIFACTS / "CERTIFICATION_PIT.md").write_text(render_pit(result))
    print(f"\nDONE in {result['meta']['runtime_seconds']}s → artifacts/CERTIFICATION_PIT.md")
    return result


def render_pit(r: dict) -> str:
    from render_report import render_certification_pit
    return render_certification_pit(r)


if __name__ == "__main__":
    main()
