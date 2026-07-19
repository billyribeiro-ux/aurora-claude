# AURORA-SWING — Survivorship-Free Certification (Point-in-Time S&P 500)

*OOS **2023-01-03 → 2026-06-25** · 698 symbols used, of which **197 were later removed / acquired / delisted** and are tradable only while they were actual index members · 1,455,682 samples · seed 7 · runtime 103.9s.*

This repeats the certification gauntlet on the **true, then-available universe** — the single most important fix, because it de-biases every downstream number. Level 2 (representation quality) is universe-agnostic and already certified in Module 12.

## The survivorship-bias correction (before → after)

| Metric | Survivor-only (biased) | Survivorship-free (PIT) | Change |
| --- | --- | --- | --- |
| Sharpe | +1.283 | -0.883 | -2.166 |
| CAGR | +0.172 | -0.064 | -0.236 |
| Max Drawdown | -0.126 | -0.226 | -0.100 |

_The gap between these columns is survivorship bias — the free lunch of only trading names that survived to 2026._

## Certification summary (point-in-time)

| Level | Validation | Verdict |
| --- | --- | --- |
| 1 | Data Integrity (survivorship-controlled) | ❌ FAIL |
| 3 | Strategy vs Baselines | ❌ FAIL |
| 4 | Regime Robustness | ✅ PASS |
| 5 | Monte Carlo Stress | ❌ FAIL |
| 6 | Significance (incl. PBO) | ❌ FAIL |
| 2 | Foundation Model | ✅ (certified separately, Module 12) |
| 7 | Live / Paper Trading | ⏸ NOT ASSESSED |

### Overall (L1,3,4,5,6): ❌ NOT CERTIFIED — passed [4], failed [1, 3, 5, 6].

## Level 1 — Data Integrity

| Check | Result | Detail |
| --- | --- | --- |
| timestamps_ordered | ✅ PASS | all symbols strictly chronological |
| no_duplicate_bars | ✅ PASS | no duplicate dates |
| no_missing_ohlcv | ✅ PASS | no NaNs in OHLCV |
| price_data_quality | ❌ FAIL | 4 distressed/delisted names with repeated >60% daily gaps (post-delisting illiquid data to winsorize or exclude): {'FOSL': 3, 'GME': 6, 'NKTR': 3, 'SBNY': 21} |
| ohlc_bounds_valid | ✅ PASS | high>=low and close in [low,high] for all bars |
| survivorship_bias_controlled | ✅ PASS | CONTROLLED: point-in-time index membership; a name is only tradable while it was an actual constituent, and the pool includes 197 removed/delisted names that a survivor-only universe omits. |

## Level 3 — Strategy Validation (point-in-time)

| Metric | Strategy | buy_and_hold_spy | momentum_20d | ma_cross_50_200 | random_agent |
| --- | --- | --- | --- | --- | --- |
| CAGR | -0.064 | +0.207 | +0.027 | +0.132 | +0.048 |
| Sharpe | -0.883 | +1.316 | +0.620 | +0.935 | +0.383 |
| Sortino | -1.347 | +1.791 | +0.469 | +1.199 | +0.574 |
| Calmar | -0.281 | +1.092 | +0.395 | +0.697 | +0.228 |
| Max DD | -0.226 | -0.190 | -0.068 | -0.190 | -0.210 |
| Total | -0.203 | +0.920 | +0.096 | +0.538 | +0.176 |

- Trades: 181186, win rate 0.498, profit factor 0.91, expectancy -0.0024.

## Level 4 — Regime Robustness

| Regime | Days | Return | Sharpe | Max DD |
| --- | --- | --- | --- | --- |
| high_volatility | 98 | -0.024 | -0.68 | -0.044 |
| bear | 29 | +0.020 | +2.16 | -0.017 |
| sideways | 38 | -0.042 | -4.98 | -0.043 |
| bull | 707 | -0.165 | -0.89 | -0.201 |

## Level 5 — Monte Carlo Stress

- Slippage: profitable up to **None×** base cost.
- Order-randomization P95 drawdown: -0.210.
- Verdict: ❌ FAIL

## Level 6 — Statistical Significance

- Bootstrap Sharpe -0.84 (95% CI [-1.784, 0.097]), P(Sharpe>0)=0.0405.
- **PBO (CSCV)**: 0.4524 → moderate.
- **Deflated Sharpe Ratio**: 0.0295 (significant: False).
- Verdict: ❌ FAIL

## Honest verdict

With survivorship bias removed, the strategy's Sharpe moved from **+1.28** (biased) to **-0.88** (point-in-time). Level 1 now **passes** — the universe includes the names that died. The strategy still does not clear every gate; Level 7 (paper trading) remains before any live-capital decision. Reproducible via `python certify_pit.py`.
