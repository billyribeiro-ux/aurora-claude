"""LEVEL 2 — Foundation Model Validation (judged by representation, not profit).

Test 1 — Mask reconstruction: does training help? AURORA's masked-reconstruction
         MSE on held-out sequences must beat an untrained random encoder (and we
         report a PCA linear-autoencoder as an external reference).
Test 2 — Latent stability: do similar market environments cluster? Mean cosine
         similarity of latents WITHIN a regime must exceed similarity ACROSS
         regimes.
Test 3 — Future-latent prediction: are the latent dynamics learnable? A ridge map
         z_t -> z_{t+H} must beat a persistence baseline (predict z_t) on
         held-out pairs.
"""

from __future__ import annotations

import numpy as np
import torch
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

__all__ = ["run_level2"]


def _masked_recon_mse(model, Xs: np.ndarray, mask_ratio: float, seed: int) -> float:
    model.eval()
    X = torch.from_numpy(Xs.astype(np.float32))
    gen = torch.Generator().manual_seed(seed)
    mask = torch.rand(X.shape[:2], generator=gen) < mask_ratio
    with torch.no_grad():
        recon = model(X, mask)
    diff = (recon - X) ** 2
    return float((diff * mask.unsqueeze(-1)).sum() / (mask.sum() * X.shape[-1] + 1e-8))


def _test1_reconstruction(model, enc_mod, cfg, Xs_train, Xs_test) -> dict:
    aurora = _masked_recon_mse(model, Xs_test, cfg.mask_ratio, seed=101)
    torch.manual_seed(999)
    random_model = enc_mod.MaskedSeqAutoencoder(Xs_test.shape[2], Xs_test.shape[1], cfg)
    rand = _masked_recon_mse(random_model, Xs_test, cfg.mask_ratio, seed=101)

    # PCA linear-AE reference (sees full input → a strong lower-ish bound).
    ntr, L, F = Xs_train.shape
    pca = PCA(n_components=min(cfg.d_model, L * F)).fit(Xs_train.reshape(ntr, L * F))
    flat_te = Xs_test.reshape(Xs_test.shape[0], L * F)
    pca_mse = float(((pca.inverse_transform(pca.transform(flat_te)) - flat_te) ** 2).mean())

    passed = aurora < rand * 0.98  # training must give a clear improvement
    return {
        "test": "mask_reconstruction",
        "aurora_masked_mse": round(aurora, 6),
        "random_encoder_masked_mse": round(rand, 6),
        "pca_full_recon_mse_reference": round(pca_mse, 6),
        "improvement_vs_random": round(1 - aurora / rand, 4) if rand else 0.0,
        "passed": bool(passed),
    }


def _test2_clustering(Z_test: np.ndarray, regime_label: np.ndarray, seed: int = 7) -> dict:
    """Intra- vs inter-regime cosine similarity of unit-normalized latents."""
    Z = Z_test / (np.linalg.norm(Z_test, axis=1, keepdims=True) + 1e-9)
    rng = np.random.default_rng(seed)
    n = len(Z)
    idx_a = rng.integers(0, n, size=20000)
    idx_b = rng.integers(0, n, size=20000)
    keep = idx_a != idx_b
    a, b = idx_a[keep], idx_b[keep]
    cos = (Z[a] * Z[b]).sum(axis=1)
    same = regime_label[a] == regime_label[b]
    intra = float(cos[same].mean()) if same.any() else 0.0
    inter = float(cos[~same].mean()) if (~same).any() else 0.0
    return {
        "test": "latent_stability",
        "intra_regime_cosine": round(intra, 4),
        "inter_regime_cosine": round(inter, 4),
        "separation": round(intra - inter, 4),
        "passed": bool(intra > inter),
    }


def _test3_future_latent(Z_all, syms, dates, train_mask, horizon) -> dict:
    """Ridge z_t -> z_{t+H} on same-symbol pairs; must beat persistence."""
    Xtr, Ytr, Xte, Yte = [], [], [], []
    order = np.lexsort((dates, syms))  # group by symbol, ordered by date
    s_sorted = syms[order]
    for sym in np.unique(syms):
        block = order[s_sorted == sym]
        if len(block) <= horizon:
            continue
        src, dst = block[:-horizon], block[horizon:]  # consecutive trading days
        for i, j in zip(src, dst):
            if train_mask[i] and train_mask[j]:
                Xtr.append(Z_all[i]); Ytr.append(Z_all[j])
            elif (not train_mask[i]) and (not train_mask[j]):
                Xte.append(Z_all[i]); Yte.append(Z_all[j])
    Xtr, Ytr = np.asarray(Xtr), np.asarray(Ytr)
    Xte, Yte = np.asarray(Xte), np.asarray(Yte)
    if len(Xte) < 50 or len(Xtr) < 50:
        return {"test": "future_latent_prediction", "passed": False, "detail": "insufficient pairs"}
    model = Ridge(alpha=10.0).fit(Xtr, Ytr)
    learned_mse = float(((model.predict(Xte) - Yte) ** 2).mean())
    persistence_mse = float(((Xte - Yte) ** 2).mean())     # predict z_t unchanged
    mean_mse = float(((Ytr.mean(axis=0) - Yte) ** 2).mean())  # predict train mean
    return {
        "test": "future_latent_prediction",
        "learned_mse": round(learned_mse, 6),
        "persistence_mse": round(persistence_mse, 6),
        "mean_baseline_mse": round(mean_mse, 6),
        "beats_persistence": bool(learned_mse < persistence_mse),
        "passed": bool(learned_mse < persistence_mse),
    }


def run_level2(model, enc_mod, cfg, Xs_train, Xs_test, Z_test, Z_all,
               regime_label, syms, dates, train_mask, horizon) -> dict:
    t1 = _test1_reconstruction(model, enc_mod, cfg, Xs_train, Xs_test)
    t2 = _test2_clustering(Z_test, regime_label)
    t3 = _test3_future_latent(Z_all, syms, dates, train_mask, horizon)
    tests = [t1, t2, t3]
    return {
        "level": 2,
        "name": "Foundation Model Validation",
        "tests": tests,
        # Gate: representation must at least be a real, trained representation
        # (beats random reconstruction) and show regime structure. Learnable
        # dynamics (t3) is reported but not required to pass this level.
        "passed": bool(t1["passed"] and t2["passed"]),
    }
