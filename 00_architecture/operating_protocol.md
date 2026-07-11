# AURORA-SWING — Operating Protocol

Training, deployment, evaluation and an honest capability assessment. This
document is the operating counterpart to [`system_design.md`](./system_design.md):
that one describes *what* the system is; this one describes *how* it is trained,
validated, deployed and judged.

---

# SECTION 4 — Training, Deployment & Autonomous Self-Improvement

## Phase 0 — Data Acquisition

Minimum recommended: **10+ years** of Daily / 4H / 1H OHLCV.

- **Universe:** start with the S&P 500, expand to the Russell 3000.
- **Market context:** SPY, QQQ, IWM.
- **Macro:** VIX, TNX, DXY, Gold, Oil.
- **Sector:** XLK, XLF, XLV, XLE, XLI, XLY, XLP.

## Phase 1 — Foundation Model Training

~**2–8 weeks** of GPU time (depending on dataset size, GPU and sequence length).
Objectives: masked modeling + contrastive learning + future-latent prediction.
Output: a pretrained **market-understanding model**.

## Phase 2 — World Model Training

Learns "what happens after this market condition?" — input past market states,
target future latent states. Must beat a random forecast, a simple momentum
baseline and buy-and-hold.

## Phase 3 — RL Training

Environment: the historical market simulator. Millions of simulated episodes.
The agent learns when to enter, **when not to enter**, sizing and exits.

## Phase 4 — Walk-Forward Certification

Minimum **5+ years** of unseen data spanning **every** market regime:

- **Bull:** 2017, 2020, 2023
- **Bear:** 2018, 2022
- **Crisis:** 2020 COVID, 2022 inflation

## Phase 5 — Paper Trading

Minimum **3–6 months, no exceptions.** Monitor live slippage, execution
assumptions, signal quality and confidence calibration.

## Autonomous Improvement Loop (weekly)

```
New Data → Experience Database → Performance Analysis → Drift Detection
    → Is the change statistically justified?
         ├─ No  → Continue (no change)
         └─ Yes → Fine-Tune → Validate → Deploy New Version
```

Adaptation is controlled — a system that changes constantly becomes unstable.

---

# SECTION 5 — Rigorous Evaluation & Validation Framework

## Philosophy

The system is evaluated as if capital is already at risk. The primary question
is not "how much did it make?" but **"does it produce repeatable risk-adjusted
returns across different market environments?"**

Evaluation hierarchy: Data Integrity → Model → Strategy → Risk → Live.

## Level 1 — Data Integrity

No future leakage. Required checks: timestamps ordered; features computed from
past data only; corporate actions handled; missing data handled; survivorship
bias controlled.

## Level 2 — Foundation Model Validation

Judged by representation quality, not profit.

- **Mask reconstruction accuracy** (MSE) vs a random encoder and a simple
  autoencoder.
- **Latent stability** — similar setups (e.g. NVDA / AMD / SMCI breakouts)
  should be closer in latent space (cosine similarity) than dissimilar ones.
- **Future latent prediction** — `MSE(z_t, z_future)`.

## Level 3 — Trading Strategy Validation

Must beat four baselines: **buy-and-hold**, **simple momentum** (20-day
breakout), a **50/200 SMA** system and a **random agent** (by a wide margin).

**Return:** CAGR, total return.
**Risk (most important — max drawdown):** a +80% return with −60% drawdown is
unacceptable.

| Metric        | Acceptable | Strong | Exceptional |
| ------------- | ---------- | ------ | ----------- |
| Sharpe ratio  | > 1.0      | > 1.5  | > 2.0       |
| Sortino ratio | > 1.5      | > 2.0  | —           |
| Calmar ratio  | > 1        | —      | —           |

**Trade statistics:** total trades, win rate, average win/loss, profit factor,
expectancy, average holding period, maximum losing streak, recovery time.

## Level 4 — Regime-Specific Validation

Performance broken down by environment so weakness cannot hide in an aggregate —
Bull, Bear, High-Volatility and Sideways, each reporting return, Sharpe,
drawdown, trade frequency and exposure.

## Level 5 — Monte Carlo Stress Testing

- **Trade-sequence randomization:** 10,000 simulations.
- **Slippage stress:** normal, 2×, 5×, 10×.
- **Gap stress:** inject ±5% overnight gaps.
- **Missing data:** randomly remove 5%, 10%, 20%.

## Level 6 — Statistical Significance

- **Bootstrap confidence interval:** 95% CI on annual return
  (e.g. 18% with a 95% CI of 11%–25%).
- **Probability of Backtest Overfitting (PBO):** must be low.

## Level 7 — Live Deployment Criteria

Paper trading (3–6 months) must demonstrate positive expectancy, stable
drawdown, no unexpected behaviour, confidence calibration and execution realism.

**Production approval checklist (before live capital):**

```
□ Walk forward passed        □ Monte Carlo passed
□ No leakage                 □ Risk limits verified
□ Paper trading passed       □ Model uncertainty acceptable
□ Regime detection stable    □ Execution tested
□ Emergency shutdown tested
```

---

# SECTION 6 — Honest Assessment of Capabilities & Limitations

## What this system actually is

Not a "prediction machine" — an **adaptive probabilistic decision system** that
identifies favourable risk/reward opportunities while continuously adapting. Its
strongest advantage is not predicting direction but *avoiding poor environments,
sizing intelligently, recognising regime change, adapting behaviour and
controlling downside.*

## Realistic capabilities

1. **Superior market-state understanding** — combines thousands of variables
   simultaneously.
2. **Adaptive strategy selection** — trend vs mean-reversion vs crisis behaviour.
3. **Improved risk management** — where AI provides the largest improvement
   (portfolio heat, volatility targeting, drawdown limits, correlation control).
4. **Continuous adaptation** — controlled, not constant.

## Realistic performance expectations

| Tier         | Annual Return | Max Drawdown | Sharpe    |
| ------------ | ------------- | ------------ | --------- |
| Conservative | 10–20%        | < 15%        | 1.0–1.5   |
| Strong       | 20–35%        | 10–20%       | 1.5–2.0   |
| Exceptional  | 35%+          | controlled   | 2.0+      |

Achieving this **consistently is extremely difficult.** No responsible
researcher promises guaranteed returns, 90% win rates or unlimited scalability —
those claims usually indicate overfitting.

## What will limit performance

- **Alpha decay** — once a pattern is known, capital flows exploit it.
- **Data quality** — bad prices / missing data / survivorship bias create false
  intelligence.
- **Overfitting** — the greatest danger; defended by walk-forward,
  regularization, unseen validation and a simplicity preference.
- **Execution reality** — spreads, liquidity, partial fills, gaps can turn a 20%
  backtest into 12–15% live.
- **Black swans** — no model predicts the never-before-seen; the risk engine
  exists precisely because prediction is impossible.

## What would make it institutional-grade

Alternative data (satellite, credit-card, web traffic, transcripts, options
flow); portfolio-level optimization (Black-Litterman, Bayesian / convex);
advanced execution (smart routing, market-impact modelling, VWAP); a
multi-agent committee; and a human-AI research loop
(AI hypothesis → human validation → AI test → deploy).

## The biggest strategic advantage

Not "AI predicts tomorrow" — it is **a machine that continuously learns how
markets behave and manages uncertainty better than static systems.**

## Recommended build path

```
V1  Foundation Model + Simulator + Backtester
V2  World Model + Regime Detection
V3  RL Portfolio Agent
V4  Continual Learning
V5  Live Paper Trading
V6  Controlled Capital Deployment
```

The correct path is not "build everything and deploy" — it is staged, evidence-
gated progression with risk authority independent of the AI at every step.
