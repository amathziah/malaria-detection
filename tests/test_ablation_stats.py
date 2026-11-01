"""Tests for src/ablation_stats.py: the statistics that answer H1 and H2."""
import os
import sys

import numpy as np
import pytest
from scipy import stats as sps
from sklearn.metrics import matthews_corrcoef, roc_auc_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import ablation_stats as st  # noqa: E402
from conftest import write_experiment  # noqa: E402


# --------------------------------------------------------------------------- corrected resampled t-test
def test_corrected_t_test_uses_the_nadeau_bengio_variance():
    d = np.arange(1, 11, dtype=float)
    t, p = st.corrected_resampled_ttest(d, n_train=18_000, n_test=2_000)
    expected_t = d.mean() / np.sqrt((1 / 10 + 2_000 / 18_000) * d.var(ddof=1))
    assert t == pytest.approx(expected_t)
    assert p == pytest.approx(2 * sps.t.sf(abs(expected_t), df=9))
    naive_t = d.mean() / np.sqrt(d.var(ddof=1) / 10)
    assert t < naive_t  # the correction widens the interval: overlapping training sets


def test_corrected_t_test_refuses_identical_differences():
    with pytest.raises(ValueError):
        st.corrected_resampled_ttest(np.ones(10), 18_000, 2_000)


def test_holm_matches_the_textbook_example():
    np.testing.assert_allclose(st.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    np.testing.assert_allclose(st.holm([0.5, 0.9]), [1.0, 1.0])


# --------------------------------------------------------------------------- weighted metrics
def random_case(n=300, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, n)               # 0 = parasitized (mx.TIPOS order)
    score = np.clip(0.5 + (0.5 - y) * 0.6 + rng.normal(0, 0.3, n), 0, 1)  # P(parasitized)
    return y, score


@pytest.mark.parametrize("name", ["accuracy", "recall", "specificity", "balanced_accuracy", "mcc", "f2", "auc"])
def test_metrics_with_unit_weights_match_sklearn(name):
    y, s = random_case()
    pos, pred = y == 0, s >= 0.5
    tp, fn = (pos & pred).sum(), (pos & ~pred).sum()
    fp, tn = (~pos & pred).sum(), (~pos & ~pred).sum()
    expected = dict(accuracy=(tp + tn) / len(y), recall=tp / (tp + fn), specificity=tn / (tn + fp),
                    balanced_accuracy=(tp / (tp + fn) + tn / (tn + fp)) / 2,
                    mcc=matthews_corrcoef(pos, pred), f2=5 * tp / (5 * tp + 4 * fn + fp),
                    auc=roc_auc_score(pos, s))[name]
    assert st.METRICS[name](y, s, np.ones(len(y))) == pytest.approx(expected)


def test_prediction_rule_is_the_softmax_argmax():
    # argmax([0.5, 0.5]) is class 0 = parasitized, so P(parasitized) = 0.5 counts as parasitized
    y = np.array([0, 1])
    assert st.METRICS["accuracy"](y, np.array([0.5, 0.49]), np.ones(2)) == 1.0


# --------------------------------------------------------------------------- patient bootstrap
def test_bootstrap_resamples_whole_patients():
    # patient A: all 4 cells right; patient B: all 4 wrong -> accuracy of a resample is 0, 0.5 or 1
    y = np.zeros(8, int)
    s = np.array([0.9] * 4 + [0.1] * 4)
    groups = np.array(["A"] * 4 + ["B"] * 4)
    r = st.cluster_bootstrap(y, s, groups, "accuracy", n_boot=500, seed=1)
    assert set(np.round(r["boot"], 6)) <= {0.0, 0.5, 1.0}
    assert r["est"] == 0.5


def test_paired_bootstrap_of_identical_arms_is_zero():
    y, s = random_case()
    groups = np.repeat(np.arange(30), 10)
    r = st.paired_cluster_bootstrap(y, s, s, groups, "mcc", n_boot=300)
    assert (r["est"], r["lo"], r["hi"]) == (0.0, 0.0, 0.0)


def test_paired_bootstrap_finds_a_real_improvement():
    y, s = random_case(600, seed=2)
    better = np.where(y == 0, np.maximum(s, 0.8), np.minimum(s, 0.2))  # B fixes A's mistakes
    groups = np.repeat(np.arange(60), 10)
    r = st.paired_cluster_bootstrap(y, s, better, groups, "mcc", n_boot=1000)
    assert r["est"] > 0 and r["lo"] > 0 and r["p"] < 0.01


def test_unpaired_bootstrap_is_b_minus_a_on_different_cells():
    ya, sa = random_case(200, seed=3)
    yb = np.zeros(100, int)
    sb = np.full(100, 0.9)  # arm B: every cell right
    r = st.unpaired_cluster_bootstrap(ya, sa, np.repeat(np.arange(20), 10),
                                      yb, sb, np.repeat(np.arange(10), 10), "accuracy", n_boot=500)
    assert r["est"] == pytest.approx(1.0 - st.METRICS["accuracy"](ya, sa, np.ones(200)))
    assert r["lo"] > 0


# --------------------------------------------------------------------------- calibration and threshold
def test_expected_calibration_error_is_zero_for_perfect_confident_predictions():
    y = np.array([0, 0, 1, 1])
    assert st.expected_calibration_error(y, np.array([1.0, 1.0, 0.0, 0.0])) == 0.0
    assert st.expected_calibration_error(y, np.array([0.0, 0.0, 1.0, 1.0])) == pytest.approx(1.0)


def test_threshold_from_cv_maximises_f2_on_out_of_fold_predictions():
    y = np.array([0, 0, 0, 1, 1, 1])
    s = np.array([0.9, 0.35, 0.3, 0.2, 0.1, 0.05])  # at 0.5 two infected cells are missed
    t = st.threshold_from_cv(y, s)
    assert 0.2 < t <= 0.3
    assert st.METRICS["recall"](y, s, np.ones(6), threshold=t) == 1.0


# --------------------------------------------------------------------------- the whole analysis
def test_analyse_answers_the_three_questions(results_root, tmp_path):
    out = st.analyse(results_root, out_dir=str(tmp_path), n_boot=200)
    contrasts = {c["contrast"]: c for c in out["contrasts"]}
    assert set(contrasts) == {"A1 vs A0", "A2 vs A1", "A3 vs A0"}
    assert contrasts["A1 vs A0"]["paired"] is False
    assert contrasts["A2 vs A1"]["paired"] is True and contrasts["A3 vs A0"]["paired"] is True
    assert contrasts["A1 vs A0"]["ensemble"]["mcc"]["est"] < 0  # the fake A1 is much worse
    for c in out["contrasts"]:
        assert 0 <= c["ensemble"]["mcc"]["p_holm"] <= 1
    text = open(os.path.join(tmp_path, "ablation_summary.md")).read()
    assert "H1" in text and "H2" in text and "Holm" in text
    assert os.path.exists(os.path.join(tmp_path, "ablation_summary.csv"))
    assert os.path.exists(os.path.join(tmp_path, "ablation_per_patient.csv"))
    saved = __import__("json").load(open(os.path.join(tmp_path, "ablation_summary.json")))
    assert len(saved["verdicts"]) == 3 and saved["verdicts"][0].startswith("- **H1")


def test_analyse_lists_missing_experiments_instead_of_failing(tmp_path):
    root = str(tmp_path / "results")
    write_experiment(root, "A0", 0, 0.8)
    out = st.analyse(root, out_dir=str(tmp_path / "out"), n_boot=50)
    assert out["missing"] == ["A1", "A2", "A3"]
    assert out["contrasts"] == []


def test_paired_contrasts_refuse_different_hold_out_sets(results_root, tmp_path):
    a = st.load_experiment(results_root, "A0")
    b = st.load_experiment(results_root, "A1")
    with pytest.raises(ValueError, match="hold-out"):
        st.compare(a, b, paired=True, n_boot=50)
