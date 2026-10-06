"""Fidelity tests for src/marques2022_exact.py.

Every expected value comes from Marques et al. (2022) or from the paper's own executed
code (Springer supplementary file MOESM1, "efn0_malaria_binary", 30 Jan 2021).

Run:  python -m pytest tests/ -q
Needs: tensorflow==2.15.*, efficientnet==1.1.1, albumentations==0.5.2, imgaug==0.4.0,
       numpy<1.24, scikit-learn, pandas, opencv-python-headless.
"""
import os
import random
import sys

import cv2
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import marques2022_exact as mx  # noqa: E402

N_PER_CLASS = 13_779  # NIH dataset: 27,558 cells, half of each class


def fake_entries(n_per_class=N_PER_CLASS):
    return ([(f"C{i}P{i}thinF_cell_{i}.png", "Parasitized") for i in range(n_per_class)] +
            [(f"C{i}NThinF_cell_{i}.png", "Uninfected") for i in range(n_per_class)])


def write_pngs(folder, n, seed=0):
    """Random RGB crops of varying size, like the NIH cells (they are not 224 x 224)."""
    rng = np.random.default_rng(seed)
    paths = []
    for k in range(n):
        h, w = int(rng.integers(70, 210)), int(rng.integers(70, 230))
        img = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
        p = str(folder / f"img_{k}.png")
        cv2.imwrite(p, img)
        paths.append(p)
    return paths


# --------------------------------------------------------------------------- recipe
def test_hyperparameters_match_the_papers_code():
    c = mx.PAPER
    assert (c["SEED"], c["KFOLD"], c["KFOLD_SEED"]) == (1234, 10, 50)
    assert (c["EPOCHS"], c["BATCH_SIZE"], c["IMG_SIZE"]) == (33, 16, 224)
    assert (c["LR"], c["LR_FACTOR"], c["PATIENCE"], c["MIN_LR"]) == (1e-4, 0.5, 6, 1e-6)
    assert (c["LABEL_SMOOTHING"], c["VAL_FRACTION"], c["WEIGHTS"]) == (0.1, 0.2, "noisy-student")


def test_class_columns_follow_the_papers_order():
    assert mx.TIPOS == ["Parasitized", "Uninfected"]
    np.testing.assert_array_equal(mx.one_hot(["Uninfected", "Parasitized"]), [[0, 1], [1, 0]])


# --------------------------------------------------------------------------- splits
def test_holdout_split_has_the_papers_sizes():
    learn, val = mx.paper_split(mx.build_index(fake_entries()))
    assert (len(learn), len(val)) == (22_046, 5_512)


def test_fold_sizes_match_the_papers_printed_output():
    learn, _ = mx.paper_split(mx.build_index(fake_entries()))
    folds = mx.paper_folds(learn)
    assert [len(tr) for tr, _ in folds] == [19_841] * 6 + [19_842] * 4
    assert [len(te) for _, te in folds] == [2_205] * 6 + [2_204] * 4


def test_split_does_not_depend_on_directory_listing_order():
    entries = fake_entries(500)
    shuffled = entries[:]
    random.Random(7).shuffle(shuffled)
    a_learn, a_val = mx.paper_split(mx.build_index(entries))
    b_learn, b_val = mx.paper_split(mx.build_index(shuffled))
    assert list(a_val["file"]) == list(b_val["file"])
    assert mx.split_fingerprint(a_learn, a_val) == mx.split_fingerprint(b_learn, b_val)


def test_folds_are_stratified_and_cover_the_learning_set_once():
    learn, _ = mx.paper_split(mx.build_index(fake_entries(1_000)))
    folds = mx.paper_folds(learn)
    tested = np.concatenate([te for _, te in folds])
    assert sorted(tested) == list(range(len(learn)))
    for tr, te in folds:
        assert not set(tr) & set(te)


# --------------------------------------------------------------------------- augmentation
def test_augmentation_is_exactly_the_papers_compose():
    from albumentations import (CLAHE, Blur, Compose, Flip, GaussNoise, GridDistortion,
                                IAAAdditiveGaussianNoise, IAAEmboss, IAAPiecewiseAffine,
                                IAASharpen, MedianBlur, MotionBlur, OneOf, OpticalDistortion,
                                RandomBrightness, RandomContrast, RandomRotate90,
                                ShiftScaleRotate, Transpose)
    # Verbatim from the paper's code (MOESM1, section 2.3)
    aug = Compose([RandomRotate90(),
                   Flip(),
                   Transpose(),
                   OneOf([IAAAdditiveGaussianNoise(),
                          GaussNoise(), ], p=0.2),
                   OneOf([MotionBlur(p=.2),
                          MedianBlur(blur_limit=3, p=.1),
                          Blur(blur_limit=3, p=.1), ], p=0.3),
                   ShiftScaleRotate(shift_limit=0.0625,
                                    scale_limit=0.2,
                                    rotate_limit=45, p=.2),
                   OneOf([OpticalDistortion(p=0.3),
                          GridDistortion(p=.1),
                          IAAPiecewiseAffine(p=0.3), ], p=0.3),
                   OneOf([CLAHE(clip_limit=2),
                          IAASharpen(),
                          IAAEmboss(),
                          RandomContrast(),
                          RandomBrightness(), ], p=0.3),
                   ], p=1)
    assert repr(mx.build_paper_augmentation()) == repr(aug)


def test_image_loading_matches_imagedataaugmentor(tmp_path):
    ida_utils = pytest.importorskip("ImageDataAugmentor.utils")
    for p in write_pngs(tmp_path, 6):
        np.testing.assert_array_equal(mx.load_resized(p), ida_utils.load_img(p, target_size=(224, 224)))


def test_clean_batches_equal_imagedataaugmentor_batches(tmp_path):
    ida = pytest.importorskip("ImageDataAugmentor.image_data_augmentor")
    paths = write_pngs(tmp_path, 10)
    df = pd.DataFrame({"file": [os.path.basename(p) for p in paths],
                       "Parasitized": [1, 0] * 5, "Uninfected": [0, 1] * 5})
    gen = ida.ImageDataAugmentor(rescale=1 / 255).flow_from_dataframe(
        df, directory=str(tmp_path), x_col="file", y_col=mx.TIPOS, class_mode="raw",
        target_size=(224, 224), shuffle=False, batch_size=4)
    expected = np.concatenate([gen[i][0] for i in range(len(gen))])

    cache = mx.build_image_cache(paths, str(tmp_path / "cache.npy"), workers=0)
    with mx.AugmentPool(0, cache) as pool:
        ours = np.concatenate([x for _, x in mx.iterate_batches(
            pool, np.arange(10), 4, augment=False, shuffle=False, drop_remainder=False,
            seed_key=(1,), epoch=0)])
    # ImageDataAugmentor rescales in float64 and casts to float32; the model rescales in float32
    np.testing.assert_array_max_ulp(ours.astype(np.float32) * np.float32(1 / 255), expected, maxulp=1)


@pytest.fixture(scope="module")
def tiny_cache(tmp_path_factory):
    folder = tmp_path_factory.mktemp("imgs")
    paths = write_pngs(folder, 24, seed=3)
    return mx.build_image_cache(paths, str(folder / "cache.npy"), workers=2)


def collect(pool, idx, **kw):
    kw = {"batch_size": 4, "augment": True, "shuffle": True, "drop_remainder": True,
          "seed_key": (1234, 0, 0), "epoch": 0, **kw}
    return list(mx.iterate_batches(pool, idx, **kw))


def test_augmented_batches_do_not_depend_on_worker_count(tiny_cache):
    idx = np.arange(24)
    with mx.AugmentPool(0, tiny_cache) as p0, mx.AugmentPool(3, tiny_cache) as p3:
        a, b = collect(p0, idx), collect(p3, idx)
    assert len(a) == len(b) == 6
    for (pa, xa), (pb, xb) in zip(a, b):
        np.testing.assert_array_equal(pa, pb)
        np.testing.assert_array_equal(xa, xb)


def test_each_epoch_gets_a_new_shuffle_and_new_augmentations(tiny_cache):
    idx = np.arange(24)
    with mx.AugmentPool(2, tiny_cache) as pool:
        e0, e1 = collect(pool, idx, epoch=0), collect(pool, idx, epoch=1)
    assert not all(np.array_equal(p0, p1) for (p0, _), (p1, _) in zip(e0, e1))
    cache = np.load(tiny_cache, mmap_mode="r")
    changed = [not np.array_equal(x[i], cache[idx[p[i]]]) for p, x in e0 for i in range(len(p))]
    assert sum(changed) > len(changed) // 2  # the paper's pipeline alters most images


def test_clean_batches_are_the_cached_images_in_order(tiny_cache):
    idx = np.array([5, 3, 9, 0, 1])
    with mx.AugmentPool(2, tiny_cache) as pool:
        out = collect(pool, idx, augment=False, shuffle=False, drop_remainder=False)
    positions = np.concatenate([p for p, _ in out])
    images = np.concatenate([x for _, x in out])
    np.testing.assert_array_equal(positions, np.arange(5))
    np.testing.assert_array_equal(images, np.load(tiny_cache)[idx])


def test_training_epoch_has_the_papers_1240_steps():
    assert mx.steps_per_epoch(19_841, 16) == 1_240
    assert mx.steps_per_epoch(19_842, 16) == 1_240


# --------------------------------------------------------------------------- model
@pytest.fixture(scope="module")
def model():
    return mx.build_model(weights=None)


def test_model_parameter_counts_match_paper_table2(model):
    trainable = int(sum(np.prod(w.shape) for w in model.trainable_weights))
    assert model.count_params() == 4_223_934
    assert trainable == 4_181_918
    assert model.count_params() - trainable == 42_016


def test_head_matches_the_papers_create_model(model):
    head = [(type(l).__name__, l.get_config().get("units"), l.get_config().get("rate"),
             l.get_config().get("activation")) for l in model.layers[-8:]]
    assert head == [("GlobalAveragePooling2D", None, None, None),
                    ("Dense", 128, None, "relu"), ("Dropout", None, 0.3, None),
                    ("Dense", 64, None, "relu"), ("Dropout", None, 0.3, None),
                    ("Dense", 32, None, "relu"), ("Dropout", None, 0.3, None),
                    ("Dense", 2, None, "softmax")]


def test_model_takes_uint8_and_rescales_by_1_over_255(model):
    import tensorflow as tf
    assert model.input.dtype == tf.uint8
    x = np.random.default_rng(0).integers(0, 256, (2, 224, 224, 3), dtype=np.uint8)
    scaled = tf.keras.Model(model.input, model.get_layer("rescale_1_255").output)(x).numpy()
    ida_rescale = np.multiply(x, 1 / 255).astype(np.float32)  # ImageDataAugmentor.standardize
    np.testing.assert_array_max_ulp(scaled, ida_rescale, maxulp=1)


def test_loss_is_categorical_crossentropy_with_label_smoothing_0_1():
    y_true = np.array([[1.0, 0.0]], np.float32)
    y_pred = np.array([[0.9, 0.1]], np.float32)
    expected = -(0.95 * np.log(0.9) + 0.05 * np.log(0.1))
    assert abs(float(mx.paper_loss(y_true, y_pred)[0]) - expected) < 1e-6


def test_optimizer_is_adam_with_lr_1e_4(model):
    mx.compile_paper_model(model, xla=False)
    assert type(model.optimizer).__name__ == "Adam"
    assert model.optimizer.learning_rate.numpy() == np.float32(1e-4)  # Keras keeps the LR in float32


def test_callbacks_follow_the_paper(tmp_path):
    rlr, ckpt = mx.paper_callbacks(str(tmp_path / "w.h5"))[:2]
    assert (rlr.monitor, rlr.factor, rlr.patience, rlr.min_lr) == ("val_loss", 0.5, 6, 1e-6)
    assert (ckpt.monitor, ckpt.save_best_only, ckpt.save_freq) == ("val_loss", True, "epoch")


# --------------------------------------------------------------------------- metrics
def labels_from_counts(blocks):
    """blocks: list of (true_class, predicted_class, count)."""
    y_true = np.concatenate([[t] * n for t, _, n in blocks])
    y_pred = np.concatenate([[p] * n for _, p, n in blocks])
    return y_true, y_pred


def test_report_reproduces_the_papers_ensemble_output():
    # Paper's ensemble on its hold-out set: 2744 parasitized (62 missed), 2768 uninfected (32 flagged)
    y_true, y_pred = labels_from_counts([(0, 0, 2682), (0, 1, 62), (1, 0, 32), (1, 1, 2736)])
    r = mx.classification_summary(y_true, y_pred)
    assert round(r["accuracy"], 6) == 0.982946
    assert (round(r["Parasitized"]["precision"], 6), round(r["Parasitized"]["recall"], 6),
            round(r["Parasitized"]["f1"], 6)) == (0.988209, 0.977405, 0.982778)
    assert (round(r["Uninfected"]["precision"], 6), round(r["Uninfected"]["recall"], 6),
            round(r["Uninfected"]["f1"], 6)) == (0.977841, 0.988439, 0.983112)
    assert round(r["macro"]["f1"], 6) == 0.982945
    assert round(r["weighted"]["precision"], 6) == 0.983003


def test_table5_uses_the_weighted_average():
    # Paper fold 0, CV test part: 1104 parasitized, 1101 uninfected; Table 5 row 0
    y_true, y_pred = labels_from_counts([(0, 0, 1073), (0, 1, 31), (1, 0, 25), (1, 1, 1076)])
    r = mx.classification_summary(y_true, y_pred)
    assert round(r["accuracy"], 6) == 0.974603
    assert (round(r["weighted"]["precision"], 6), round(r["weighted"]["recall"], 6),
            round(r["weighted"]["f1"], 6)) == (0.974617, 0.974603, 0.974603)


def test_roc_auc_is_the_same_for_both_classes():
    rng = np.random.default_rng(0)
    p0 = rng.random(200)
    probs = np.stack([p0, 1 - p0], 1)
    y_true = (rng.random(200) < p0).astype(int) ^ 1  # 0 = parasitized, more likely when p0 is high
    r = mx.classification_summary(y_true, probs.argmax(1), probs)
    from sklearn.metrics import roc_auc_score
    assert abs(r["auc"] - roc_auc_score(y_true == 0, probs[:, 0])) < 1e-12


def test_ensemble_averages_softmax_outputs():
    p1 = np.array([[0.6, 0.4], [0.2, 0.8]])
    p2 = np.array([[0.3, 0.7], [0.4, 0.6]])
    np.testing.assert_allclose(mx.ensemble_probs([p1, p2]), [[0.45, 0.55], [0.3, 0.7]])


# --------------------------------------------------------------------------- end to end
def test_train_fold_runs_end_to_end_and_restores_the_best_checkpoint(tmp_path):
    folder = tmp_path / "imgs"
    folder.mkdir()
    paths = write_pngs(folder, 40, seed=5)
    labels = ["Parasitized", "Uninfected"] * 20
    df = mx.build_index([(os.path.basename(p), l) for p, l in zip(paths, labels)], root=str(folder))
    learn, val = mx.paper_split(df)
    folds = mx.paper_folds(learn, n_splits=4)
    cache = mx.build_image_cache(list(df["path"]), str(tmp_path / "cache.npy"), workers=0)
    with mx.AugmentPool(2, cache) as pool:
        res = mx.train_fold(0, learn=learn, val=val, folds=folds, pool=pool,
                            out_dir=str(tmp_path / "out"), weights=None, xla=False,
                            epochs=2, batch_size=4, verbose=0)
    n_test, n_val = len(folds[0][1]), len(val)
    for key, n in [("test_aug", n_test), ("test_clean", n_test), ("val_aug", n_val), ("val_clean", n_val)]:
        assert res["probs"][key].shape == (n, 2)
        np.testing.assert_allclose(res["probs"][key].sum(1), 1, atol=1e-5)
    assert len(res["history"]["val_loss"]) == 2
    assert res["best_epoch"] == int(np.argmin(res["history"]["val_loss"])) + 1
    assert os.path.exists(res["weights_path"])
    assert os.path.exists(os.path.join(str(tmp_path / "out"), "fold_0", "fold_0_predictions.npz"))


# --------------------------------------------------------------------------- aggregation over folds
def fake_fold_outputs(root, n_folds=3, n_val=40, n_test=20, fingerprint="abc", seed=0):
    """Write fold outputs in train_fold's format without training (random but valid predictions)."""
    rng = np.random.default_rng(seed)
    val_files = np.array([f"C{i % 7}P_cell_{i}.png" for i in range(n_val)])
    val_true = np.arange(n_val) % 2
    all_probs = []
    for k in range(n_folds):
        probs = {}
        for name, n in [("test_aug", n_test), ("test_clean", n_test), ("val_aug", n_val), ("val_clean", n_val)]:
            p0 = rng.random(n)
            probs[name] = np.stack([p0, 1 - p0], 1)
        test_true = np.arange(n_test) % 2
        test_files = np.array([f"C{k}N_cell_{i}.png" for i in range(n_test)])
        metrics = {name: mx.classification_summary((test_true if name.startswith("test") else val_true),
                                                   p.argmax(1), p) for name, p in probs.items()}
        record = dict(fold=k, best_epoch=3, epochs=5, train_seconds=60.0, eval_seconds=5.0,
                      history={"loss": [1.0] * 5, "val_loss": [1.0] * 5, "accuracy": [0.5] * 5,
                               "val_accuracy": [0.5] * 5},
                      metrics=metrics, split_fingerprint=fingerprint, gpu=["NVIDIA GeForce RTX 4090"])
        mx.save_fold_outputs(str(root), record, probs, test_files=test_files, val_files=val_files,
                             test_true=test_true, val_true=val_true)
        all_probs.append(probs)
    return all_probs, val_true


def test_ensemble_is_the_mean_of_the_saved_fold_probabilities(tmp_path):
    all_probs, val_true = fake_fold_outputs(tmp_path)
    agg = mx.aggregate(str(tmp_path), n_folds=3)
    for proto, key in [("paper", "val_aug"), ("clean", "val_clean")]:
        mean = np.mean([p[key] for p in all_probs], 0)
        assert agg["ensemble"][proto]["accuracy"] == pytest.approx(float(np.mean(mean.argmax(1) == val_true)))


def test_aggregate_refuses_folds_from_different_splits(tmp_path):
    fake_fold_outputs(tmp_path / "a", n_folds=2, fingerprint="one")
    fake_fold_outputs(tmp_path / "b", n_folds=3, fingerprint="two")
    os.rename(tmp_path / "b" / "fold_2", tmp_path / "a" / "fold_2")
    with pytest.raises(ValueError, match="split"):
        mx.aggregate(str(tmp_path / "a"), n_folds=3)


def test_comparison_uses_the_papers_true_precision_and_recall(tmp_path):
    fake_fold_outputs(tmp_path)
    cmp = mx.aggregate(str(tmp_path), n_folds=3)["comparison"].set_index("Metric")
    assert cmp.loc["Ensemble recall (parasitized)", "Paper"] == 97.74
    assert cmp.loc["Ensemble precision (parasitized)", "Paper"] == 98.82
    assert cmp.loc["Ensemble accuracy", "Paper"] == 98.29


def test_written_results_work_with_check_results(tmp_path):
    fake_fold_outputs(tmp_path / "folds")
    out = tmp_path / "results"
    mx.write_results(mx.aggregate(str(tmp_path / "folds"), n_folds=3), str(out))
    script = os.path.join(os.path.dirname(__file__), "..", "src", "check_results.py")
    r = __import__("subprocess").run([sys.executable, script, str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "Mean fold accuracy" in r.stdout and "Folds run         : 3 of 3" in r.stdout


def test_available_cpus_respects_the_container_quota(tmp_path):
    quota = tmp_path / "cpu.max"
    quota.write_text("1360000 100000\n")  # what a "16 vCPU" RunPod pod actually allows: 13.6 CPUs
    assert mx.available_cpus(cgroup_file=str(quota)) == 13
    quota.write_text("max 100000\n")      # no quota
    assert 1 <= mx.available_cpus(cgroup_file=str(quota)) <= os.cpu_count()


def test_fold_outputs_with_pandas_file_names_load_back(tmp_path):
    # train_fold passes df["file"].values: an object array, which np.savez would pickle
    files = pd.Series(["C1P_cell_1.png", "C2N_cell_2.png"]).values
    probs = {name: np.array([[0.9, 0.1], [0.2, 0.8]]) for name in mx.EVAL_SETS}
    record = dict(fold=0, metrics={}, split_fingerprint="x")
    mx.save_fold_outputs(str(tmp_path), record, probs, test_files=files, val_files=files,
                         test_true=np.array([0, 1]), val_true=np.array([0, 1]))
    loaded = mx.load_fold(str(tmp_path / "fold_0"))
    assert list(loaded["npz"]["val_files"]) == list(files)


def test_available_cpus_reads_a_cgroup_v1_quota(tmp_path):
    (tmp_path / "cpu.cfs_quota_us").write_text("1360000\n")  # RunPod EU-RO-1 host: cgroup v1, 32 CPUs visible
    (tmp_path / "cpu.cfs_period_us").write_text("100000\n")
    assert mx.available_cpus(cgroup_file=str(tmp_path / "missing"), cgroup_v1_dir=str(tmp_path)) == 13
    (tmp_path / "cpu.cfs_quota_us").write_text("-1\n")       # no quota
    assert mx.available_cpus(cgroup_file=str(tmp_path / "missing"), cgroup_v1_dir=str(tmp_path)) >= 1


def test_augmentation_workers_use_single_threaded_blas(tiny_cache):
    # 11 workers each starting an OpenBLAS/OpenMP pool on a 13.6-CPU pod cut throughput 3x (957 vs 2884 img/s)
    with mx.AugmentPool(2, tiny_cache) as pool:
        env = pool._pool.apply(mx._worker_env)
    assert env == {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
