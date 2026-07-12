# AURORA-SWING — North Star & Operating Doctrine

*Chief architect's charter. The goal is the most intelligent, accurate, precise
market intelligence we can build — and the only path to it that means anything is
**hard evidence**. This document is the discipline that keeps ambition honest.*

## The goal, stated so it can be measured

"Best in the world" is a direction, not a claim we get to make about ourselves.
We convert it into things that are **falsifiable**:

- Every predictive claim is **out-of-sample**, on a **survivorship-free** universe,
  with a **PBO** (probability-of-backtest-overfitting) check.
- Nothing is "intelligent" until it beats a naive baseline *after* costs and
  *after* de-biasing. Accuracy is measured, never asserted.
- A negative result, honestly obtained, outranks a positive result obtained by
  fooling ourselves.

## Where we actually stand (measured, not hoped)

- Data & engineering integrity: **provably 100%** — leakage-free, reproducible,
  honest provenance, verified against the raw source.
- Representation learning: the self-supervised encoder is **real** (beats a random
  encoder 64% on reconstruction, clusters by regime, has learnable dynamics).
- **Tradable edge: none yet.** On the survivorship-free S&P 500, the current
  cross-sectional signal is Sharpe **−0.88** — worse than buy-and-hold. The
  survivor-only +1.28 was survivorship bias, and we proved it.

That is the starting line. We build up from a true number, not a flattering one.

## Our only durable advantage: we don't fool ourselves

We cannot out-resource institutions (their tick data, order flow, alt-data,
fundamentals feeds, and teams dwarf ours). We can out-**discipline** them:

1. **Survivorship-free always.** Every backtest runs on point-in-time membership
   that includes the names that died. (Module 13.)
2. **PBO on every strategy-selection step.** If choosing among configurations
   overfits the backtest, we measure it and reject. (Module 13, CSCV.)
3. **Embargoed walk-forward.** No training label may touch the test period.
4. **Costs and capacity are first-class**, not afterthoughts.
5. **Report as-measured.** The console and every artifact state plainly what is
   heuristic, what is trained, and what has *no* demonstrated edge.

## The evidence-gated path to real intelligence

Each stage is a hypothesis tested on the survivorship-free harness; it graduates
only by clearing the gates. Order is by expected signal-per-unit-risk-of-self-
deception, not by glamour.

1. **Breadth of accessible signal.** Exhaust what daily OHLCV can give: multi-
   horizon momentum/reversal, volatility structure, volume/liquidity, cross-
   sectional and market-relative ranks, regime conditioning. (Module 14.)
2. **Representation in the loop.** Wire the self-supervised latent into the
   tradable signal and test whether it adds *incremental* IC over hand features.
3. **Right target, right horizon.** Predict calibrated forward *distributions*
   (world-model objective) and size by conviction, not just direction.
4. **Alternative data, leakage-safe.** Point-in-time fundamentals (with reporting
   lag handled), estimates, earnings surprises — only with as-of dates that
   prevent look-ahead.
5. **Portfolio construction & costs.** Turn any surviving signal into a
   capacity-aware, cost-robust portfolio; re-certify end to end.

## The bar for "deploy real capital"

Unchanged and absolute: a strategy reaches live capital only after it clears
Levels 1–6 **survivorship-free**, then survives **Level 7** (3–6 months paper
trading), with the risk firewall retaining final authority and a human sign-off.
Until then, AURORA is a research instrument that tells the truth — which is
already rarer than it should be.

*The mission is not to claim we are the best. It is to build the process that
would* find out *if we were — and to believe it only when the evidence does.*
