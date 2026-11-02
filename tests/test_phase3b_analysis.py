"""Tests for src/phase3b_analysis.py: the exploratory analyses fixed in docs/phase3b_addendum.md (E1-E4)."""
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest
from PIL import Image
from scipy import stats as sps

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import phase3b_analysis as p3  # noqa: E402

# Conventions shared with ablation_stats: y 0 = parasitized, 1 = uninfected; s = P(parasitized), parasitized if s >= t.


# --------------------------------------------------------------------------- E1: equivalence and detectable effects
def test_tost_from_boot_declares_equivalence_when_the_90_percent_interval_is_inside_the_margin():
    boot = np.tile([-0.004, -0.002, 0.0, 0.002, 0.004], 200)
    r = p3.tost_from_boot(boot, margin=0.01)
    assert (r["lo90"], r["hi90"]) == pytest.approx((-0.004, 0.004))
    assert r["equivalent"] is True
    assert r["smallest_margin"] == pytest.approx(0.004)
    assert r["p_tost"] == pytest.approx(1 / 1000)  # no resample beyond the margin: floored at 1 / n_boot


def test_tost_from_boot_refuses_equivalence_when_the_interval_crosses_the_margin():
    boot = np.tile([0.0045, 0.0065, 0.0085, 0.0105, 0.0125], 200)
    r = p3.tost_from_boot(boot, margin=0.01)
    assert r["equivalent"] is False
    assert r["hi90"] == pytest.approx(0.0125)
    assert r["p_tost"] == pytest.approx(0.4)  # 400 of 1,000 resamples at or above +0.01


def test_tost_from_boot_uses_the_5th_and_95th_percentiles():
    # two one-sided 5 % tests = a 90 % interval; a 95 % interval here would be [-0.019, 0.019]
    r = p3.tost_from_boot(np.linspace(-0.02, 0.02, 1001), margin=0.0185)
    assert (r["lo90"], r["hi90"]) == pytest.approx((-0.018, 0.018))
    assert r["equivalent"] is True


def test_tost_from_t_uses_the_t_distribution_with_the_given_df():
    # diff -0.6 pp, SE 0.4 pp, df 9: 90 % CI = -0.006 -+ 1.833113 * 0.004
    r = p3.tost_from_t(-0.006, 0.004, df=9, margin=0.01)
    assert r["lo90"] == pytest.approx(-0.013332, abs=1e-6)
    assert r["hi90"] == pytest.approx(0.001332, abs=1e-6)
    assert r["equivalent"] is False
    assert r["p_tost"] == pytest.approx(sps.t.sf(1.0, 9))  # the lower test, (diff + margin) / SE = 1, is the weaker
    assert r["smallest_margin"] == pytest.approx(0.013332, abs=1e-6)


def test_minimum_detectable_effect_for_80_percent_power():
    assert p3.mde(0.01) == pytest.approx(0.028016, abs=1e-5)         # (1.959964 + 0.841621) * SE
    assert p3.mde(0.01, df=9) == pytest.approx(0.031452, abs=1e-5)   # (2.262157 + 0.883029) * SE


def test_design_effect_equals_the_cluster_size_when_patients_are_all_right_or_all_wrong():
    # 20 patients x 10 cells, each patient entirely right or entirely wrong: ICC = 1, so deff = 1 + (10 - 1) * 1
    groups = np.repeat(np.arange(20), 10)
    y = np.zeros(200, int)
    s = np.where(groups < 10, 0.9, 0.1)
    r = p3.design_effect(y, s, groups, "accuracy", n_boot=2000, seed=0)
    assert 8 < r["deff"] < 12


# --------------------------------------------------------------------------- E2: leakage on identical cells
def test_align_returns_the_shared_files_in_the_first_arms_order():
    ia, ib = p3.align(np.array(["x", "y", "z"]), np.array(["z", "x", "w"]))
    assert list(ia) == [0, 2] and list(ib) == [1, 0]


def make_exp(val_files, val_true, val_scores, fold_files, fold_true, fold_scores):
    """The parts of ablation_stats.load_experiment's dict that the same-cell analysis reads."""
    return dict(val_files=np.asarray(val_files), val_true=np.asarray(val_true), ens_clean=np.asarray(val_scores, float),
                val_groups=np.array([f.split("P_")[0] for f in val_files]),
                fold_files=[np.asarray(f) for f in fold_files], fold_true=[np.asarray(t) for t in fold_true],
                fold_scores_clean=[np.asarray(s, float) for s in fold_scores])


def two_arms(wrong_patients=()):
    """30 patients x 6 cells shared by both arms; arm 1 gets every cell of `wrong_patients` wrong."""
    files = [f"C{p}P_cell_{i}.png" for p in range(30) for i in range(6)]
    y = [i % 2 for p in range(30) for i in range(6)]
    right = [0.95 if t == 0 else 0.05 for t in y]
    arm1 = [1 - r if int(f[1:].split("P")[0]) in wrong_patients else r for f, r in zip(files, right)]
    half = len(files) // 2
    e0 = make_exp(files, y, right, [files[:half], files[half:]], [y[:half], y[half:]], [right[:half], right[half:]])
    e1 = make_exp(files, y, arm1, [files[:half], files[half:]], [y[:half], y[half:]], [arm1[:half], arm1[half:]])
    return e0, e1


def test_same_cell_leakage_of_identical_predictions_is_equivalent_to_zero():
    e0, e1 = two_arms()
    r = p3.same_cell_leakage(e0, e1, n_boot=300, seed=0)
    for level in ["holdout", "oof"]:
        assert r[level]["n_cells"] == 180 and r[level]["n_patients"] == 30
        assert r[level]["mcc"]["est"] == 0.0
        assert r[level]["reading"] == "equivalent within ±1 pp"


def test_same_cell_leakage_detects_an_arm_that_fails_on_unseen_patients():
    e0, e1 = two_arms(wrong_patients=range(10))
    r = p3.same_cell_leakage(e0, e1, n_boot=300, seed=0)
    assert r["holdout"]["accuracy"]["est"] == pytest.approx(-10 / 30)
    assert r["holdout"]["reading"] == "leakage detected"


def test_leakage_reading_is_inconclusive_when_the_interval_is_wide():
    assert p3.leakage_reading(dict(hi=0.01, lo90=-0.02, hi90=0.005)) == "inconclusive"
    assert p3.leakage_reading(dict(hi=-0.001, lo90=-0.009, hi90=-0.002)) == "leakage detected"
    assert p3.leakage_reading(dict(hi=0.004, lo90=-0.006, hi90=0.003)) == "equivalent within ±1 pp"


# --------------------------------------------------------------------------- E3: patient-level diagnosis
def test_patient_truth_marks_a_patient_infected_if_any_cell_is_parasitized():
    assert p3.patient_truth(np.array(["A", "A", "B"]), np.array([0, 1, 1])) == {"A": True, "B": False}


def test_patient_calls_count_cells_at_or_above_the_threshold():
    g, s = np.array(["A", "A", "B"]), np.array([0.9, 0.2, 0.6])
    assert p3.patient_calls(g, s, t=0.5, tau=1) == {"A": True, "B": True}
    assert p3.patient_calls(g, s, t=0.5, tau=2) == {"A": False, "B": False}
    assert p3.patient_calls(g, s, t=0.6, tau=1) == {"A": True, "B": True}  # 0.6 >= 0.6


def test_sens_spec_counts_patients_not_cells():
    r = p3.sens_spec({"A": True, "B": False, "C": True}, {"A": True, "B": False, "C": False})
    assert (r["sens"], r["spec"], r["n_infected"], r["n_healthy"]) == (0.5, 1.0, 2, 1)


def four_patients(prefix=""):
    """P1 infected (3 strong cells), P2 infected (1 strong cell), H1 healthy with one 0.6 false alarm, H2 clean."""
    g, y, s = [], [], []
    for name, cells in [("P1", [(0, 0.9)] * 3 + [(1, 0.1)] * 3), ("P2", [(0, 0.9)] + [(1, 0.1)] * 5),
                        ("H1", [(1, 0.6)] + [(1, 0.1)] * 5), ("H2", [(1, 0.1)] * 6)]:
        for label, score in cells:
            g.append(prefix + name)
            y.append(label)
            s.append(score)
    return np.array(g), np.array(y), np.array(s)


def test_select_rule_takes_the_best_youden_j_among_rules_with_95_percent_specificity():
    g, y, s = four_patients()
    r = p3.select_rule(g, y, s, ts=[0.5, 0.8], taus=[1, 2])
    # (0.5, 1) flags H1 (spec 0.5); (0.5, 2) and (0.8, 2) miss P2 (J 0.5); (0.8, 1) is perfect (J 1)
    assert (r["t"], r["tau"]) == (0.8, 1)
    assert (r["sens"], r["spec"], r["meets_min_spec"]) == (1.0, 1.0, True)


def test_select_rule_breaks_ties_toward_the_smaller_tau_then_the_smaller_t():
    g = np.repeat(["P1", "P2", "H1"], 4)
    y = np.array([0] * 8 + [1] * 4)
    s = np.array([0.99] * 8 + [0.01] * 4)
    r = p3.select_rule(g, y, s, ts=[0.8, 0.5], taus=[2, 1])
    assert (r["t"], r["tau"]) == (0.5, 1)


def test_select_rule_falls_back_to_the_best_j_when_no_rule_reaches_the_specificity_floor():
    g, y, s = four_patients()
    s = np.where(g == "H1", 0.999, s)  # H1 now looks infected under every rule
    r = p3.select_rule(g, y, s, ts=[0.5, 0.8], taus=[1, 2])
    assert r["meets_min_spec"] is False
    assert (r["t"], r["tau"], r["spec"]) == (0.5, 1, 0.5)


def test_nested_selection_scores_each_fold_with_a_rule_chosen_on_the_others():
    parts = [four_patients(prefix=f"F{k}") for k in range(4)]
    g = np.concatenate([p[0] for p in parts])
    y = np.concatenate([p[1] for p in parts])
    s = np.concatenate([p[2] for p in parts])
    folds = np.repeat(np.arange(4), len(parts[0][0]))
    r = p3.nested_rule_selection(g, y, s, folds, ts=[0.5, 0.8], taus=[1, 2])
    assert [(x["t"], x["tau"]) for x in r["rules"]] == [(0.8, 1)] * 4
    assert (r["sens"], r["spec"], r["n_infected"], r["n_healthy"]) == (1.0, 1.0, 8, 8)


def test_clopper_pearson_exact_limits():
    assert p3.clopper_pearson(12, 12) == pytest.approx((0.025 ** (1 / 12), 1.0))   # 0.7354
    assert p3.clopper_pearson(0, 12) == pytest.approx((0.0, 1 - 0.025 ** (1 / 12)))
    lo, hi = p3.clopper_pearson(11, 12)
    assert lo == pytest.approx(0.6152, abs=1e-4) and hi == pytest.approx(0.975 ** (1 / 12))


def test_dilution_keeps_m_parasitized_cells_per_infected_patient():
    g = np.array(["P"] * 8 + ["H"] * 3)
    y = np.array([0] * 5 + [1] * 3 + [1] * 3)
    s = np.array([0.9] * 5 + [0.1] * 3 + [0.1] * 3)
    assert p3.dilution_sensitivity(g, y, s, t=0.5, tau=2, m=1, n_draws=50, seed=0) == 0.0
    assert p3.dilution_sensitivity(g, y, s, t=0.5, tau=2, m=2, n_draws=50, seed=0) == 1.0


def test_dilution_with_one_detectable_cell_of_two_finds_the_patient_half_the_time():
    g = np.array(["P", "P", "P"])
    y = np.array([0, 0, 1])
    s = np.array([0.9, 0.1, 0.1])
    x = p3.dilution_sensitivity(g, y, s, t=0.5, tau=1, m=1, n_draws=2000, seed=0)
    assert 0.45 < x < 0.55


# --------------------------------------------------------------------------- E4: error audit
def test_false_alarm_rates_are_split_by_the_patients_status():
    g = np.array(["A"] * 6 + ["B"] * 4)
    y = np.array([0, 0, 1, 1, 1, 1] + [1] * 4)
    s = np.array([0.9, 0.9, 0.9, 0.9, 0.1, 0.1] + [0.1] * 4)
    r = p3.false_alarm_by_status(g, y, s, n_boot=200, seed=0)
    assert (r["infected"]["flagged"], r["infected"]["cells"], r["infected"]["rate"]) == (2, 4, 0.5)
    assert (r["healthy"]["flagged"], r["healthy"]["cells"], r["healthy"]["rate"]) == (0, 4, 0.0)
    assert r["difference"]["est"] == 0.5


def test_error_dispersion_test_flags_errors_piled_on_one_patient():
    g = np.repeat(np.arange(10), 10)
    y = np.ones(100, int)
    s = np.where(g == 0, 0.9, 0.1)  # all 10 errors in patient 0
    r = p3.error_dispersion_test(g, y, s, n_perm=500, seed=0)
    assert r["stat"] == pytest.approx(90.0)   # (10 - 1)^2 / 1 + 9 * (0 - 1)^2 / 1
    assert r["p"] < 0.01


def test_error_dispersion_test_accepts_errors_spread_one_per_patient():
    g = np.repeat(np.arange(10), 10)
    y = np.ones(100, int)
    s = np.where(np.arange(100) % 10 == 0, 0.9, 0.1)  # exactly one error per patient
    r = p3.error_dispersion_test(g, y, s, n_perm=500, seed=0)
    assert r["stat"] == pytest.approx(0.0)
    assert r["p"] == 1.0


def test_confident_learning_flags_cells_confidently_predicted_as_the_other_class():
    y = np.array([0, 0, 0, 1, 1, 1])
    s = np.array([0.95, 0.9, 0.05, 0.1, 0.05, 0.97])
    mask, thr = p3.confident_learning_candidates(y, s)
    assert list(mask) == [False, False, True, False, False, True]
    assert thr["parasitized"] == pytest.approx((0.95 + 0.9 + 0.05) / 3)
    assert thr["uninfected"] == pytest.approx((0.9 + 0.95 + 0.03) / 3)


def test_blinded_gallery_mixes_errors_with_label_matched_controls(tmp_path):
    img_dir = tmp_path / "cells"
    for cls in ["Parasitized", "Uninfected"]:
        (img_dir / cls).mkdir(parents=True)
    files = [f"C{i}P_cell_{i}.png" for i in range(8)]
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    s = np.array([0.1, 0.9, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1])  # one missed parasite, one false alarm
    for f, label in zip(files, y):
        Image.new("RGB", (20, 24), (200, 100, 120)).save(img_dir / ("Parasitized" if label == 0 else "Uninfected") / f)
    key = p3.blinded_gallery(np.array(files), y, s, str(img_dir), str(tmp_path / "g.png"), str(tmp_path / "k.csv"))
    assert os.path.exists(tmp_path / "g.png")
    saved = pd.read_csv(tmp_path / "k.csv")
    assert len(saved) == 4 and saved["error"].sum() == 2
    assert set(saved.loc[saved["error"], "file"]) == {files[0], files[4]}
    assert sorted(saved.loc[~saved["error"], "label"]) == sorted(saved.loc[saved["error"], "label"])
    assert list(saved["id"]) == [1, 2, 3, 4]


# --------------------------------------------------------------------------- the whole analysis
def test_analyse_writes_every_part_of_the_addendum(results_root, tmp_path):
    out = p3.analyse(results_root, out_dir=str(tmp_path), n_boot=100, n_perm=100, n_draws=20, image_dir=None)
    saved = json.load(open(tmp_path / "phase3b_summary.json"))
    assert {"E1", "E2", "E3", "E4"} <= set(saved)
    assert saved["E2"]["holdout"]["n_cells"] == 0  # the fake A0 and A1 share no cells
    assert saved["E3"]["selected"]["tau"] in [1, 2, 3, 4, 5, 6, 8, 10, 12, 15]
    assert os.path.exists(tmp_path / "phase3b_summary.md")
    assert "E3" in out["text"] and "Disclosure" in out["text"]
    for fig in ["phase3b_leakage.png", "phase3b_equivalence.png", "phase3b_patient_level.png",
                "phase3b_reliability.png"]:
        assert os.path.getsize(tmp_path / fig) > 0
