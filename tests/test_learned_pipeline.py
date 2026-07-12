"""Module 12 — learned-pipeline integrity tests (no network, no FMP needed).

These lock in the properties that make the out-of-sample evidence trustworthy:
feature-level no-look-ahead, the walk-forward label embargo, cross-sectional
de-meaning, train-only scaling, and end-to-end reproducibility. They run on
small synthetic OHLCV frames so they are fast and deterministic.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

PIPE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "12_learned_pipeline")
if PIPE_DIR not in sys.path:
    sys.path.insert(0, PIPE_DIR)

import dataset as ds_mod  # noqa: E402
import evaluate as ev_mod  # noqa: E402
import models as m_mod  # noqa: E402
from dataset import DatasetConfig, build_dataset, scale_splits  # noqa: E402


def _synth_ohlcv(symbol: str, n: int, seed: int) -> pd.DataFrame:
    """Deterministic geometric-random-walk OHLCV for one symbol."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2016-01-01", periods=n)
    rets = rng.normal(0.0003, 0.015, n)
    close = 100 * np.exp(np.cumsum(rets))
    openp = close * (1 + rng.normal(0, 0.003, n))
    high = np.maximum(openp, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(openp, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    vol = rng.integers(1_000_000, 5_000_000, n)
    return pd.DataFrame({"date": dates, "open": openp, "high": high,
                         "low": low, "close": close, "volume": vol})


def _synth_universe(n: int = 400) -> dict[str, pd.DataFrame]:
    return {sym: _synth_ohlcv(sym, n, seed=i + 1)
            for i, sym in enumerate(["AAA", "BBB", "CCC", "DDD", "EEE"])}


def _cfg() -> DatasetConfig:
    return DatasetConfig(seq_len=16, horizon=5, split_date="2017-01-01")


def test_features_have_no_look_ahead() -> None:
    """Perturbing a FUTURE bar must never change an earlier feature row."""
    df = _synth_ohlcv("AAA", 300, seed=1)
    feats = ds_mod.FeatureEngineer().transform(df.set_index("date"))
    df2 = df.copy()
    df2.loc[df2.index[-1], "close"] *= 1.10  # change only the last bar
    feats2 = ds_mod.FeatureEngineer().transform(df2.set_index("date"))
    common = feats.index.intersection(feats2.index)[:-1]  # all but the perturbed bar
    cols = ds_mod.FEATURE_COLS
    assert np.allclose(feats.loc[common, cols].to_numpy(),
                       feats2.loc[common, cols].to_numpy())


def test_walk_forward_embargo() -> None:
    ds = build_dataset(_synth_universe(), _cfg())
    split = np.datetime64(_cfg().split_date)
    # No training label may resolve on/after the split → no leakage into test.
    assert ds.label_dates[ds.train_mask].max() < split
    assert ds.dates[ds.test_mask].min() >= split
    assert not bool((ds.train_mask & ds.test_mask).any())
    assert ds.train_mask.sum() > 0 and ds.test_mask.sum() > 0


def test_cross_sectional_target_is_market_neutral() -> None:
    ds = build_dataset(_synth_universe(), _cfg())
    # Each day's cross-sectionally de-meaned forward returns must sum to ~0.
    for d in np.unique(ds.dates):
        m = ds.dates == d
        if m.sum() > 1:
            assert abs(float(ds.fwd_xs[m].sum())) < 1e-8
    # Binary xs label is derived from the sign of the de-meaned return.
    assert set(np.unique(ds.y_xs)).issubset({0, 1})


def test_scaling_fits_on_train_only() -> None:
    ds = build_dataset(_synth_universe(), _cfg())
    tr, te = ds.train_mask, ds.test_mask
    Xtr, Xte, (mu, sd) = scale_splits(ds.X_flat[tr], ds.X_flat[te])
    assert np.allclose(Xtr.mean(axis=0), 0, atol=1e-5)   # train standardized
    assert np.allclose(Xtr.std(axis=0), 1, atol=1e-3)
    # Test set uses train stats → its mean is NOT forced to zero (no peeking).
    assert not np.allclose(Xte.mean(axis=0), 0, atol=1e-2)


def test_dataset_is_reproducible() -> None:
    a = build_dataset(_synth_universe(), _cfg())
    b = build_dataset(_synth_universe(), _cfg())
    assert np.array_equal(a.X_seq, b.X_seq)
    assert np.array_equal(a.y_xs, b.y_xs)
    assert np.array_equal(a.fwd_xs, b.fwd_xs)


def test_information_coefficient_detects_signal() -> None:
    rng = np.random.default_rng(0)
    fwd = rng.normal(0, 0.02, 5000)
    aligned = fwd + rng.normal(0, 0.01, 5000)   # score correlated with outcome
    assert m_mod.information_coefficient(aligned, fwd) > 0.5
    assert abs(m_mod.information_coefficient(rng.normal(0, 1, 5000), fwd)) < 0.1
    assert m_mod.information_coefficient(np.ones(100), fwd[:100]) == 0.0  # constant → 0


def test_permutation_null_shape() -> None:
    ds = build_dataset(_synth_universe(), _cfg())
    tr, te = ds.train_mask, ds.test_mask
    clf = m_mod.fit_logistic(ds.X_flat[tr], ds.y_xs[tr])
    ic = m_mod.information_coefficient(clf.predict_proba(ds.X_flat[te])[:, 1], ds.fwd_xs[te])
    out = ev_mod.permutation_null(m_mod.fit_logistic, ds.X_flat[tr], ds.y_xs[tr],
                                  ds.X_flat[te], ds.fwd_xs[te], ic, n_perm=4, seed=1)
    assert out["n_perm"] == 4
    assert "p_value" in out and 0.0 <= out["p_value"] <= 1.0
    assert "significant" in out


def test_encoder_pretrains_and_encodes() -> None:
    """End-to-end (tiny) self-supervised encode — skipped if torch is absent."""
    pytest.importorskip("torch")
    import encoder as enc_mod
    ds = build_dataset(_synth_universe(), _cfg())
    tr = ds.train_mask
    Xs_tr, _, _ = scale_splits(ds.X_seq[tr], ds.X_seq[tr])
    cfg = enc_mod.EncoderConfig(epochs=1, batch_size=128, d_model=16, n_layers=1, n_heads=2)
    model, hist = enc_mod.pretrain_encoder(Xs_tr, cfg)
    Z = enc_mod.encode(model, Xs_tr)
    assert Z.shape[0] == Xs_tr.shape[0]
    assert Z.shape[1] == cfg.d_model
    assert np.isfinite(Z).all()
    assert len(hist["train_loss"]) == 1
