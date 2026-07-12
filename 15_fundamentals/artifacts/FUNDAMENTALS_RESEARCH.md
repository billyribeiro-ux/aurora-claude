# AURORA-SWING — Alpha Research #2: Fundamentals, Survivorship-Free

*OOS 2023-01-03→2026-06-25 · 685 symbols (667 with fundamentals, 185 delisted) · 1,354,941 samples · 24 technical + 11 fundamental factors · filing lag 90d · 127.1s.*

Fundamentals are point-in-time (available only 90 days after period-end, so no look-ahead). Question: do they add INCREMENTAL signal over technicals?

## Out-of-sample IC — does adding fundamentals help?

| Model | OOS IC |
| --- | --- |
| technicals only (24) | +0.0051 |
| technicals + fundamentals (35) | +0.0015 |
| **incremental from fundamentals** | **-0.0036** |

## Level 3 — Strategy vs baselines (survivorship-free)

| Metric | Strategy | buy_and_hold_spy | momentum_20d | ma_cross_50_200 | random_agent |
| --- | --- | --- | --- | --- | --- |
| CAGR | -0.025 | +0.207 | +0.027 | +0.132 | +0.048 |
| Sharpe | -0.567 | +1.316 | +0.620 | +0.935 | +0.383 |
| Sortino | -0.756 | +1.791 | +0.469 | +1.199 | +0.574 |
| Calmar | -0.247 | +1.092 | +0.395 | +0.697 | +0.228 |
| Max DD | -0.100 | -0.190 | -0.068 | -0.190 | -0.210 |

- Gates — L3 ❌ FAIL, L4 ✅ PASS, L5 ❌ FAIL, L6 ❌ FAIL.
- Bootstrap Sharpe -0.52 (95% CI [-1.552, 0.512]), P(Sharpe>0)=0.1611; PBO 0.1706.

> **Regime caveat:** OOS 2023-2026 was a mega-cap growth regime historically hostile to value/quality factors; a weak result is regime-conditional.

## Honest verdict

Incremental IC from fundamentals: **-0.0036**. Fundamentals did not add a usable edge in this window. Strategy Sharpe -0.57 vs buy-and-hold +1.32. Survivorship-free, leakage-controlled, reported as-measured.
