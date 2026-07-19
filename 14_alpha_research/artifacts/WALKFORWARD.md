# AURORA-SWING — Multi-Year Walk-Forward Robustness (Survivorship-Free)

*Expanding-window, one-year sequential test folds · 1,354,941 samples · 685 symbols (185 delisted incl.) · 148.4s.*

Every year is a true out-of-sample fold (train strictly before, label-embargoed).

| Year | Train n | OOS IC | L/S Sharpe | L/S Return | L/S MaxDD | SPY Sharpe |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | 369,981 | +0.0114 | +0.24 | +0.006 | -0.037 | +2.08 |
| 2020 | 499,290 | -0.0187 | -0.30 | -0.027 | -0.087 | +0.61 |
| 2021 | 630,147 | +0.0426 | +2.01 | +0.065 | -0.016 | +1.89 |
| 2022 | 761,099 | -0.0157 | -1.20 | -0.041 | -0.045 | -0.78 |
| 2023 | 892,061 | +0.0043 | -0.69 | -0.021 | -0.032 | +1.73 |
| 2024 | 1,022,444 | +0.0025 | +0.74 | +0.017 | -0.021 | +1.73 |
| 2025 | 1,154,285 | +0.0363 | +1.19 | +0.051 | -0.026 | +0.88 |
| 2026 | 1,286,615 | +0.0188 | +1.25 | +0.024 | -0.025 | +1.17 |

**Summary:** mean OOS IC +0.0102 (6/8 years positive) · mean L/S Sharpe +0.41 (5/8 positive) · worst year -1.20.

Read: a real edge shows positive IC in most years and no catastrophic year. Reported as-measured, survivorship-free. Reproducible via `python walkforward.py`.
