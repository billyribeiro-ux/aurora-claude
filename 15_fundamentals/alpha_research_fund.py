"""Alpha research #2 — technicals + leakage-safe fundamentals, survivorship-free.

Isolates the INCREMENTAL value of fundamental factors: trains one model on the 24
technical features and another on technicals + 11 point-in-time fundamental
factors, on the same survivorship-free universe, and compares out-of-sample IC and
the certified strategy.

Honest caveat recorded in the report: the OOS window (2023-2026) was a mega-cap
growth regime historically hostile to value/quality factors, so a weak result
here is regime-conditional, not proof the factors are worthless.

Usage:  python alpha_research_fund.py
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
M12, M13, M14 = HERE.parent / "12_learned_pipeline", HERE.parent / "13_certification", HERE.parent / "14_alpha_research"
for p in (str(HERE), str(M12), str(M13), str(M14)):
    if p not in sys.path:
        sys.path.insert(0, p)

from data import DATA_DIR  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402

import baselines as base_mod  # noqa: E402
from features_plus import FEATURES as TECH, compute_features  # noqa: E402
from fundamental_factors import FUND_FACTORS, attach_fundamentals, coverage  # noqa: E402
from l4_regime import run_level4  # noqa: E402
from l5_montecarlo import run_level5  # noqa: E402
from l6_significance import run_level6  # noqa: E402
from metrics import perf_metrics, trade_stats  # noqa: E402
from panel import load_panel  # noqa: E402
from sp500_pit import build_timeline, get_api_key  # noqa: E402
from strategy import build_long_short  # noqa: E402

ARTIFACTS = HERE / "artifacts"
SEED, START, END, HORIZON, SPLIT = 7, "2015-01-01", "2026-07-10", 10, "2023-01-01"


def build_combined(timeline):
    pool = sorted(timeline.ever_members(START, END))
    frames, used, deaths, with_fund = [], set(), set(), set()
    for sym in pool:
        path = DATA_DIR / f"{sym}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, parse_dates=["date"])
        if len(df) < 260:
            continue
        f = compute_features(df)
        if len(f) <= HORIZON + 1:
            continue
        f = attach_fundamentals(f, sym)
        close = f["close"].to_numpy()
        rows = f[TECH + FUND_FACTORS].copy()
        rows["fwd"] = np.r_[close[HORIZON:] / close[:-HORIZON] - 1.0, [np.nan] * HORIZON]
        rows["sym"], rows["date"] = sym, f.index
        member = np.array([timeline.is_member(sym, str(pd.Timestamp(d).date())) for d in f.index])
        rows = rows[member].dropna(subset=["fwd"])
        if len(rows):
            frames.append(rows)
            used.add(sym)
            if rows[FUND_FACTORS].notna().any().any():
                with_fund.add(sym)
            if sym not in timeline.current:
                deaths.add(sym)
    big = pd.concat(frames, ignore_index=True)

    all_cols = TECH + FUND_FACTORS
    ranks = big.groupby("date")[all_cols].rank(pct=True) - 0.5
    ranks = ranks.fillna(0.0)  # missing fundamentals → neutral rank
    big["fwd_xs"] = big["fwd"] - big.groupby("date")["fwd"].transform("mean")
    y = (big["fwd_xs"] > 0).astype(int).to_numpy()
    dates, syms = big["date"].to_numpy(), big["sym"].to_numpy()
    split = np.datetime64(SPLIT)
    tr = (dates < split) & (dates < (split - np.timedelta64(int(HORIZON * 1.5), "D")))
    te = dates >= split
    return {"ranks": ranks, "y": y, "fwd_xs": big["fwd_xs"].to_numpy(), "dates": dates,
            "syms": syms, "tr": tr, "te": te, "used": len(used), "deaths": len(deaths),
            "with_fund": len(with_fund), "n": len(big)}


def _ic(s, f):
    if np.std(s) < 1e-12:
        return 0.0
    ic, _ = spearmanr(s, f)
    return float(ic) if np.isfinite(ic) else 0.0


def _panel(proba, dates, syms, mask):
    df = pd.DataFrame({"date": pd.to_datetime(dates[mask]), "sym": syms[mask], "score": proba[mask]})
    return df.pivot_table(index="date", columns="sym", values="score", aggfunc="mean")


def _train(X, y, tr):
    return HistGradientBoostingClassifier(max_iter=400, max_depth=5, learning_rate=0.03,
                                          l2_regularization=1.0, random_state=SEED,
                                          early_stopping=True).fit(X[tr], y[tr])


def main():
    t0 = time.time()
    print(f"[cov] fundamentals cached for {coverage()['symbols_cached']} symbols")
    print("[1/4] building combined PIT dataset ...")
    tl = build_timeline(get_api_key())
    d = build_combined(tl)
    tr, te = d["tr"], d["te"]
    R = d["ranks"]
    tech_idx = [R.columns.get_loc(c) for c in TECH]
    all_idx = [R.columns.get_loc(c) for c in TECH + FUND_FACTORS]
    Xtech, Xall = R.to_numpy(np.float32)[:, tech_idx], R.to_numpy(np.float32)[:, all_idx]
    print(f"      samples={d['n']:,} symbols={d['used']} with_fundamentals={d['with_fund']} deaths={d['deaths']}")

    print("[2/4] training technicals-only vs technicals+fundamentals ...")
    m_tech = _train(Xtech, d["y"], tr)
    m_all = _train(Xall, d["y"], tr)
    p_tech = m_tech.predict_proba(Xtech)[:, 1]
    p_all = m_all.predict_proba(Xall)[:, 1]
    ic = {"technicals_only": _ic(p_tech[te], d["fwd_xs"][te]),
          "technicals_plus_fundamentals": _ic(p_all[te], d["fwd_xs"][te])}
    print(f"      OOS IC: {ic}")

    print("[3/4] survivorship-free strategy (technicals+fundamentals) ...")
    used_syms = sorted(set(d["syms"].tolist()))
    oos_start = str(pd.Timestamp(d["dates"][te].min()).date())
    oos_end = str(pd.Timestamp(d["dates"][te].max()).date())
    panel = load_panel(used_syms + ["SPY"], START, END)
    sp = panel.slice(oos_start, oos_end)
    scores = _panel(p_all, d["dates"], d["syms"], te)
    primary = build_long_short(scores, sp, HORIZON, quantile=0.2)
    strat_m = perf_metrics(primary.daily_returns)

    print("[4/4] L3/L4/L5/L6 ...")
    bl = base_mod.all_baselines(panel, oos_start, oos_end)
    baseline_metrics = {n: perf_metrics(r).to_dict() for n, r in bl.items()}
    best_bl = max(m["sharpe"] for m in baseline_metrics.values())
    L3_pass = bool(strat_m.sharpe > best_bl and strat_m.max_drawdown > -0.25)
    L4 = run_level4(primary.dates, primary.daily_returns, panel)
    L5 = run_level5(primary.daily_returns, primary.turnover, seed=SEED)
    cfg_cols, cfg_names = [], []
    for name, pr in [("tech", p_tech), ("all", p_all)]:
        spn = _panel(pr, d["dates"], d["syms"], te)
        for q in (0.1, 0.2, 0.3):
            cfg_cols.append(build_long_short(spn, sp, HORIZON, quantile=q).daily_returns)
            cfg_names.append(f"{name}_q{int(q*100)}")
    T = min(len(c) for c in cfg_cols)
    L6 = run_level6(primary.daily_returns, np.column_stack([c[-T:] for c in cfg_cols]), cfg_names, seed=SEED)

    result = {
        "meta": {"oos_window": [oos_start, oos_end], "symbols_used": d["used"],
                 "with_fundamentals": d["with_fund"], "delisted_included": d["deaths"],
                 "samples": d["n"], "n_tech": len(TECH), "n_fund": len(FUND_FACTORS),
                 "fundamental_lag_days": 90, "runtime_seconds": round(time.time() - t0, 1), "seed": SEED},
        "oos_ic": ic,
        "incremental_ic_from_fundamentals": ic["technicals_plus_fundamentals"] - ic["technicals_only"],
        "strategy": strat_m.to_dict(), "baselines": baseline_metrics,
        "trade_stats": trade_stats(primary.trade_returns),
        "gates": {"L3": L3_pass, "L4": L4["passed"], "L5": L5["passed"], "L6": L6["passed"]},
        "significance": {"bootstrap_ci": L6["bootstrap_ci"], "pbo": L6["pbo_cscv"]},
        "regime_caveat": ("OOS 2023-2026 was a mega-cap growth regime historically hostile to "
                          "value/quality factors; a weak result is regime-conditional."),
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "fundamentals_research.json").write_text(json.dumps(result, indent=2, default=float))
    (ARTIFACTS / "FUNDAMENTALS_RESEARCH.md").write_text(render(result))
    print(f"\nDONE in {result['meta']['runtime_seconds']}s → artifacts/FUNDAMENTALS_RESEARCH.md")
    return result


def render(r):
    g = lambda p: "✅ PASS" if p else "❌ FAIL"  # noqa: E731
    s, bm = r["strategy"], r["baselines"]
    ic, sig, pbo = r["oos_ic"], r["significance"]["bootstrap_ci"], r["significance"]["pbo"]
    m = r["meta"]
    lines = [
        "# AURORA-SWING — Alpha Research #2: Fundamentals, Survivorship-Free",
        "",
        f"*OOS {m['oos_window'][0]}→{m['oos_window'][1]} · {m['symbols_used']} symbols "
        f"({m['with_fundamentals']} with fundamentals, {m['delisted_included']} delisted) · "
        f"{m['samples']:,} samples · {m['n_tech']} technical + {m['n_fund']} fundamental factors · "
        f"filing lag {m['fundamental_lag_days']}d · {m['runtime_seconds']}s.*",
        "",
        "Fundamentals are point-in-time (available only 90 days after period-end, so no "
        "look-ahead). Question: do they add INCREMENTAL signal over technicals?",
        "",
        "## Out-of-sample IC — does adding fundamentals help?",
        "",
        "| Model | OOS IC |",
        "| --- | --- |",
        f"| technicals only (24) | {ic['technicals_only']:+.4f} |",
        f"| technicals + fundamentals (35) | {ic['technicals_plus_fundamentals']:+.4f} |",
        f"| **incremental from fundamentals** | **{r['incremental_ic_from_fundamentals']:+.4f}** |",
        "",
        "## Level 3 — Strategy vs baselines (survivorship-free)",
        "",
        "| Metric | Strategy | " + " | ".join(bm.keys()) + " |",
        "| --- | --- | " + " | ".join("---" for _ in bm) + " |",
    ]
    for key, lab in [("cagr", "CAGR"), ("sharpe", "Sharpe"), ("sortino", "Sortino"),
                     ("calmar", "Calmar"), ("max_drawdown", "Max DD")]:
        row = [f"{s[key]:+.3f}"] + [f"{b[key]:+.3f}" for b in bm.values()]
        lines.append(f"| {lab} | " + " | ".join(row) + " |")
    lines += [
        "",
        f"- Gates — L3 {g(r['gates']['L3'])}, L4 {g(r['gates']['L4'])}, "
        f"L5 {g(r['gates']['L5'])}, L6 {g(r['gates']['L6'])}.",
        f"- Bootstrap Sharpe {sig.get('sharpe_mean', 0):+.2f} (95% CI {sig.get('sharpe_ci95')}), "
        f"P(Sharpe>0)={sig.get('prob_sharpe_positive')}; PBO {pbo.get('pbo')}.",
        "",
        f"> **Regime caveat:** {r['regime_caveat']}",
        "",
        "## Honest verdict",
        "",
        f"Incremental IC from fundamentals: **{r['incremental_ic_from_fundamentals']:+.4f}**. "
        + ("Fundamentals did not add a usable edge in this window."
           if r["incremental_ic_from_fundamentals"] < 0.005 else
           "Fundamentals added measurable incremental signal — worth deeper, multi-regime study.")
        + f" Strategy Sharpe {s['sharpe']:+.2f} vs buy-and-hold {bm['buy_and_hold_spy']['sharpe']:+.2f}. "
        "Survivorship-free, leakage-controlled, reported as-measured.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
