"""
AURORA-SWING — Module 13: Institutional Certification Harness (Levels 1-6).

Implements the rigorous evaluation hierarchy: a strategy is not "successful"
because a backtest looks profitable — it must prove the edge is real, persistent,
survives unseen data, is not overfit, and carries acceptable risk.

    L1 Data Integrity  →  L2 Foundation Model  →  L3 Strategy vs Baselines
       →  L4 Regime Robustness  →  L5 Monte Carlo Stress  →  L6 Significance (PBO)

Each level has a PASS/FAIL gate fixed in advance. Level 7 (live/paper trading) is
intentionally not assessed — it requires real time and cannot be simulated. Run
``python certify.py``; the report lands in ``artifacts/CERTIFICATION.md``.
"""
