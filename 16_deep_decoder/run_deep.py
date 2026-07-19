"""End-to-end deep decoder — the neural net makes the trading decision itself.

Pipeline:
  1. Build a survivorship-free, point-in-time SEQUENCE dataset (32-day windows of
     24 leakage-safe features, cross-sectional outperformance label).
  2. Self-supervised pretraining of the encoder (masked reconstruction, no labels).
  3. Fine-tune the encoder + head END-TO-END on the decision (pretrained vs
     from-scratch, to isolate what pretraining buys).
  4. Evaluate survivorship-free: OOS IC, strategy, and the certification gates.

Usage:  python run_deep.py           (full)
        AURORA_PRE=2 AURORA_FT=2 python run_deep.py   (smoke)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
M12, M13, M14 = HERE.parent / "12_learned_pipeline", HERE.parent / "13_certification", HERE.parent / "14_alpha_research"
for p in (str(HERE), str(M12), str(M13), str(M14)):
    if p not in sys.path:
        sys.path.insert(0, p)

import encoder as enc_mod  # noqa: E402
from data import DATA_DIR  # noqa: E402
import baselines as base_mod  # noqa: E402
import deep_model as dm  # noqa: E402
from features_plus import FEATURES, compute_features  # noqa: E402
from l4_regime import run_level4  # noqa: E402
from l5_montecarlo import run_level5  # noqa: E402
from l6_significance import run_level6  # noqa: E402
from metrics import perf_metrics, trade_stats  # noqa: E402
from panel import load_panel  # noqa: E402
from sp500_pit import build_timeline, get_api_key  # noqa: E402
from strategy import build_long_short  # noqa: E402

ARTIFACTS = HERE / "artifacts"
SEED, START, END, L, H, SPLIT = 7, "2015-01-01", "2026-07-10", 32, 10, "2023-01-01"
MAX_TRAIN = 350_000  # subsample cap for CPU tractability (reported honestly)


def build_sequences(timeline):
    pool = sorted(timeline.ever_members(START, END))
    Xs, fwds, ds, sy = [], [], [], []
    used, deaths = set(), set()
    for sym in pool:
        path = DATA_DIR / f"{sym}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, parse_dates=["date"])
        if len(df) < 300:
            continue
        f = compute_features(df)
        n = len(f)
        if n <= L + H:
            continue
        fmat = f[FEATURES].to_numpy(np.float32)
        close = f["close"].to_numpy(np.float64)
        idx = f.index
        win = sliding_window_view(fmat, L, axis=0).transpose(0, 2, 1)  # (n-L+1, L, F)
        t = np.arange(L - 1, n - H)                    # decision indices
        w = win[t - (L - 1)]                           # (len(t), L, F)
        fwd = close[t + H] / close[t] - 1.0
        dts = idx[t]
        member = np.array([timeline.is_member(sym, str(pd.Timestamp(d).date())) for d in dts])
        keep = member & np.isfinite(fwd)
        if keep.any():
            Xs.append(w[keep]); fwds.append(fwd[keep])
            ds.append(dts.to_numpy()[keep]); sy.append(np.array([sym] * int(keep.sum())))
            used.add(sym)
            if sym not in timeline.current:
                deaths.add(sym)
    X = np.concatenate(Xs)  # inputs are float32 → result is float32 (no extra copy)
    assert X.dtype == np.float32
    Xs.clear()  # release the per-symbol copies before building the rest
    fwd = np.concatenate(fwds)
    dates = np.concatenate(ds)
    syms = np.concatenate(sy)
    # cross-sectional target
    fwd_xs = np.empty_like(fwd)
    order = np.argsort(dates, kind="stable")
    d_sorted = dates[order]
    uniq, starts = np.unique(d_sorted, return_index=True)
    bounds = list(starts) + [len(dates)]
    for i in range(len(uniq)):
        blk = order[bounds[i]:bounds[i + 1]]
        fwd_xs[blk] = fwd[blk] - fwd[blk].mean()
    y = (fwd_xs > 0).astype(np.int64)
    split = np.datetime64(SPLIT)
    tr = (dates < split) & (dates < (split - np.timedelta64(int(H * 1.5), "D")))
    te = dates >= split
    return {"X": X, "y": y, "fwd_xs": fwd_xs, "dates": dates, "syms": syms,
            "tr": tr, "te": te, "used": len(used), "deaths": len(deaths), "n": len(y)}


def _ic(s, f):
    if np.std(s) < 1e-12:
        return 0.0
    ic, _ = spearmanr(s, f)
    return float(ic) if np.isfinite(ic) else 0.0


def _panel(proba, dates, syms, mask):
    df = pd.DataFrame({"date": pd.to_datetime(dates[mask]), "sym": syms[mask], "score": proba[mask]})
    return df.pivot_table(index="date", columns="sym", values="score", aggfunc="mean")


def main():
    t0 = time.time()
    pre_ep = int(os.environ.get("AURORA_PRE", "10"))
    ft_ep = int(os.environ.get("AURORA_FT", "6"))

    print("[1/6] building survivorship-free sequence dataset ...")
    tl = build_timeline(get_api_key())
    d = build_sequences(tl)
    tr, te = d["tr"], d["te"]
    F = d["X"].shape[2]
    print(f"      n={d['n']:,} train={tr.sum():,} test={te.sum():,} symbols={d['used']} deaths={d['deaths']}")

    print("[2/6] scaling (train stats, in-place chunked — memory-safe) ...")
    X = d.pop("X")  # single 4.1GB owner; everything below views/copies slices of it

    # Seeded train subsample for CPU tractability (reported honestly in meta).
    tr_idx = np.where(tr)[0]
    rng = np.random.default_rng(SEED)
    if len(tr_idx) > MAX_TRAIN:
        tr_idx = np.sort(rng.choice(tr_idx, size=MAX_TRAIN, replace=False))
    n_val = max(1, int(0.1 * len(tr_idx)))
    perm = rng.permutation(len(tr_idx))
    va_sel, tr_sel = tr_idx[perm[:n_val]], tr_idx[perm[n_val:]]

    # Scaler stats from a ≤100k training subsample (train-only, no test peeking),
    # then standardize the full array IN PLACE in chunks — peak stays ~1 copy.
    stat_sel = tr_sel[:: max(1, len(tr_sel) // 100_000)]
    sample = X[stat_sel]
    mu = sample.reshape(-1, F).mean(0).astype(np.float32)
    sd = (sample.reshape(-1, F).std(0) + 1e-8).astype(np.float32)
    del sample
    CHUNK = 100_000
    for s in range(0, len(X), CHUNK):
        X[s : s + CHUNK] = (X[s : s + CHUNK] - mu) / sd

    print(f"[3/6] self-supervised pretraining ({pre_ep} ep) on {len(tr_sel):,} seqs ...")
    ssl_cfg = enc_mod.EncoderConfig(epochs=pre_ep, seed=SEED)
    ssl, _ = enc_mod.pretrain_encoder(X[tr_sel], ssl_cfg)

    print(f"[4/6] fine-tuning end-to-end ({ft_ep} ep): pretrained vs scratch ...")
    cfg = dm.DeepConfig(epochs=ft_ep, seed=SEED)
    Xtr_s, Xva_s = X[tr_sel], X[va_sel]  # materialize once, reuse for both models
    m_pre = dm.DeepDecoder(F, L, cfg); m_pre.load_pretrained(ssl)
    dm.train_supervised(m_pre, Xtr_s, d["y"][tr_sel], Xva_s, d["y"][va_sel], cfg)
    m_scr = dm.DeepDecoder(F, L, cfg)
    dm.train_supervised(m_scr, Xtr_s, d["y"][tr_sel], Xva_s, d["y"][va_sel], cfg)
    del Xtr_s, Xva_s

    X_te = X[te]
    p_pre = dm.predict_proba(m_pre, X_te)
    p_scr = dm.predict_proba(m_scr, X_te)
    del X_te, X
    ic = {"deep_pretrained_finetuned": _ic(p_pre, d["fwd_xs"][te]),
          "deep_from_scratch": _ic(p_scr, d["fwd_xs"][te])}
    print(f"      OOS IC: {ic}")

    print("[5/6] survivorship-free strategy (deep pretrained model) ...")
    used_syms = sorted(set(d["syms"].tolist()))
    oos_start = str(pd.Timestamp(d["dates"][te].min()).date())
    oos_end = str(pd.Timestamp(d["dates"][te].max()).date())
    panel = load_panel(used_syms + ["SPY"], START, END)
    sp = panel.slice(oos_start, oos_end)
    scores = _panel(p_pre, d["dates"], d["syms"], te)
    primary = build_long_short(scores, sp, H, quantile=0.2)
    strat_m = perf_metrics(primary.daily_returns)

    print("[6/6] certification gates (L3/L4/L5/L6) ...")
    bl = base_mod.all_baselines(panel, oos_start, oos_end)
    baseline_metrics = {n: perf_metrics(r).to_dict() for n, r in bl.items()}
    best_bl = max(m["sharpe"] for m in baseline_metrics.values())
    L3 = bool(strat_m.sharpe > best_bl and strat_m.max_drawdown > -0.25)
    L4 = run_level4(primary.dates, primary.daily_returns, panel)
    L5 = run_level5(primary.daily_returns, primary.turnover, seed=SEED)
    cfg_cols, cfg_names = [], []
    for name, pr in [("pre", p_pre), ("scr", p_scr)]:
        spn = _panel(pr, d["dates"], d["syms"], te)
        for q in (0.1, 0.2, 0.3):
            cfg_cols.append(build_long_short(spn, sp, H, quantile=q).daily_returns)
            cfg_names.append(f"{name}_q{int(q*100)}")
    T = min(len(c) for c in cfg_cols)
    L6 = run_level6(primary.daily_returns, np.column_stack([c[-T:] for c in cfg_cols]), cfg_names, seed=SEED)

    result = {
        "meta": {"mode": "end-to-end deep decoder (SSL pretrain + fine-tune), survivorship-free",
                 "oos_window": [oos_start, oos_end], "symbols_used": d["used"],
                 "delisted_included": d["deaths"], "samples": d["n"],
                 "train_used": int(len(tr_sel)), "features": F, "seq_len": L,
                 "pretrain_epochs": pre_ep, "finetune_epochs": ft_ep,
                 "runtime_seconds": round(time.time() - t0, 1), "seed": SEED},
        "oos_ic": ic,
        "pretraining_benefit_ic": ic["deep_pretrained_finetuned"] - ic["deep_from_scratch"],
        "strategy": strat_m.to_dict(), "baselines": baseline_metrics,
        "trade_stats": trade_stats(primary.trade_returns),
        "gates": {"L3": L3, "L4": L4["passed"], "L5": L5["passed"], "L6": L6["passed"]},
        "significance": {"bootstrap_ci": L6["bootstrap_ci"], "pbo": L6["pbo_cscv"]},
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "deep_decoder.json").write_text(json.dumps(result, indent=2, default=float))
    (ARTIFACTS / "DEEP_DECODER.md").write_text(render(result))
    print(f"\nDONE in {result['meta']['runtime_seconds']}s → artifacts/DEEP_DECODER.md")
    return result


def render(r):
    g = lambda p: "✅ PASS" if p else "❌ FAIL"  # noqa: E731
    s, bm, m = r["strategy"], r["baselines"], r["meta"]
    ic, sig, pbo = r["oos_ic"], r["significance"]["bootstrap_ci"], r["significance"]["pbo"]
    lines = [
        "# AURORA-SWING — Deep Decoder: the neural net makes the decision",
        "",
        f"*End-to-end Transformer (self-supervised pretrain + supervised fine-tune), "
        f"survivorship-free. OOS {m['oos_window'][0]}→{m['oos_window'][1]} · "
        f"{m['symbols_used']} symbols ({m['delisted_included']} delisted) · {m['samples']:,} "
        f"samples ({m['train_used']:,} used to train) · {m['features']} features × {m['seq_len']}d · "
        f"pretrain {m['pretrain_epochs']}ep / fine-tune {m['finetune_epochs']}ep · {m['runtime_seconds']}s.*",
        "",
        "The deep model is in the driver's seat — it makes the call directly, not a "
        "downstream hand-feature model.",
        "",
        "## Out-of-sample IC — does the deep model (and pretraining) help?",
        "",
        "| Model | OOS IC |",
        "| --- | --- |",
        f"| deep, from scratch | {ic['deep_from_scratch']:+.4f} |",
        f"| deep, self-supervised pretrain + fine-tune | {ic['deep_pretrained_finetuned']:+.4f} |",
        f"| **benefit of pretraining** | **{r['pretraining_benefit_ic']:+.4f}** |",
        "",
        "## Level 3 — strategy vs baselines (survivorship-free)",
        "",
        "| Metric | Deep strategy | " + " | ".join(bm.keys()) + " |",
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
        "## Honest verdict",
        "",
        f"Deep model OOS IC **{ic['deep_pretrained_finetuned']:+.4f}**, strategy Sharpe "
        f"**{s['sharpe']:+.2f}** vs buy-and-hold **{bm['buy_and_hold_spy']['sharpe']:+.2f}**. "
        + ("The neural net now makes the decision end-to-end; on this data it still does not "
           "clear the bar." if not all(r["gates"].values()) else
           "The deep model cleared the assessable gates — candidate for deeper validation.")
        + " Survivorship-free, reproducible via `python run_deep.py`.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
