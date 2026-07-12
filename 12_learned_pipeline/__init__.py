"""
AURORA-SWING — Module 12: Learned Pipeline (runnable, CPU-scale, evidence-first).

The first *actually trained* learning stage of the platform. Where modules 02/06
define the GPU-scale model architecture, this module is a self-contained,
reproducible pipeline that:

  1. pulls real market data (FMP),
  2. builds a leakage-safe walk-forward dataset,
  3. pretrains a self-supervised sequence encoder (masked reconstruction),
  4. and judges a linear probe on that representation against strong hand-feature
     baselines using out-of-sample Information Coefficient with a permutation-null
     significance test.

It exists to answer one question with hard evidence, not assertion: does a
learned market representation carry tradable signal beyond hand-built features?
Run ``python run.py`` from this directory; results land in ``artifacts/``.
"""
