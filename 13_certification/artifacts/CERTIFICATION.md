# AURORA-SWING — Institutional Certification Report

*Out-of-sample window **2023-01-03 → 2026-06-25** · 32 symbols · 89,792 samples · seed 7 · runtime 464.1s.*

**Primary strategy under test:** cross-sectional L/S, logistic signal, q=0.2, H=10, daily-rebalanced overlap.

> Evaluated as if capital were already at risk. The question is not *how much did it make* but *does it produce repeatable risk-adjusted returns across environments, and is the edge real rather than overfit*. Gates are fixed in advance; numbers are reported as-measured.

## Certification summary

| Level | Validation | Verdict |
| ----- | ---------- | ------- |
| 1 | Data Integrity | ❌ FAIL |
| 2 | Foundation Model | ✅ PASS |
| 3 | Strategy vs Baselines | ❌ FAIL |
| 4 | Regime Robustness | ✅ PASS |
| 5 | Monte Carlo Stress | ✅ PASS |
| 6 | Statistical Significance (incl. PBO) | ✅ PASS |
| 7 | Live / Paper Trading | ⏸ NOT ASSESSED (requires live time) |

### Overall: ❌ NOT CERTIFIED  —  passed levels [2, 4, 5, 6], failed [1, 3].

## Level 1 — Data Integrity

| Check | Result | Detail |
| --- | --- | --- |
| timestamps_ordered | ✅ PASS | all symbols strictly chronological |
| no_duplicate_bars | ✅ PASS | no duplicate dates |
| no_missing_ohlcv | ✅ PASS | no NaNs in OHLCV |
| corporate_actions_adjusted | ✅ PASS | split-adjusted closes — no split-like discontinuities (real earnings moves up to ~50% retained) |
| ohlc_bounds_valid | ✅ PASS | high>=low and close in [low,high] for all bars |
| survivorship_bias_controlled | ❌ FAIL | NOT CONTROLLED: universe is fixed CURRENT constituents (2026 survivors) back-tested to 2015. This inflates results by excluding delisted names. Controlling it requires point-in-time index membership + delisted history. |

## Level 2 — Foundation Model Validation

- **mask_reconstruction** — ✅ PASS: aurora_masked_mse=0.532794, random_encoder_masked_mse=1.463079, pca_full_recon_mse_reference=0.122432, improvement_vs_random=0.6358
- **latent_stability** — ✅ PASS: intra_regime_cosine=0.7187, inter_regime_cosine=0.659, separation=0.0598
- **future_latent_prediction** — ✅ PASS: learned_mse=0.042207, persistence_mse=0.103002, mean_baseline_mse=0.139186, beats_persistence=True

## Level 3 — Strategy Validation

_Strategy is a dollar-neutral cross-sectional long/short; baselines are long-only SPY. Compare on Sharpe / drawdown, not raw return._

| Metric | Strategy | buy_and_hold_spy | momentum_20d | ma_cross_50_200 | random_agent |
| --- | --- | --- | --- | --- | --- |
| CAGR | +0.172 | +0.207 | +0.027 | +0.132 | +0.048 |
| Sharpe | +1.283 | +1.316 | +0.620 | +0.935 | +0.383 |
| Sortino | +1.894 | +1.791 | +0.469 | +1.199 | +0.574 |
| Calmar | +1.371 | +1.092 | +0.395 | +0.697 | +0.228 |
| Max Drawdown | -0.126 | -0.190 | -0.068 | -0.190 | -0.210 |
| Total Return | +0.734 | +0.920 | +0.096 | +0.538 | +0.176 |

- Trades: 10344, win rate 0.500, profit factor 1.28, expectancy +0.0065, max losing streak 17.

## Level 4 — Regime Robustness

| Regime | Days | Return | Sharpe | Max DD |
| --- | --- | --- | --- | --- |
| high_volatility | 98 | +0.159 | +2.45 | -0.065 |
| bear | 29 | -0.002 | -0.07 | -0.031 |
| sideways | 38 | +0.124 | +6.34 | -0.014 |
| bull | 707 | +0.334 | +0.88 | -0.121 |

- Worst single-regime drawdown: -0.121 → ✅ PASS

## Level 5 — Monte Carlo Stress

- **Order randomization** (10,000 sims): actual maxDD -0.126, P95 -0.094.
- **Slippage**: profitable up to **10×** base cost (5.0bps); 1x Sharpe +1.18, 2x Sharpe +1.08, 5x Sharpe +0.77, 10x Sharpe +0.25.
- **Gap shocks**: base Sharpe +1.28 → stressed median +0.81 (P05 +0.04).
- **Missing data**: Sharpe by drop {'5pct': 1.282, '10pct': 1.258, '20pct': 1.25}.

- Verdict: ✅ PASS

## Level 6 — Statistical Significance

- **Bootstrap CI** (block bootstrap): annualized return +0.171 (95% CI [0.0201, 0.3401]), Sharpe +1.27 (95% CI [0.216, 2.341]), P(Sharpe>0) = 0.9915.
- **PBO (CSCV)** across 27 configs, 252 splits: **0.2143** → moderate.
- Verdict: ✅ PASS (requires Sharpe CI lower bound > 0 AND PBO < 0.5).

## Honest verdict

**NOT CERTIFIED.** Failed levels: [1, 3]. This is the framework doing its job — the strategy has not proven a real, persistent, overfitting-free, risk-acceptable edge on unseen data. Notable honest findings:

- Level 1 flags **survivorship bias**: the universe is today's survivors, so all downstream results are optimistically biased until point-in-time constituents are used.
- Levels 3/6 measure whether the edge is real and not luck — reported as-measured, not curve-fit to pass.

Level 7 is intentionally not assessed: it requires live/paper-trading time that cannot be simulated. Everything above is out-of-sample, seeded, and reproducible via `python certify.py`.
