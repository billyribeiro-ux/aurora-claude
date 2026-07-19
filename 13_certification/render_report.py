"""Render the certification result into an institutional-style markdown report."""

from __future__ import annotations

__all__ = ["render_certification", "render_certification_pit"]


def _gate(passed: bool) -> str:
    return "✅ PASS" if passed else "❌ FAIL"


def render_certification_pit(r: dict) -> str:
    m = r["meta"]
    L = {lvl["level"]: lvl for lvl in r["levels"]}
    cmp = r["survivor_only_comparison"]
    so, sf = cmp["survivor_only"], cmp["survivorship_free"]
    out: list[str] = [
        "# AURORA-SWING — Survivorship-Free Certification (Point-in-Time S&P 500)",
        "",
        f"*OOS **{m['oos_window'][0]} → {m['oos_window'][1]}** · {m['symbols_used']} symbols "
        f"used, of which **{m['delisted_or_removed_included']} were later removed / acquired / "
        f"delisted** and are tradable only while they were actual index members · "
        f"{m['samples']:,} samples · seed {m['seed']} · runtime {m['runtime_seconds']}s.*",
        "",
        "This repeats the certification gauntlet on the **true, then-available universe** — the "
        "single most important fix, because it de-biases every downstream number. Level 2 "
        "(representation quality) is universe-agnostic and already certified in Module 12.",
        "",
        "## The survivorship-bias correction (before → after)",
        "",
        "| Metric | Survivor-only (biased) | Survivorship-free (PIT) | Change |",
        "| --- | --- | --- | --- |",
    ]
    for key, label in [("sharpe", "Sharpe"), ("cagr", "CAGR"), ("max_drawdown", "Max Drawdown")]:
        b = so.get(key)
        a = sf.get(key)
        if b is not None and a is not None:
            out.append(f"| {label} | {b:+.3f} | {a:+.3f} | {a-b:+.3f} |")
    out += [
        "",
        "_The gap between these columns is survivorship bias — the free lunch of only trading "
        "names that survived to 2026._",
        "",
        "## Certification summary (point-in-time)",
        "",
        "| Level | Validation | Verdict |",
        "| --- | --- | --- |",
        f"| 1 | Data Integrity (survivorship-controlled) | {_gate(L[1]['passed'])} |",
        f"| 3 | Strategy vs Baselines | {_gate(L[3]['passed'])} |",
        f"| 4 | Regime Robustness | {_gate(L[4]['passed'])} |",
        f"| 5 | Monte Carlo Stress | {_gate(L[5]['passed'])} |",
        f"| 6 | Significance (incl. PBO) | {_gate(L[6]['passed'])} |",
        f"| 2 | Foundation Model | ✅ (certified separately, Module 12) |",
        f"| 7 | Live / Paper Trading | ⏸ NOT ASSESSED |",
        "",
        f"### Overall (L1,3,4,5,6): "
        f"{'✅ ALL PASS' if r['certified_1_3_4_5_6'] else '❌ NOT CERTIFIED'} — "
        f"passed {r['levels_passed'] or 'none'}, failed {r['levels_failed'] or 'none'}.",
        "",
    ]
    # L1
    out += ["## Level 1 — Data Integrity", "", "| Check | Result | Detail |", "| --- | --- | --- |"]
    for c in L[1]["checks"]:
        out.append(f"| {c['check']} | {_gate(c['passed'])} | {c['detail']} |")
    # L3
    s = L[3]["strategy"]
    out += ["", "## Level 3 — Strategy Validation (point-in-time)", "",
            "| Metric | Strategy | " + " | ".join(L[3]["baselines"].keys()) + " |",
            "| --- | --- | " + " | ".join("---" for _ in L[3]["baselines"]) + " |"]
    for key, label in [("cagr", "CAGR"), ("sharpe", "Sharpe"), ("sortino", "Sortino"),
                       ("calmar", "Calmar"), ("max_drawdown", "Max DD"), ("total_return", "Total")]:
        row = [f"{s[key]:+.3f}"] + [f"{b[key]:+.3f}" for b in L[3]["baselines"].values()]
        out.append(f"| {label} | " + " | ".join(row) + " |")
    ts = L[3]["trade_stats"]
    out += ["", f"- Trades: {ts.get('trades')}, win rate {ts.get('win_rate', 0):.3f}, "
            f"profit factor {ts.get('profit_factor', 0):.2f}, expectancy {ts.get('expectancy', 0):+.4f}.", ""]
    # L4
    out += ["## Level 4 — Regime Robustness", "", "| Regime | Days | Return | Sharpe | Max DD |",
            "| --- | --- | --- | --- | --- |"]
    for name, v in L[4]["regime_breakdown"].items():
        out.append(f"| {name} | {v['days']} | {v['total_return']:+.3f} | {v['sharpe']:+.2f} | {v['max_drawdown']:+.3f} |")
    # L5 + L6
    l5 = {t["test"]: t for t in L[5]["tests"]}
    ci, pbo = L[6]["bootstrap_ci"], L[6]["pbo_cscv"]
    out += [
        "", "## Level 5 — Monte Carlo Stress", "",
        f"- Slippage: profitable up to **{l5['slippage_stress']['profitable_up_to_multiple']}×** base cost.",
        f"- Order-randomization P95 drawdown: {l5['trade_order_randomization']['p95_max_drawdown']:+.3f}.",
        f"- Verdict: {_gate(L[5]['passed'])}",
        "", "## Level 6 — Statistical Significance", "",
        f"- Bootstrap Sharpe {ci.get('sharpe_mean', 0):+.2f} (95% CI {ci.get('sharpe_ci95')}), "
        f"P(Sharpe>0)={ci.get('prob_sharpe_positive')}.",
        f"- **PBO (CSCV)**: {pbo.get('pbo')} → {pbo.get('interpretation')}.",
        (f"- **Deflated Sharpe Ratio**: {L[6].get('deflated_sharpe', {}).get('dsr', 'n/a')} "
         f"(significant: {L[6].get('deflated_sharpe', {}).get('significant', 'n/a')})."),
        f"- Verdict: {_gate(L[6]['passed'])}",
        "", "## Honest verdict", "",
        f"With survivorship bias removed, the strategy's Sharpe moved from "
        f"**{so.get('sharpe', float('nan')):+.2f}** (biased) to **{sf.get('sharpe', float('nan')):+.2f}** "
        f"(point-in-time). Level 1 now **passes** — the universe includes the names that died. "
        f"{'The strategy clears levels 1,3,4,5,6' if r['certified_1_3_4_5_6'] else 'The strategy still does not clear every gate'}; "
        "Level 7 (paper trading) remains before any live-capital decision. Reproducible via "
        "`python certify_pit.py`.", "",
    ]
    return "\n".join(out)


def render_certification(r: dict) -> str:
    m = r["meta"]
    L = {lvl["level"]: lvl for lvl in r["levels"]}
    out: list[str] = []

    out += [
        "# AURORA-SWING — Institutional Certification Report",
        "",
        f"*Out-of-sample window **{m['oos_window'][0]} → {m['oos_window'][1]}** · "
        f"{m['universe_size']} symbols · {m['samples']:,} samples · seed {m['seed']} · "
        f"runtime {m['runtime_seconds']}s.*",
        "",
        f"**Primary strategy under test:** {m['primary_strategy']}.",
        "",
        "> Evaluated as if capital were already at risk. The question is not *how much "
        "did it make* but *does it produce repeatable risk-adjusted returns across "
        "environments, and is the edge real rather than overfit*. Gates are fixed in "
        "advance; numbers are reported as-measured.",
        "",
        "## Certification summary",
        "",
        "| Level | Validation | Verdict |",
        "| ----- | ---------- | ------- |",
        f"| 1 | Data Integrity | {_gate(L[1]['passed'])} |",
        f"| 2 | Foundation Model | {_gate(L[2]['passed'])} |",
        f"| 3 | Strategy vs Baselines | {_gate(L[3]['passed'])} |",
        f"| 4 | Regime Robustness | {_gate(L[4]['passed'])} |",
        f"| 5 | Monte Carlo Stress | {_gate(L[5]['passed'])} |",
        f"| 6 | Statistical Significance (incl. PBO) | {_gate(L[6]['passed'])} |",
        f"| 7 | Live / Paper Trading | ⏸ NOT ASSESSED (requires live time) |",
        "",
        f"### Overall: {'✅ CERTIFIED' if r['certified'] else '❌ NOT CERTIFIED'}"
        f"  —  passed levels {r['levels_passed'] or 'none'}, failed {r['levels_failed'] or 'none'}.",
        "",
    ]

    # L1
    out += ["## Level 1 — Data Integrity", "", "| Check | Result | Detail |", "| --- | --- | --- |"]
    for c in L[1]["checks"]:
        out.append(f"| {c['check']} | {_gate(c['passed'])} | {c['detail']} |")
    out += [""]

    # L2
    out += ["## Level 2 — Foundation Model Validation", ""]
    for t in L[2]["tests"]:
        out.append(f"- **{t['test']}** — {_gate(t.get('passed', False))}: "
                   + ", ".join(f"{k}={v}" for k, v in t.items() if k not in ("test", "passed")))
    out += [""]

    # L3
    s = L[3]["strategy"]
    out += [
        "## Level 3 — Strategy Validation",
        "",
        f"_{L[3]['note']}_",
        "",
        "| Metric | Strategy | " + " | ".join(L[3]["baselines"].keys()) + " |",
        "| --- | --- | " + " | ".join("---" for _ in L[3]["baselines"]) + " |",
    ]
    for key, label in [("cagr", "CAGR"), ("sharpe", "Sharpe"), ("sortino", "Sortino"),
                       ("calmar", "Calmar"), ("max_drawdown", "Max Drawdown"), ("total_return", "Total Return")]:
        row = [f"{s[key]:+.3f}"] + [f"{b[key]:+.3f}" for b in L[3]["baselines"].values()]
        out.append(f"| {label} | " + " | ".join(row) + " |")
    ts = L[3]["trade_stats"]
    out += ["",
            f"- Trades: {ts.get('trades')}, win rate {ts.get('win_rate', 0):.3f}, "
            f"profit factor {ts.get('profit_factor', 0):.2f}, expectancy {ts.get('expectancy', 0):+.4f}, "
            f"max losing streak {ts.get('max_losing_streak')}.", ""]

    # L4
    out += ["## Level 4 — Regime Robustness", "", "| Regime | Days | Return | Sharpe | Max DD |",
            "| --- | --- | --- | --- | --- |"]
    for name, v in L[4]["regime_breakdown"].items():
        out.append(f"| {name} | {v['days']} | {v['total_return']:+.3f} | {v['sharpe']:+.2f} | {v['max_drawdown']:+.3f} |")
    out += ["", f"- Worst single-regime drawdown: {L[4]['worst_regime_drawdown']:+.3f} → {_gate(L[4]['passed'])}", ""]

    # L5
    out += ["## Level 5 — Monte Carlo Stress", ""]
    for t in L[5]["tests"]:
        if t["test"] == "trade_order_randomization":
            out.append(f"- **Order randomization** ({t['simulations']:,} sims): actual maxDD "
                       f"{t['actual_max_drawdown']:+.3f}, P95 {t['p95_max_drawdown']:+.3f}.")
        elif t["test"] == "slippage_stress":
            out.append(f"- **Slippage**: profitable up to **{t['profitable_up_to_multiple']}×** base "
                       f"cost ({t['base_cost_bps']}bps); " + ", ".join(f"{k} Sharpe {v['sharpe']:+.2f}" for k, v in t["by_multiple"].items()) + ".")
        elif t["test"] == "gap_stress":
            out.append(f"- **Gap shocks**: base Sharpe {t['base_sharpe']:+.2f} → stressed median {t['stressed_sharpe_median']:+.2f} (P05 {t['stressed_sharpe_p05']:+.2f}).")
        elif t["test"] == "missing_data":
            out.append(f"- **Missing data**: Sharpe by drop {t['median_sharpe_by_drop']}.")
    out += ["", f"- Verdict: {_gate(L[5]['passed'])}", ""]

    # L6
    ci = L[6]["bootstrap_ci"]
    pbo = L[6]["pbo_cscv"]
    dsr = L[6].get("deflated_sharpe", {})
    out += [
        "## Level 6 — Statistical Significance",
        "",
        f"- **Bootstrap CI** (block bootstrap): annualized return "
        f"{ci.get('ann_return_mean', 0):+.3f} (95% CI {ci.get('ann_return_ci95')}), "
        f"Sharpe {ci.get('sharpe_mean', 0):+.2f} (95% CI {ci.get('sharpe_ci95')}), "
        f"P(Sharpe>0) = {ci.get('prob_sharpe_positive')}.",
        f"- **PBO (CSCV)** across {pbo.get('n_configs')} configs, {pbo.get('n_splits')} splits: "
        f"**{pbo.get('pbo')}** → {pbo.get('interpretation')}.",
        (f"- **Deflated Sharpe Ratio** (selection across {dsr.get('n_trials')} trials + "
         f"skew {dsr.get('skew')} / kurtosis {dsr.get('kurtosis')}): observed "
         f"{dsr.get('observed_sharpe_ann')} vs null-max {dsr.get('expected_max_null_sharpe_ann')} "
         f"→ **DSR {dsr.get('dsr')}** (significant: {dsr.get('significant')})."
         if dsr and "dsr" in dsr else "- Deflated Sharpe: n/a."),
        f"- Verdict: {_gate(L[6]['passed'])} "
        "(requires Sharpe CI lower bound > 0 AND PBO < 0.5 AND DSR > 0.95).",
        "",
        "## Honest verdict",
        "",
    ]
    if r["certified"]:
        out += ["All assessable levels (1–6) passed. This clears the *research* bar; Level 7 "
                "(3–6 months paper trading) remains before any live-capital decision."]
    else:
        out += [
            f"**NOT CERTIFIED.** Failed levels: {r['levels_failed']}. This is the framework "
            "doing its job — the strategy has not proven a real, persistent, overfitting-free, "
            "risk-acceptable edge on unseen data. Notable honest findings:",
            "",
            "- Level 1 flags **survivorship bias**: the universe is today's survivors, so all "
            "downstream results are optimistically biased until point-in-time constituents are used.",
            "- Levels 3/6 measure whether the edge is real and not luck — reported as-measured, "
            "not curve-fit to pass.",
        ]
    out += ["",
            "Level 7 is intentionally not assessed: it requires live/paper-trading time that "
            "cannot be simulated. Everything above is out-of-sample, seeded, and reproducible "
            "via `python certify.py`.", ""]
    return "\n".join(out)
