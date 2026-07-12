# Module 12 — Learned Pipeline

The first **actually-trained** learning stage of AURORA-SWING: a self-contained,
reproducible, CPU-runnable pipeline that produces **hard out-of-sample evidence**
about whether a learned market representation beats hand-built features.

This is the concrete first step of the roadmap in
`00_architecture/evolution_roadmap.md` (phases **E1 evidence harness** and
**E2 representation**). It does not touch the live engine.

## What it does

```
real FMP data ──► leakage-safe walk-forward dataset ──► self-supervised encoder
                                                              │  (masked reconstruction,
                                                              │   no labels)
                                                              ▼
                              frozen representation ──► linear probe
                                                              │
   hand-feature logistic / gradient boosting ◄──── compared against ────┘
                                                              │
                                                              ▼
                        out-of-sample IC + permutation-null significance
                                     + quintile long-short evidence
```

## Why the methodology is strict

Financial ML is a minefield of self-deception. This pipeline is built to *resist*
it:

- **No look-ahead in features.** Features come from the platform's
  `FeatureEngineer`, which only looks backwards. A unit test perturbs a future
  bar and proves earlier feature rows do not change.
- **Walk-forward with a label embargo.** Train is 2015→2022, test is 2023→2026.
  A training sample is kept only if *both* its decision date and the date its
  label resolves fall before the split — so no training label can peek into the
  test period.
- **Train-only scaling.** Standardization statistics are fit on train rows only.
- **The right target.** The primary task is *cross-sectional* (market-neutral):
  will this name outperform the universe over the next 10 days? That strips out
  market drift, so any edge is genuine selection alpha, not beta. Null ≈ 50%.
- **Honest significance.** Samples overlap heavily (10-day horizons sampled daily,
  cross-sectionally correlated), so IC is far noisier than iid theory says. Edge
  is judged against a **permutation null** (retrain on shuffled labels N times),
  not an arbitrary threshold. A monotone quintile curve that is still inside the
  null is reported as *no edge*.

## Run it

```bash
cd 12_learned_pipeline
export FMP_API_KEY=...            # or rely on frontend/.env
python run.py                     # full run  → artifacts/results.json + REPORT.md
AURORA_EPOCHS=3 python run.py     # fast smoke run
```

First run fetches ~11 years of daily bars for 32 symbols and caches them under
`artifacts/data/` (git-ignored); later runs are offline and reproducible.

## Files

| File | Role |
| ---- | ---- |
| `universe.py` | Liquid 32-name equity + ETF universe |
| `data.py` | FMP fetch + on-disk cache (key never logged/committed) |
| `dataset.py` | Leakage-safe features, windows, labels, walk-forward split |
| `encoder.py` | Self-supervised masked-reconstruction Transformer encoder |
| `models.py` | Baselines, linear probe, metrics (accuracy / AUC / **IC**) |
| `evaluate.py` | Permutation-null significance + quintile long-short analysis |
| `run.py` | Orchestrates end-to-end; writes the evidence report |

Tests live in `tests/test_learned_pipeline.py` (fast, synthetic, no network).

## Reading the results

Open `artifacts/REPORT.md`. The number that matters is the **Information
Coefficient on the cross-sectional task, judged against the permutation null**.
Accuracy alone is a weak yardstick. The report states plainly whether a
statistically significant edge was found — win or lose.
