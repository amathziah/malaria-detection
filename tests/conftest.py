"""Shared fixtures: fake A0-A3 results in train_fold's format (for the statistics and figure tests)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import marques2022_exact as mx  # noqa: E402


def write_experiment(root, exp, seed, quality):
    """10 fake folds of `exp` in results/<folder>/folds; image experiments share files, patient ones too."""
    rng = np.random.default_rng(seed)
    patient = mx.EXPERIMENTS[exp]["split"] == "patient"
    val_files = np.array([f"C{(200 if patient else 0) + i % 8}P_cell_{i}.png" for i in range(80)])
    val_true = np.arange(80) % 2
    folder = os.path.join(root, mx.EXPERIMENTS[exp]["folder"], "folds")
    for k in range(10):
        test_files = np.array([f"C{(300 if patient else 0) + 10 * k + i % 10}P_cell_{k}_{i}.png" for i in range(30)])
        test_true = np.arange(30) % 2
        probs = {}
        for name, truth in [("test_aug", test_true), ("test_clean", test_true), ("val_aug", val_true),
                            ("val_clean", val_true)]:
            p0 = np.clip(np.where(truth == 0, quality, 1 - quality) + rng.normal(0, 0.25, len(truth)), 0, 1)
            probs[name] = np.stack([p0, 1 - p0], 1)
        metrics = {n: mx.classification_summary(test_true if n.startswith("test") else val_true, p.argmax(1), p)
                   for n, p in probs.items()}
        e = mx.EXPERIMENTS[exp]
        record = dict(fold=k, best_epoch=3, epochs=5, train_seconds=60.0, eval_seconds=5.0, n_train=270, n_test=30,
                      history={"loss": [1.0] * 5, "val_loss": [1.0] * 5, "accuracy": [0.5] * 5,
                               "val_accuracy": [0.5] * 5},
                      metrics=metrics, split_fingerprint="p" if patient else "i", gpu=["RTX 4090"],
                      experiment=exp, split=e["split"], preprocess=e["preprocess"])
        mx.save_fold_outputs(folder, record, probs, test_files=test_files, val_files=val_files,
                             test_true=test_true, val_true=val_true)
    mx.write_results(mx.aggregate(folder), os.path.join(root, mx.EXPERIMENTS[exp]["folder"]))


@pytest.fixture(scope="module")
def results_root(tmp_path_factory):
    root = str(tmp_path_factory.mktemp("results"))
    for exp, seed, quality in [("A0", 0, 0.8), ("A1", 1, 0.65), ("A2", 2, 0.66), ("A3", 3, 0.8)]:
        write_experiment(root, exp, seed, quality)
    return root
