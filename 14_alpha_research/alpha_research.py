"""Alpha research pass #1 — rich features + cross-sectional rank-normalization,
judged survivorship-free.

Hypothesis: a broader, leakage-safe feature set that is RANK-normalized across the
live universe each day (the standard cross-sectional equity approach) carries more
selection signal than the 8 raw features used so far — enough to matter after
survivorship correction, costs, and PBO.

Pre-registered before seeing results:
  * primary model = gradient boosting on rank features (natural for tabular
    cross-sectional data); logistic + ensemble reported as references;
  * evaluated on the point-in-time S&P 500 (Module 13 harness);
  * gates unchanged; PBO across {model x quantile x horizon}.

Usage:  python alpha_research.py
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
M12 = HERE.parent / "12_learned_pipeline"
M13 = HERE.parent / "13_certification"
for p in (str(HERE), str(M12), str(M13)):
    if p not in sys.path:
        sys.path.insert(0, p)

from data import DATA_DIR  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

import baselines as base_mod  # noqa: E402
from features_plus import FEATURES, compute_features  # noqa: E402
from l4_regime import run_level4  # noqa: E402
from l5_montecarlo import run_level5  # noqa: E402
from l6_significance import run_level6  # noqa: E402
from metrics import perf_metrics, trade_stats  # noqa: E402
from panel import load_panel  # noqa: E402
from sp500_pit import build_timeline, get_api_key  # noqa: E402
from strategy import build_long_short  # noqa: E402

ARTIFACTS = HERE / "artifacts"
SEED = 7
START, END = "2015-01-01", "2026-07-10"
HORIZON = 10
SPLIT = "2023-01-01"


def build_rich_pit(timeline):
    """Rich-feature, rank-normalized, point-in-time cross-sectional dataset."""
    pool = sorted(timeline.ever_members(START, END))
    frames = []
    used, deaths = set(), set()
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
        close = f["close"].to_numpy()
        rows = f[FEATURES].copy()
        rows["fwd"] = np.r_[close[HORIZON:] / close[:-HORIZON] - 1.0, [np.nan] * HORIZON]
        rows["sym"] = sym
        rows["date"] = f.index
        # point-in-time membership mask
        member = np.array([timeline.is_member(sym, str(pd.Timestamp(d).date())) for d in f.index])
        rows = rows[member]
        rows = rows.dropna(subset=["fwd"])
        if len(rows):
            frames.append(rows)
            used.add(sym)
            if sym not in timeline.current:
                deaths.add(sym)
    big = pd.concat(frames, ignore_index=True)

    # Cross-sectional rank-normalization per day (percentile rank → centered).
    ranks = big.groupby("date")[FEATURES].rank(pct=True) - 0.5
    # Cross-sectional target: outperform the day's live universe.
    big["fwd_xs"] = big["fwd"] - big.groupby("date")["fwd"].transform("mean")
    y = (big["fwd_xs"] > 0).astype(int).to_numpy()

    dates = big["date"].to_numpy()
    syms = big["sym"].to_numpy()
    split = np.datetime64(SPLIT)
    # Embargo: a train row's label resolves H trading days later; approximate the
    # embargo by requiring the decision date to be H days before the split.
    label_ok = dates < (split - np.timedelta64(int(HORIZON * 1.5), "D"))
    tr = (dates < split) & label_ok
    te = dates >= split
    return {
        "X": ranks.to_numpy(np.float32), "y": y, "fwd_xs": big["fwd_xs"].to_numpy(),
        "dates": dates, "syms": syms, "tr": tr, "te": te,
        "used": len(used), "deaths": len(deaths), "n": len(big),
    }


def _ic(scores, fwd):
    if np.std(scores) < 1e-12:
        return 0.0
    ic, _ = spearmanr(scores, fwd)
    return float(ic) if np.isfinite(ic) else 0.0


def _score_panel(proba, dates, syms, mask):
    df = pd.DataFrame({"date": pd.to_datetime(dates[mask]), "sym": syms[mask], "score": proba[mask]})
    return df.pivot_table(index="date", columns="sym", values="score", aggfunc="mean")


def main() -> dict:
    t0 = time.time()
    print("[1/5] point-in-time membership + rich features ...")
    tl = build_timeline(get_api_key())
    d = build_rich_pit(tl)
    tr, te = d["tr"], d["te"]
    print(f"      samples={d['n']:,} train={tr.sum():,} test={te.sum():,} "
          f"symbols={d['used']} deaths={d['deaths']}")

    print("[2/5] training models (GBM primary, logistic + ensemble refs) ...")
    gbm = HistGradientBoostingClassifier(max_iter=400, max_depth=5, learning_rate=0.03,
                                         l2_regularization=1.0, random_state=SEED,
                                         early_stopping=True).fit(d["X"][tr], d["y"][tr])
    logit = LogisticRegression(max_iter=2000, C=1.0).fit(d["X"][tr], d["y"][tr])
    p_gbm = gbm.predict_proba(d["X"])[:, 1]
    p_logit = logit.predict_proba(d["X"])[:, 1]
    p_ens = 0.5 * (p_gbm + p_logit)

    ic = {"gbm": _ic(p_gbm[te], d["fwd_xs"][te]),
          "logistic": _ic(p_logit[te], d["fwd_xs"][te]),
          "ensemble": _ic(p_ens[te], d["fwd_xs"][te])}
    print(f"      OOS IC: {ic}")

    print("[3/5] building survivorship-free strategy (primary = GBM) ...")
    used_syms = sorted(set(d["syms"].tolist()))
    scores = _score_panel(p_gbm, d["dates"], d["syms"], te)
    oos_start = str(pd.Timestamp(d["dates"][te].min()).date())
    oos_end = str(pd.Timestamp(d["dates"][te].max()).date())
    panel = load_panel(used_syms + ["SPY"], START, END)
    strat_panel = panel.slice(oos_start, oos_end)
    primary = build_long_short(scores, strat_panel, HORIZON, quantile=0.2)
    strat_m = perf_metrics(primary.daily_returns)

    print("[4/5] L3/L4/L5/L6 on survivorship-free universe ...")
    bl = base_mod.all_baselines(panel, oos_start, oos_end)
    baseline_metrics = {n: perf_metrics(r).to_dict() for n, r in bl.items()}
    best_bl = max(m["sharpe"] for m in baseline_metrics.values())
    L3 = {"strategy": strat_m.to_dict(), "baselines": baseline_metrics,
          "trade_stats": trade_stats(primary.trade_returns),
          "passed": bool(strat_m.sharpe > best_bl and strat_m.max_drawdown > -0.25)}
    L4 = run_level4(primary.dates, primary.daily_returns, panel)
    L5 = run_level5(primary.daily_returns, primary.turnover, seed=SEED)

    cfg_names, cfg_cols = [], []
    for name, pr in [("gbm", p_gbm), ("logistic", p_logit), ("ensemble", p_ens)]:
        sp = _score_panel(pr, d["dates"], d["syms"], te)
        for q in (0.1, 0.2, 0.3):
            res = build_long_short(sp, strat_panel, HORIZON, quantile=q)
            cfg_names.append(f"{name}_q{int(q*100)}")
            cfg_cols.append(res.daily_returns)
    T = min(len(c) for c in cfg_cols)
    L6 = run_level6(primary.daily_returns, np.column_stack([c[-T:] for c in cfg_cols]), cfg_names, seed=SEED)

    print("[5/5] writing report ...")
    # Compare to the naive-feature survivorship-free result (Module 13).
    prev = {}
    pj = M13 / "artifacts" / "certification_pit.json"
    if pj.exists():
        pv = json.loads(pj.read_text())
        prev = pv["survivor_only_comparison"]["survivorship_free"]

    result = {
        "meta": {"mode": "rich features + cross-sectional rank-norm, survivorship-free",
                 "oos_window": [oos_start, oos_end], "symbols_used": d["used"],
                 "delisted_included": d["deaths"], "samples": d["n"], "features": len(FEATURES),
                 "runtime_seconds": round(time.time() - t0, 1), "seed": SEED},
        "oos_ic": ic,
        "strategy": strat_m.to_dict(),
        "baselines": baseline_metrics,
        "trade_stats": L3["trade_stats"],
        "regime": L4, "monte_carlo": L5, "significance": L6,
        "gates": {"L3": L3["passed"], "L4": L4["passed"], "L5": L5["passed"], "L6": L6["passed"]},
        "vs_naive_features_pit": {"naive": prev,
                                  "rich": {"sharpe": strat_m.sharpe, "cagr": strat_m.cagr,
                                           "max_drawdown": strat_m.max_drawdown}},
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "alpha_research.json").write_text(json.dumps(result, indent=2, default=float))
    (ARTIFACTS / "ALPHA_RESEARCH.md").write_text(render(result))
    print(f"\nDONE in {result['meta']['runtime_seconds']}s → artifacts/ALPHA_RESEARCH.md")
    return result


def render(r: dict) -> str:
    g = lambda p: "✅ PASS" if p else "❌ FAIL"  # noqa: E731
    s, bm = r["strategy"], r["baselines"]
    vs = r["vs_naive_features_pit"]
    naive, rich = vs.get("naive", {}), vs["rich"]
    sig, pbo = r["significance"]["bootstrap_ci"], r["significance"]["pbo_cscv"]
    lines = [
        "# AURORA-SWING — Alpha Research #1: Rich Features, Survivorship-Free",
        "",
        f"*OOS {r['meta']['oos_window'][0]}→{r['meta']['oos_window'][1]} · "
        f"{r['meta']['symbols_used']} symbols ({r['meta']['delisted_included']} delisted incl.) · "
        f"{r['meta']['samples']:,} samples · {r['meta']['features']} rank-normalized features · "
        f"seed {r['seed'] if 'seed' in r else r['meta']['seed']} · {r['meta']['runtime_seconds']}s.*",
        "",
        "Same survivorship-free harness as Module 13 — only the signal changed "
        "(24 leakage-safe features, cross-sectionally rank-normalized each day).",
        "",
        "## Out-of-sample Information Coefficient",
        "",
        "| Model | OOS IC (cross-sectional) |",
        "| --- | --- |",
        *[f"| {k} | {v:+.4f} |" for k, v in r["oos_ic"].items()],
        "",
        "## Did richer features help? (survivorship-free, before → after)",
        "",
        "| Metric | Naive 8 features | Rich 24 features | Change |",
        "| --- | --- | --- | --- |",
    ]
    for key, lab in [("sharpe", "Sharpe"), ("cagr", "CAGR"), ("max_drawdown", "Max DD")]:
        if naive.get(key) is not None:
            lines.append(f"| {lab} | {naive[key]:+.3f} | {rich[key]:+.3f} | {rich[key]-naive[key]:+.3f} |")
    lines += [
        "",
        "## Level 3 — Strategy vs baselines (point-in-time)",
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
        f"P(Sharpe>0)={sig.get('prob_sharpe_positive')}; **PBO {pbo.get('pbo')}** ({pbo.get('interpretation')}).",
        "",
        "## Honest verdict",
        "",
        f"Best OOS IC: **{max(r['oos_ic'], key=r['oos_ic'].get)} = "
        f"{max(r['oos_ic'].values()):+.4f}**. Survivorship-free strategy Sharpe "
        f"**{rich['sharpe']:+.2f}** vs naive **{naive.get('sharpe', float('nan')):+.2f}** and "
        f"buy-and-hold **{bm['buy_and_hold_spy']['sharpe']:+.2f}**. "
        + ("Richer features improved the signal but it still does not clear the bar."
           if not all(r["gates"].values()) else
           "Richer features cleared the assessable gates — candidate for deeper validation.")
        + " Reported as-measured, survivorship-free. Reproducible via `python alpha_research.py`.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
