"""Tests for the ablation switches (A1-A3): patient-grouped split and YUV preprocessing.

Run:  python -m pytest tests/ -q   (same environment as tests/test_marques2022_exact.py)
"""
import os
import subprocess
import sys

import cv2
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import marques2022_exact as mx  # noqa: E402

REPO = os.path.join(os.path.dirname(__file__), "..")


def patient_entries(n_patients=60, seed=0):
    """NIH-like names: infected patients (P token) have both classes, healthy ones only uninfected cells."""
    rng = np.random.default_rng(seed)
    entries = []
    for c in range(1, n_patients + 1):
        infected = c % 4 != 0
        n_par = int(rng.integers(5, 60)) if infected else 0
        n_uninf = int(rng.integers(20, 40))
        tag = f"C{c}P{c + 100}thinF" if infected else f"C{c}NThinF"
        entries += [(f"{tag}_IMG_2015_{c}_cell_{i}.png", "Parasitized") for i in range(n_par)]
        entries += [(f"{tag}_IMG_2015_{c}_cell_{1000 + i}.png", "Uninfected") for i in range(n_uninf)]
    return entries


def patients(frame):
    return set(frame["file"].map(mx.patient_id))


# --------------------------------------------------------------------------- experiments
def test_experiment_table_changes_one_thing_at_a_time():
    e = mx.EXPERIMENTS
    assert (e["A0"]["split"], e["A0"]["preprocess"]) == ("image", "none")
    assert (e["A1"]["split"], e["A1"]["preprocess"]) == ("patient", "none")
    assert (e["A2"]["split"], e["A2"]["preprocess"]) == ("patient", "yuv")
    assert (e["A3"]["split"], e["A3"]["preprocess"]) == ("image", "yuv")
    assert [e[k]["folder"] for k in ["A0", "A1", "A2", "A3"]] == [
        "A0_10fold_paper", "A1_slide_split", "A2_yuv_slide", "A3_yuv_image"]
    assert [e[k]["prefix"] for k in ["A0", "A1", "A2", "A3"]] == ["A0_10fold", "A1", "A2", "A3"]


# --------------------------------------------------------------------------- patient id and split
@pytest.mark.parametrize("name, expected", [
    ("C33P1thinF_IMG_20150619_114756a_cell_179.png", "C33"),
    ("C37BP2_thinF_IMG_20150620_133111a_cell_87.png", "C37"),
    ("C51AP12thinF_IMG_20150724_153246_cell_131.png", "C51"),
    ("C47P8thinOriginalOlympusCX21_IMG_1_cell_3.png", "C47"),  # NIH lists P8 under two keys: one patient
    ("C47P8thin_Original_Motic_IMG_2_cell_4.png", "C47"),
    ("C1_thinF_IMG_20150604_104722_cell_9.png", "C1"),
    ("C241NThinF_IMG_20151207_124643_cell_77.png", "C241"),
])
def test_patient_id_is_the_c_number(name, expected):
    assert mx.patient_id(name) == expected


def test_patient_id_rejects_names_without_a_c_number():
    with pytest.raises(ValueError):
        mx.patient_id("img_0.png")


def test_patient_split_has_no_shared_patients():
    df = mx.build_index(patient_entries())
    learn, val, folds = mx.make_split(df, "patient")
    assert not patients(learn) & patients(val)
    assert len(learn) + len(val) == len(df)
    tested = np.concatenate([te for _, te in folds])
    assert sorted(tested) == list(range(len(learn)))
    for tr, te in folds:
        assert not patients(learn.iloc[tr]) & patients(learn.iloc[te])


def test_patient_split_picks_the_outer_split_closest_to_20pct_and_balanced():
    from sklearn.model_selection import StratifiedGroupKFold
    df = mx.build_index(patient_entries())
    y = (df["label"] == "Parasitized").astype(int).values
    groups = df["file"].map(mx.patient_id).values
    scores = []
    for _, hold in StratifiedGroupKFold(5, shuffle=True, random_state=1234).split(df, y, groups):
        scores.append(abs(len(hold) / len(df) - 0.2) + abs(y[hold].mean() - 0.5))
    _, val = mx.patient_split(df)
    best = int(np.argmin(scores))
    expected_hold = list(StratifiedGroupKFold(5, shuffle=True, random_state=1234).split(df, y, groups))[best][1]
    assert sorted(val["file"]) == sorted(df["file"].values[expected_hold])


def test_make_split_refuses_a_patient_in_train_and_test(monkeypatch):
    df = mx.build_index(patient_entries())
    learn, val = mx.patient_split(df)
    leaky_val = pd.concat([val, learn.iloc[:1]])  # one learning-set patient leaks into the hold-out set
    monkeypatch.setattr(mx, "patient_split", lambda d, **kw: (learn, leaky_val.reset_index(drop=True)))
    with pytest.raises(ValueError, match="patient"):
        mx.make_split(df, "patient")


def test_image_split_is_unchanged_for_a0():
    df = mx.build_index(patient_entries())
    learn, val, folds = mx.make_split(df, "image")
    p_learn, p_val = mx.paper_split(df)
    assert mx.split_fingerprint(learn, val, folds) == mx.split_fingerprint(p_learn, p_val, mx.paper_folds(p_learn))


def test_unknown_split_is_an_error():
    with pytest.raises(ValueError):
        mx.make_split(mx.build_index(patient_entries()), "random")


def test_split_csv_round_trips(tmp_path):
    df = mx.build_index(patient_entries())
    learn, val, folds = mx.make_split(df, "patient")
    path = str(tmp_path / "split.csv")
    mx.save_split(path, learn, val, folds)
    saved = pd.read_csv(path)
    assert list(saved.columns) == ["file", "label", "patient", "role", "fold"]
    shuffled = df.sample(frac=1, random_state=3)  # e.g. a different os.listdir order on the pod
    l2, v2, f2 = mx.load_split(path, mx.build_index(shuffled[["file", "label"]].values))
    assert mx.split_fingerprint(l2, v2, f2) == mx.split_fingerprint(learn, val, folds)
    np.testing.assert_array_equal(l2["file"], learn["file"])


def test_load_split_refuses_a_dataset_that_does_not_match(tmp_path):
    df = mx.build_index(patient_entries())
    learn, val, folds = mx.make_split(df, "patient")
    path = str(tmp_path / "split.csv")
    mx.save_split(path, learn, val, folds)
    with pytest.raises(ValueError, match="split"):
        mx.load_split(path, df.iloc[5:].reset_index(drop=True))


# --------------------------------------------------------------------------- YUV preprocessing
def cell_like(seed=0, h=120, w=140):
    """A dim, low-contrast 'cell' on a pure black background, like the NIH crops."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[:h, :w]
    inside = (yy - h / 2) ** 2 / (h / 2.3) ** 2 + (xx - w / 2) ** 2 / (w / 2.3) ** 2 < 1
    img[inside] = rng.integers(120, 170, (inside.sum(), 3), dtype=np.uint8)
    return img, inside


def test_yuv_equalize_matches_the_opencv_reference():
    bgr, _ = cell_like()
    yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)
    yuv[..., 0] = cv2.equalizeHist(yuv[..., 0])
    expected = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
    np.testing.assert_array_equal(mx.yuv_equalize(bgr), expected)


def test_yuv_equalize_stretches_brightness_and_keeps_the_black_background():
    bgr, inside = cell_like()
    out = mx.yuv_equalize(bgr)
    assert out.dtype == np.uint8 and out.shape == bgr.shape
    assert (out[~inside] == 0).all()
    y_in = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)[..., 0][inside]
    y_out = cv2.cvtColor(out, cv2.COLOR_BGR2YUV)[..., 0][inside]
    assert np.ptp(y_out) > 2 * np.ptp(y_in)


def test_yuv_equalize_rejects_float_images():
    with pytest.raises(ValueError):
        mx.yuv_equalize(np.zeros((4, 4, 3), np.float32))


def test_load_resized_applies_yuv_before_the_nearest_neighbour_resize(tmp_path):
    bgr, _ = cell_like(1)
    p = str(tmp_path / "c.png")
    cv2.imwrite(p, bgr)
    expected = cv2.resize(cv2.cvtColor(mx.yuv_equalize(bgr), cv2.COLOR_BGR2RGB), (224, 224),
                          interpolation=cv2.INTER_NEAREST)
    np.testing.assert_array_equal(mx.load_resized(p, preprocess="yuv"), expected)
    np.testing.assert_array_equal(mx.load_resized(p, preprocess="none"), mx.load_resized(p))
    with pytest.raises(ValueError):
        mx.load_resized(p, preprocess="lab")


def test_yuv_cache_differs_from_rgb_cache_only_by_preprocessing(tmp_path):
    paths = []
    for k in range(5):
        p = str(tmp_path / f"c{k}.png")
        cv2.imwrite(p, cell_like(k)[0])
        paths.append(p)
    rgb = np.load(mx.build_image_cache(paths, str(tmp_path / "rgb.npy"), workers=0))
    yuv = np.load(mx.build_image_cache(paths, str(tmp_path / "yuv.npy"), workers=0, preprocess="yuv"))
    for k, p in enumerate(paths):
        np.testing.assert_array_equal(rgb[k], mx.load_resized(p))
        np.testing.assert_array_equal(yuv[k], mx.load_resized(p, preprocess="yuv"))
    assert mx.cache_preprocess(str(tmp_path / "yuv.npy")) == "yuv"
    assert mx.cache_preprocess(str(tmp_path / "rgb.npy")) == "none"


def test_train_fold_refuses_a_cache_with_the_wrong_preprocessing(tmp_path):
    entries = patient_entries(12)
    folder = tmp_path / "imgs"
    folder.mkdir()
    for f, _ in entries[:8]:
        cv2.imwrite(str(folder / f), cell_like(0, 30, 30)[0])
    df = mx.build_index(entries[:8], root=str(folder))
    cache = mx.build_image_cache(list(df["path"]), str(tmp_path / "c.npy"), workers=0)  # RGB cache
    with mx.AugmentPool(0, cache) as pool, pytest.raises(ValueError, match="preprocess"):
        mx.train_fold(0, learn=df, val=df, folds=[(np.arange(4), np.arange(4, 8))], pool=pool,
                      out_dir=str(tmp_path / "out"), weights=None, experiment="A2")


# --------------------------------------------------------------------------- aggregation
def fake_patient_fold_outputs(root, experiment="A1", n_folds=3, seed=0, leak=False, fingerprint="abc"):
    """train_fold-format outputs on a patient split: hold-out patients C100+, fold k tests patients C{10k..10k+9}."""
    rng = np.random.default_rng(seed)
    val_files = np.array([f"C{100 + i % 5}P_cell_{i}.png" for i in range(40)])
    val_true = np.arange(40) % 2
    for k in range(n_folds):
        first = 10 * k if not (leak and k == 1) else 100  # leak: fold 1 tests a hold-out patient
        test_files = np.array([f"C{first + i % 10}P_cell_{k}_{i}.png" for i in range(20)])
        test_true = np.arange(20) % 2
        probs = {}
        for name, n in [("test_aug", 20), ("test_clean", 20), ("val_aug", 40), ("val_clean", 40)]:
            p0 = rng.random(n)
            probs[name] = np.stack([p0, 1 - p0], 1)
        metrics = {name: mx.classification_summary(test_true if name.startswith("test") else val_true,
                                                   p.argmax(1), p) for name, p in probs.items()}
        e = mx.EXPERIMENTS[experiment]
        record = dict(fold=k, best_epoch=3, epochs=5, train_seconds=60.0, eval_seconds=5.0,
                      history={"loss": [1.0] * 5, "val_loss": [1.0] * 5, "accuracy": [0.5] * 5,
                               "val_accuracy": [0.5] * 5},
                      metrics=metrics, split_fingerprint=fingerprint, gpu=["NVIDIA GeForce RTX 4090"],
                      experiment=experiment, split=e["split"], preprocess=e["preprocess"])
        mx.save_fold_outputs(str(root), record, probs, test_files=test_files, val_files=val_files,
                             test_true=test_true, val_true=val_true)


def test_aggregate_refuses_mixed_experiments(tmp_path):
    fake_patient_fold_outputs(tmp_path / "a", "A1")
    fake_patient_fold_outputs(tmp_path / "b", "A2")
    __import__("shutil").rmtree(tmp_path / "a" / "fold_2")
    os.rename(tmp_path / "b" / "fold_2", tmp_path / "a" / "fold_2")  # an A2 fold among A1 folds
    with pytest.raises(ValueError, match="experiment"):
        mx.aggregate(str(tmp_path / "a"), n_folds=3)


def test_aggregate_rechecks_patient_leakage_from_the_saved_file_lists(tmp_path):
    fake_patient_fold_outputs(tmp_path / "ok", "A1")
    agg = mx.aggregate(str(tmp_path / "ok"), n_folds=3)
    assert agg["experiment"] == "A1"
    assert agg["n_patients_holdout"] == 5
    fake_patient_fold_outputs(tmp_path / "leak", "A1", leak=True)
    with pytest.raises(ValueError, match="patient"):
        mx.aggregate(str(tmp_path / "leak"), n_folds=3)


def test_old_a0_fold_records_still_aggregate_as_a0(tmp_path):
    from test_marques2022_exact import fake_fold_outputs  # records without the "experiment" key
    fake_fold_outputs(tmp_path)
    assert mx.aggregate(str(tmp_path), n_folds=3)["experiment"] == "A0"


def test_write_results_records_experiment_split_and_preprocess(tmp_path):
    fake_patient_fold_outputs(tmp_path / "folds", "A2")
    agg = mx.aggregate(str(tmp_path / "folds"), n_folds=3)
    s = mx.write_results(agg, str(tmp_path / "out"), prefix="A2")
    assert s["experiment"] == "A2"
    assert s["split"].startswith("patient") and s["preprocess"].startswith("yuv")
    assert s["n_patients_holdout"] == 5
    assert s["holdout_class_counts"] == {"Parasitized": 20, "Uninfected": 20}
    for key in ["balanced_accuracy", "f2"]:
        assert key in s["ensemble"] and key in s["mean_fold"]
    assert os.path.exists(tmp_path / "out" / "A2_summary.json")
    assert os.path.exists(tmp_path / "out" / "A2_per_fold_val.csv")


def test_check_results_gives_the_paper_verdict_only_for_the_reproduction(tmp_path):
    script = os.path.join(REPO, "src", "check_results.py")
    r = subprocess.run([sys.executable, script, os.path.join(REPO, "results", "A0_10fold_paper")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "within 1 pp of the paper" in r.stdout
    fake_patient_fold_outputs(tmp_path / "folds", "A1")
    mx.write_results(mx.aggregate(str(tmp_path / "folds"), n_folds=3), str(tmp_path / "out"), prefix="A1")
    r = subprocess.run([sys.executable, script, str(tmp_path / "out")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "not a reproduction run" in r.stdout
