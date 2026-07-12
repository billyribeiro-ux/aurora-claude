# Module 13 — Institutional Certification Harness

*A quantitative strategy is not "successful" because a backtest is profitable. It
must prove the edge is **real**, **persistent**, **survives unseen data**, is
**not overfit**, and carries an **acceptable risk profile**.* This module is the
machine that tries to disprove all five — and reports the result honestly.

It implements the evaluation hierarchy from the project's Section 5 spec as a
single runnable certification with **PASS/FAIL gates fixed in advance**.

```
L1 Data Integrity ─► L2 Foundation Model ─► L3 Strategy vs Baselines
     ─► L4 Regime Robustness ─► L5 Monte Carlo Stress ─► L6 Significance (PBO)
```

Level 7 (3–6 months live/paper trading) is **intentionally not assessed** — it
cannot be simulated in-session and is reported as `NOT ASSESSED`.

## The levels

| Level | What it proves | Key gate |
| ----- | -------------- | -------- |
| **L1 Data Integrity** | The inputs are trustworthy | ordered timestamps, no missing bars, split-adjusted, **survivorship-bias controlled** |
| **L2 Foundation Model** | The representation is real, not noise | masked-reconstruction beats a random encoder; latents cluster by regime; latent dynamics beat persistence |
| **L3 Strategy** | It beats naive alternatives | Sharpe > buy-and-hold / momentum / MA-cross / random, drawdown acceptable |
| **L4 Regime** | It doesn't hide weakness | no catastrophic drawdown in any single market regime |
| **L5 Monte Carlo** | The edge survives friction & luck | order-randomization, slippage (1–10×), gap shocks, missing data |
| **L6 Significance** | The edge is not luck or overfitting | bootstrap Sharpe CI excludes 0; **PBO (CSCV)** below threshold |

## Why it is built to fail honestly

- **Gates are pre-registered**, not tuned until they pass.
- **Survivorship bias is a first-class L1 check** and, on the current
  fixed-universe design, it is reported as **NOT CONTROLLED** — a disclosed
  limitation, because the universe is today's survivors back-tested to 2015.
- **PBO (Bailey & López de Prado CSCV)** directly measures whether the strategy
  *selection* is overfitting the backtest — the single most important test
  against self-deception in quant research.
- The strategy under test is the honest one we actually have (a cross-sectional
  long/short on the Module 12 signal); the report states plainly when it does
  **not** beat a simple buy-and-hold.

## Run it

```bash
cd 13_certification
export FMP_API_KEY=...              # or rely on frontend/.env (never committed)
python certify.py                   # full run → artifacts/CERTIFICATION.md
AURORA_EPOCHS=3 python certify.py   # fast smoke run
```

Reuses Module 12's data cache, dataset and encoder. Tests:
`tests/test_certification.py` (fast, synthetic, no network).

## Reading the result

Open `artifacts/CERTIFICATION.md`. The headline is the **CERTIFIED / NOT
CERTIFIED** verdict and the per-level table. A `NOT CERTIFIED` result with a
clear reason is a *success* of the harness: it means the system has not yet
earned live capital, and it says exactly why.
