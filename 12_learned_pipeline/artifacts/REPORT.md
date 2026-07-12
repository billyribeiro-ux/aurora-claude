# AURORA-SWING — Learned Pipeline: Out-of-Sample Evidence

*Walk-forward. Train 2015-04-29 → 2022-12-15 · Test 2023-01-03 → 2026-07. 89,792 samples (61,568 train / 27,904 test), 8 features, seq_len 32. Encoder: masked-reconstruction Transformer, val loss 0.5233, repr dim 64. Seed 7. Runtime 590.1s.*

**Reading this:** accuracy is a weak yardstick (markets drift). The honest test is the **Information Coefficient** — rank correlation of the model's score with realized forward return — judged against a **permutation null** that respects the overlapping-sample structure. IC inside the null = no edge.

## Cross-sectional selection task (market-neutral, 10-day)

| Model | Accuracy | ROC-AUC | Info Coefficient |
| ----- | -------- | ------- | ---------------- |
| majority (null) | 0.5255 | n/a | +0.0000 |
| hand features · logistic | 0.5286 | 0.5149 | +0.0245 |
| hand features · gradient boosting | 0.5143 | 0.5079 | +0.0094 |
| self-supervised repr · linear probe | 0.5182 | 0.5010 | -0.0066 |

- Best by |IC|: **hand_logistic** (IC +0.0245, acc 0.5286).
- Permutation null (n=12): IC +0.0006 ± 0.0211; real IC p-value **0.167** → significant edge: **False**.
- Forward 10-day return by score quintile (low→high): -0.274%, -0.258%, -0.222%, +0.048%, +0.705%
- Long-short spread (top − bottom): **+0.979%**, monotone: **True**

## Absolute direction task (10-day)

| Model | Accuracy | ROC-AUC | Info Coefficient |
| ----- | -------- | ------- | ---------------- |
| majority (null) | 0.5553 | n/a | +0.0000 |
| hand features · logistic | 0.5535 | 0.4997 | +0.0013 |
| hand features · gradient boosting | 0.5479 | 0.5035 | -0.0105 |
| self-supervised repr · linear probe | 0.5368 | 0.5118 | +0.0048 |

- Best by |IC|: **hand_gbm** (IC -0.0105, acc 0.5479).
- Permutation null (n=12): IC -0.0079 ± 0.0154; real IC p-value **0.333** → significant edge: **False**.
- Forward 10-day return by score quintile (low→high): +1.344%, +0.810%, +0.648%, +0.677%, +1.058%
- Long-short spread (top − bottom): **-0.286%**, monotone: **False**

## Honest verdict

- **Significant edge on the market-neutral selection task (the one that matters for AURORA): False** (p=0.167).
- **E2 gate — does the self-supervised representation beat hand features (with significance) on the selection task? NOT PASSED.** Probe IC -0.0066 vs best hand feature +0.0245; and no model on this task cleared the null.

### What this means

- The encoder genuinely *learned* (validation reconstruction loss fell monotonically), but a learned representation reconstructing market sequences is **not the same as** a representation that predicts forward returns better than hand features. On this data, it does not — yet.
- The best hand model shows a *suggestive* monotone quintile curve, but its IC sits **inside the permutation-null band**, so it is statistically indistinguishable from luck. The overlapping-sample structure makes the null wide — this test has low power, so 'not significant' here means 'not proven', not 'proven absent'.
- This is the roadmap's E2 gate doing its job: **authority is earned on evidence, and the evidence is not yet there.** No component graduates from shadow on these numbers.

### Legitimate next experiments (new, pre-registered — not test-set fishing)

- Widen the universe (hundreds of names) and lengthen history to raise the test's statistical power.
- Richer, less-generic features (cross-asset, microstructure, fundamentals).
- Predict a calibrated forward *distribution* (the world-model objective), not just direction, and size by conviction.

Every number here is out-of-sample, walk-forward, seeded, and reproducible from `python run.py`. Reported as-measured, not as-hoped.
