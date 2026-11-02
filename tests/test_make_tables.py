"""Tests for docs/ieee/make_tables.py: the paper's tables are written from results/, never typed by hand."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "docs", "ieee"))
import make_tables as mt  # noqa: E402


def experiment_row(**overrides):
    row = dict(experiment="A1", split="patient", preprocess="none", holdout_cells=5550, holdout_patients=40,
               fold_mcc_mean=0.9392, fold_mcc_sd=0.0151, fold_accuracy_mean=0.9724, fold_accuracy_sd=0.0066)
    for metric, (est, lo, hi) in dict(accuracy=(0.9845, 0.9794, 0.9891), mcc=(0.9690, 0.9583, 0.9781),
                                      recall=(0.9805, 0.9701, 0.9884), auc=(0.9980, 0.9961, 0.9992)).items():
        row[f"ens_{metric}"], row[f"ens_{metric}_lo"], row[f"ens_{metric}_hi"] = est, lo, hi
    row.update(overrides)
    return row


def test_experiments_table_reports_the_ensemble_roc_auc_with_its_interval():
    tex = mt.experiments_table({"experiments": [experiment_row()]})
    assert "Ens. ROC-AUC" in tex
    assert "99.80 [99.61, 99.92]" in tex


def test_experiments_table_keeps_one_column_spec_per_header_cell():
    tex = mt.experiments_table({"experiments": [experiment_row()]})
    spec = tex.split(r"\begin{tabular}{")[1].replace("@{}", "").split("}")[0]
    header = next(line for line in tex.splitlines() if line.startswith("ID &"))
    assert len(spec) == header.count("&") + 1
