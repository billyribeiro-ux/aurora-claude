# AURORA-SWING — Alpha Research #1: Rich Features, Survivorship-Free

*OOS 2023-01-03→2026-06-25 · 685 symbols (185 delisted incl.) · 1,354,941 samples · 24 rank-normalized features · seed 7 · 120.4s.*

Same survivorship-free harness as Module 13 — only the signal changed (24 leakage-safe features, cross-sectionally rank-normalized each day).

## Out-of-sample Information Coefficient

| Model | OOS IC (cross-sectional) |
| --- | --- |
| gbm | +0.0051 |
| logistic | +0.0103 |
| ensemble | +0.0087 |

## Did richer features help? (survivorship-free, before → after)

| Metric | Naive 8 features | Rich 24 features | Change |
| --- | --- | --- | --- |
| Sharpe | -0.883 | -0.161 | +0.722 |
| CAGR | -0.064 | -0.007 | +0.057 |
| Max DD | -0.226 | -0.084 | +0.142 |

## Level 3 — Strategy vs baselines (point-in-time)

| Metric | Strategy | buy_and_hold_spy | momentum_20d | ma_cross_50_200 | random_agent |
| --- | --- | --- | --- | --- | --- |
| CAGR | -0.007 | +0.207 | +0.027 | +0.132 | +0.048 |
| Sharpe | -0.161 | +1.316 | +0.620 | +0.935 | +0.383 |
| Sortino | -0.222 | +1.791 | +0.469 | +1.199 | +0.574 |
| Calmar | -0.082 | +1.092 | +0.395 | +0.697 | +0.228 |
| Max DD | -0.084 | -0.190 | -0.068 | -0.190 | -0.210 |

- Gates — L3 ❌ FAIL, L4 ✅ PASS, L5 ❌ FAIL, L6 ❌ FAIL.
- Bootstrap Sharpe -0.16 (95% CI [-1.161, 0.809]), P(Sharpe>0)=0.3774; **PBO 0.4484** (moderate).

## Honest verdict

Best OOS IC: **logistic = +0.0103**. Survivorship-free strategy Sharpe **-0.16** vs naive **-0.88** and buy-and-hold **+1.32**. Richer features improved the signal but it still does not clear the bar. Reported as-measured, survivorship-free. Reproducible via `python alpha_research.py`.
