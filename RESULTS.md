# AURORA-SWING — Evidence Ledger

*The single honest record of what has been built and what has been measured. Every
number here is out-of-sample where it claims to be, survivorship-free where it
claims to be, and reproducible from the commands shown. Nothing is asserted that
the evidence does not support.*

---

## What AURORA-SWING is

An autonomous quantitative **research platform** for swing trading, built to the
one standard that actually matters: **hard evidence**. It is not a live trading
system and it makes **no claim of a profitable edge**. Its value is that it can
tell the truth about a strategy — including the truth that a strategy has no edge —
using machinery that most systems in this space never apply to themselves.

## The two things that are provably true

**1. Engineering & data integrity: 100%.**

| Property | Evidence |
| --- | --- |
| Live data matches the raw source | 120/120 exact OHLC match vs FMP |
| No look-ahead leakage | Feature- and label-level embargo, integration-tested |
| Reproducible | Seeded, walk-forward; identical inputs → identical outputs |
| Honest provenance | `FMP` only when genuinely live; fallbacks labelled `SYNTHETIC` |
| Test coverage | 47 Python tests + 12 e2e, all passing |

**2. The self-supervised encoder learns real structure** (Module 13, Level 2):
beats an untrained random encoder by **64%** on masked reconstruction, its latents
**cluster by regime**, and their dynamics **beat a persistence baseline**.

## The one thing that is provably *not* true (yet): a certified tradable edge

This is the finding the whole platform exists to establish honestly. The same
task, attacked five ways, all measured on the identical out-of-sample window:

| Evaluation | Sharpe (OOS 2023–2026) | Verdict |
| --- | --- | --- |
| Survivor-only universe (**biased**) | **+1.28** | looked great — and was a mirage |
| Survivorship-free, point-in-time | **−0.88** | the bias *was* the edge |
| + richer features, rank-normalized | **−0.16** | method helped; still no edge |
| + leakage-safe fundamentals | **−0.57** | fundamentals hurt in this regime |
| **end-to-end deep decoder (unsupervised pretrain + fine-tune)** | **+0.76** | first positive — still not certified |
| *baseline: buy-and-hold SPY* | *+1.32* | *the bar none of the above beat* |

**Headline 1: survivorship bias manufactured the entire apparent hand-feature
edge.** Once the 197 removed/acquired/bankrupt names are included and traded only
while they were real index members, every hand-feature strategy loses money.

**Headline 2: the self-learning machine is the best honest signal found.** The
end-to-end Transformer — pretrained *unsupervised* (masked reconstruction, no
labels) then fine-tuned on the decision — achieves the platform's best
survivorship-free numbers: OOS IC +0.0127, Sharpe +0.76, max drawdown −6.2%.
Pretraining measurably helps (+0.0017 IC vs the same net from scratch). It beats
momentum (+0.62) and random (+0.38) — and still honestly fails certification:
below buy-and-hold (+1.32), bootstrap CI includes zero, PBO 0.49. A promising
signal is not a proven edge, and the gates say so.

**Robustness across regimes (8-year walk-forward, survivorship-free):** the
rank-feature signal's OOS IC is positive in 6/8 years (mean +0.0102) and fails
exactly in the crisis years (2020, 2022) — evidence the signal is real but
regime-dependent, which is precisely what the regime engine must gate.

## Why the negative result is the achievement

Anyone can produce a +1.28 Sharpe backtest by (accidentally or otherwise) only
trading survivors. Almost no one proves their own edge is a mirage. AURORA does,
because every claim runs through:

- **Survivorship-free, point-in-time universe** (Module 13) — includes the dead.
- **PBO via CSCV** (Bailey & López de Prado) — measures backtest-overfitting directly.
- **Deflated Sharpe Ratio** — the L6 gate also corrects for selection across every
  configuration tried and for skew/kurtosis (DSR > 0.95 required). Verified on
  real evidence: the edgeless PIT strategy scores DSR 0.03.
- **Embargoed walk-forward** — no training label touches the test period; plus an
  8-year sequential-fold walk-forward so no single lucky split can flatter results.
- **Leakage-controlled fundamentals** — data usable only after its filing date.
- **Reported as-measured** — the console itself labels what is heuristic, what is
  trained, and what has no demonstrated edge.
- **24/7 continual loop** — nightly refresh → re-certify → commit-only-if-changed
  (`00_architecture/runbook_24x7.md`), with honest failure semantics.

## The module map

| Module | Role | Status |
| --- | --- | --- |
| 00 architecture | Design, operating protocol, roadmap, **north star** | ✅ |
| 01–09 | Data, foundation model, regime, RL, risk, backtesting, training (scaffolds) | ✅ built |
| 10 deployment | Live engine, signal service, monitoring | ✅ |
| 11 research agents | Multi-agent committee scaffold | ✅ |
| 12 learned pipeline | Trained self-supervised encoder + honest OOS harness | ✅ trained |
| 13 certification | Institutional L1–L6 gauntlet incl. **survivorship-free PIT** | ✅ |
| 14 alpha research | Rich features, rank-normalization + 8-year walk-forward | ✅ |
| 15 fundamentals | Leakage-safe point-in-time fundamentals | ✅ |
| 16 deep decoder | End-to-end unsupervised-pretrained Transformer decision model | ✅ trained |
| frontend | SvelteKit console (8 pages) with honest disclosures | ✅ |

## Reproduce it

```bash
# Trained encoder + honest OOS evidence
cd 12_learned_pipeline && python run.py
# Institutional certification (survivor-only)
cd 13_certification && python certify.py
# Survivorship-free certification (the headline)
cd 13_certification && python certify_pit.py
# Rich-feature alpha research
cd 14_alpha_research && python alpha_research.py
# Fundamentals swing
cd 15_fundamentals && python fetch_fundamentals.py && python alpha_research_fund.py
# End-to-end deep decoder (unsupervised pretrain + fine-tune, checkpointed)
cd 16_deep_decoder && python run_deep.py
# 8-year walk-forward robustness
cd 14_alpha_research && python walkforward.py
# Tests
python -m pytest tests/
```

## The bar for real capital (unchanged, absolute)

A strategy reaches live capital only after it clears Levels 1–6 **survivorship-free**,
then survives **Level 7** (3–6 months paper trading), with the risk firewall
retaining final authority and a human sign-off. Nothing here is close to that bar —
and the platform says so, plainly, which is the point.

*See `00_architecture/north_star.md` for the operating doctrine and the
evidence-gated path forward.*
