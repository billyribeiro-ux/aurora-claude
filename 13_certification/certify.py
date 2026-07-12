"""AURORA-SWING — Institutional Certification Harness (Levels 1–6).

Runs the full evaluation hierarchy on the real out-of-sample period and emits a
single certification with explicit PASS/FAIL gates:

    L1 Data Integrity → L2 Foundation Model → L3 Strategy → L4 Regime
       → L5 Monte Carlo → L6 Significance (bootstrap CI + PBO)

Level 7 (live/paper trading) is intentionally excluded — it cannot be simulated
in-session and is reported as such. Nothing here is curve-fit to pass: the gates
are stated up front and the numbers are reported as-measured.

Usage:
    python certify.py                  # full run
    AURORA_EPOCHS=3 python certify.py  # fast smoke run
"""

from __future__ import annotations

import json
import os
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

# Module 12 building blocks (reused, not reimplemented).
import encoder as enc_mod  # noqa: E402
from data import get_api_key, load_universe  # noqa: E402
from dataset import DatasetConfig, build_dataset, scale_splits  # noqa: E402
from models import fit_gbm, fit_logistic, fit_probe  # noqa: E402
from universe import UNIVERSE  # noqa: E402

# Certification levels.
import baselines as base_mod  # noqa: E402
from l1_data_integrity import run_level1  # noqa: E402
from l2_foundation import run_level2  # noqa: E402
from l4_regime import run_level4  # noqa: E402
from l5_montecarlo import run_level5  # noqa: E402
from l6_significance import run_level6  # noqa: E402
from metrics import perf_metrics, trade_stats  # noqa: E402
from panel import load_panel  # noqa: E402
from strategy import build_long_short  # noqa: E402

ARTIFACTS = HERE / "artifacts"
SEED = 7
START, END = "2015-01-01", "2026-07-10"


def _score_panel(proba: np.ndarray, dates: np.ndarray, syms: np.ndarray, mask: np.ndarray) -> pd.DataFrame:
    """Pivot per-sample scores into a date x symbol panel (masked subset)."""
    df = pd.DataFrame({"date": pd.to_datetime(dates[mask]), "sym": syms[mask], "score": proba[mask]})
    return df.pivot_table(index="date", columns="sym", values="score", aggfunc="mean")


def main() -> dict:
    t0 = time.time()
    epochs = int(os.environ.get("AURORA_EPOCHS", "20"))

    print("[load] data + dataset ...")
    data = load_universe(UNIVERSE, START, END, get_api_key())
    ds = build_dataset(data, DatasetConfig())
    tr, te = ds.train_mask, ds.test_mask
    oos_start = str(pd.Timestamp(ds.dates[te].min()).date())
    oos_end = str(pd.Timestamp(ds.dates[te].max()).date())
    horizon = DatasetConfig().horizon

    # ---- LEVEL 1 -----------------------------------------------------------
    print("[L1] data integrity ...")
    L1 = run_level1(data, universe_is_current=True)

    # ---- encoder + representations ----------------------------------------
    print(f"[enc] self-supervised pretraining ({epochs} epochs) ...")
    Xs_tr, Xs_te, (mu, sd) = scale_splits(ds.X_seq[tr], ds.X_seq[te])
    cfg = enc_mod.EncoderConfig(epochs=epochs, seed=SEED)
    model, _ = enc_mod.pretrain_encoder(Xs_tr, cfg)
    Z_tr, Z_te = enc_mod.encode(model, Xs_tr), enc_mod.encode(model, Xs_te)
    Z_all = enc_mod.encode(model, (ds.X_seq - mu) / sd)

    # ---- LEVEL 2 -----------------------------------------------------------
    print("[L2] foundation model validation ...")
    regime_label = (ds.X_flat[te][:, ds.feature_cols.index("trend_strength")] > 0).astype(int)
    L2 = run_level2(model, enc_mod, cfg, Xs_tr, Xs_te, Z_te, Z_all,
                    regime_label, ds.syms, ds.dates, tr, horizon)

    # ---- models → OOS score panels ----------------------------------------
    print("[fit] models (cross-sectional selection) ...")
    y_tr = ds.y_xs[tr]
    logit = fit_logistic(ds.X_flat[tr], y_tr)
    gbm = fit_gbm(ds.X_flat[tr], y_tr, seed=SEED)
    probe = fit_probe(Z_tr, y_tr)
    scores = {
        "logistic": _score_panel(_full_proba(logit, ds.X_flat), ds.dates, ds.syms, te),
        "gbm": _score_panel(_full_proba(gbm, ds.X_flat), ds.dates, ds.syms, te),
        "probe": _score_panel(_full_proba(probe, Z_all), ds.dates, ds.syms, te),
    }

    # ---- panels + primary strategy ----------------------------------------
    panel_full = load_panel(UNIVERSE, START, END)
    strat_panel = panel_full.slice(oos_start, oos_end)
    primary = build_long_short(scores["logistic"], strat_panel, horizon, quantile=0.2)

    # ---- LEVEL 3 -----------------------------------------------------------
    print("[L3] strategy validation vs baselines ...")
    strat_m = perf_metrics(primary.daily_returns)
    bl = base_mod.all_baselines(panel_full, oos_start, oos_end)
    baseline_metrics = {name: perf_metrics(r).to_dict() for name, r in bl.items()}
    best_baseline_sharpe = max(m["sharpe"] for m in baseline_metrics.values())
    L3 = {
        "level": 3, "name": "Strategy Validation",
        "strategy": strat_m.to_dict(),
        "trade_stats": trade_stats(primary.trade_returns),
        "baselines": baseline_metrics,
        "note": ("Strategy is a dollar-neutral cross-sectional long/short; baselines are "
                 "long-only SPY. Compare on Sharpe / drawdown, not raw return."),
        "passed": bool(strat_m.sharpe > best_baseline_sharpe and strat_m.max_drawdown > -0.25),
    }

    # ---- LEVEL 4 -----------------------------------------------------------
    print("[L4] regime breakdown ...")
    L4 = run_level4(primary.dates, primary.daily_returns, panel_full)

    # ---- LEVEL 5 -----------------------------------------------------------
    print("[L5] monte carlo stress ...")
    L5 = run_level5(primary.daily_returns, primary.turnover, seed=SEED)

    # ---- LEVEL 6 -----------------------------------------------------------
    print("[L6] significance + PBO ...")
    cfg_names, cfg_cols = [], []
    for mname, sp in scores.items():
        for q in (0.1, 0.2, 0.3):
            for h in (5, 10, 20):
                res = build_long_short(sp, strat_panel, h, quantile=q)
                cfg_names.append(f"{mname}_q{int(q*100)}_h{h}")
                cfg_cols.append(res.daily_returns)
    T = min(len(c) for c in cfg_cols)
    config_matrix = np.column_stack([c[-T:] for c in cfg_cols])
    L6 = run_level6(primary.daily_returns, config_matrix, cfg_names, seed=SEED)

    levels = [L1, L2, L3, L4, L5, L6]
    result = {
        "meta": {
            "oos_window": [oos_start, oos_end],
            "universe_size": len(data),
            "samples": int(len(ds.y)),
            "primary_strategy": "cross-sectional L/S, logistic signal, q=0.2, H=10, daily-rebalanced overlap",
            "runtime_seconds": round(time.time() - t0, 1),
            "seed": SEED,
        },
        "levels": levels,
        "levels_passed": [l["level"] for l in levels if l["passed"]],
        "levels_failed": [l["level"] for l in levels if not l["passed"]],
        "certified": all(l["passed"] for l in levels),
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "certification.json").write_text(json.dumps(result, indent=2, default=float))
    (ARTIFACTS / "CERTIFICATION.md").write_text(render(result))
    print(f"\nDONE in {result['meta']['runtime_seconds']}s → artifacts/CERTIFICATION.md")
    return result


def _full_proba(clf, X: np.ndarray) -> np.ndarray:
    return clf.predict_proba(X)[:, 1]


def render(r: dict) -> str:
    from render_report import render_certification
    return render_certification(r)


if __name__ == "__main__":
    main()
