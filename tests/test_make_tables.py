"""Tests for docs/ieee/make_tables.py: the paper's tables are written from results/, never typed by hand."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "docs", "ieee"))
import make_tables as mt  # noqa: E402


def experiment_row(**overrides):
    row = dict(experiment="A1", split="patient", preprocess="none", holdout_cells=5550, holdout_patients=40,
               fold_mcc_mean=0.9392, fold_mcc_sd=0.0151, fold_accuracy_mean=0.9724, fold_accuracy_sd=0.0066,
               cv_threshold=0.18947, recall_at_cv_threshold=0.99218, specificity_at_cv_threshold=0.93931,
               ece=0.06496)
    for metric, (est, lo, hi) in dict(accuracy=(0.9845, 0.9794, 0.9891), mcc=(0.9690, 0.9583, 0.9781),
                                      recall=(0.9805, 0.9701, 0.9884), auc=(0.9980, 0.9961, 0.9992)).items():
        row[f"ens_{metric}"], row[f"ens_{metric}_lo"], row[f"ens_{metric}_hi"] = est, lo, hi
    row.update(overrides)
    return row


def phase3b_summary():
    """The parts of results/phase3b/phase3b_summary.json that Table VI reads, with the paper's values."""
    mcc = lambda est, lo, hi: dict(est=est, lo=lo, hi=hi)
    e1 = lambda contrast, level, est, lo90, hi90, eq: dict(contrast=contrast, level=level, metric="mcc", est=est,
                                                         lo90=lo90, hi90=hi90, equivalent=eq)
    return {
        "E1": {"rows": [e1("A2 vs A1", "ensemble", -0.0026, -0.0073, 0.0016, True),
                        e1("A2 vs A1", "fold", -0.0060, -0.0127, 0.0006, False),
                        e1("A3 vs A0", "ensemble", 0.0, -0.0044, 0.0044, True),
                        e1("A3 vs A0", "fold", -0.0037, -0.0077, 0.0003, True),
                        dict(contrast="A1 vs A0", level="ensemble (different cells)", metric="mcc", est=0.0162)]},
        "E2": {"holdout": dict(n_cells=1095, n_patients=40, mcc=mcc(0.0, -0.0090, 0.0098)),
               "oof": dict(n_cells=17591, n_patients=160, mcc=mcc(-0.0085, -0.0202, -0.0005))},
        "E3": {"holdout": dict(tp=26, n_infected=28, sens_ci=[0.765, 0.991], tn=12, n_healthy=12,
                               spec_ci=[0.735, 1.0])},
    }


def column_spec(tex):
    return tex.split(r"\begin{tabular}{")[1].replace("@{}", "").split("}")[0]


def last_header_row(tex):
    """The header row right above the first \\midrule: it names one column per column spec."""
    lines = tex.splitlines()
    return lines[lines.index(r"\midrule") - 1]


def contrasts_summary():
    r = dict(est=-0.0165, lo=-0.0328, hi=-0.0002, p_holm=0.142)
    level = {m: dict(r) for m in ("mcc", "accuracy", "recall", "specificity", "auc")}
    return {"contrasts": [dict(contrast=c, fold=level, ensemble=level) for c in ("A1 vs A0", "A2 vs A1", "A3 vs A0")]}


TABLES = {
    "reproduction": lambda: mt.reproduction_table({
        "paper": dict(mean_fold_accuracy=97.56, accuracy=98.29, recall=97.74, precision=98.82, specificity=98.84,
                      f1=98.28, auc=99.76),
        **{k: dict(accuracy=97.6, recall=97.1, precision=98.1, specificity=98.2, f1=97.6, auc=99.7)
           for k in ("ensemble", "ensemble_clean")},
        "mean_fold": dict(accuracy=97.55), "mean_fold_clean": dict(accuracy=97.78)}),
    "experiments": lambda: mt.experiments_table({"experiments": [experiment_row()]}),
    "contrasts": lambda: mt.contrasts_table(contrasts_summary()),
    "extras": lambda: mt.extras_table({"experiments": [experiment_row()]}),
    "phase3b": lambda: mt.phase3b_table(phase3b_summary()),
}


@pytest.mark.parametrize("name", sorted(TABLES))
def test_every_table_names_one_column_per_column_spec(name):
    tex = TABLES[name]()
    assert len(column_spec(tex)) == last_header_row(tex).count("&") + 1


@pytest.mark.parametrize("name", sorted(TABLES))
def test_no_table_uses_a_dash_as_punctuation(name):
    tex = TABLES[name]()
    assert "---" not in tex and "—" not in tex
    assert "Nadeau--Bengio" not in tex


def test_experiments_table_reports_the_ensemble_roc_auc_with_its_interval():
    tex = mt.experiments_table({"experiments": [experiment_row()]})
    assert "ROC-AUC" in last_header_row(tex)
    assert "99.80" in tex and "[99.61, 99.92]" in tex


def test_experiments_table_groups_its_columns_under_a_two_row_header():
    tex = mt.experiments_table({"experiments": [experiment_row()]})
    assert r"\multicolumn{2}{c}{Hold-out set}" in tex
    assert r"\multicolumn{4}{c}{Ensemble on the hold-out set [95\,\% CI]}" in tex
    assert tex.count(r"\cmidrule") == 3


def test_experiments_table_gives_cells_and_patients_their_own_columns():
    tex = mt.experiments_table({"experiments": [experiment_row()]})
    assert "A1 & patient & none & 5{,}550 & 40 &" in tex


def test_experiments_table_only_shrinks_when_too_wide():
    tex = mt.experiments_table({"experiments": [experiment_row()]})
    assert r"\resizebox{\ifdim\width>\textwidth\textwidth\else\width\fi}{!}" in tex


def test_extras_table_gives_recall_at_05_and_at_the_threshold_their_own_columns():
    tex = mt.extras_table({"experiments": [experiment_row()]})
    assert r"A1 & 0.189 & 98.05 & 99.22 & 93.93 & 0.065 \\" in tex
    assert r"$\to$" not in tex


def test_phase3b_table_gives_the_equivalence_verdict_its_own_column():
    tex = mt.phase3b_table(phase3b_summary())
    assert "Within" in tex
    assert r"H2, ensembles & $-$0.26 & [$-$0.73, +0.16] & yes \\" in tex
    assert r"H2, folds & $-$0.60 & [$-$1.27, +0.06] & no \\" in tex


def test_phase3b_table_separates_its_three_groups_and_writes_patients_in_full():
    tex = mt.phase3b_table(phase3b_summary())
    assert tex.count(r"\addlinespace") == 2
    assert "pts" not in tex
    assert r"Ensembles, 40 patients & +0.00 & [$-$0.90, +0.98] & \\" in tex
    assert r"Sensitivity, 26/28 & 92.9 & [76.5, 99.1] & \\" in tex
