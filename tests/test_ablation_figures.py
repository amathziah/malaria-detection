"""Smoke tests for src/ablation_figures.py on fake A0-A3 results (they must render and save, not look a certain way)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import ablation_figures as figs  # noqa: E402
import ablation_stats as st  # noqa: E402
import marques2022_exact as mx  # noqa: E402


@pytest.fixture(scope="module")
def analysed(results_root, tmp_path_factory):  # results_root: tests/conftest.py
    return st.analyse(results_root, out_dir=str(tmp_path_factory.mktemp("out")), n_boot=100)


def is_png(path):
    with open(path, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


def test_fold_strip_saves_a_png(analysed, tmp_path):
    assert is_png(figs.fold_strip(analysed["found"], "mcc", path=str(tmp_path / "strip.png")))


def test_contrast_forest_saves_a_png(analysed, tmp_path):
    assert is_png(figs.contrast_forest(analysed["contrasts"], path=str(tmp_path / "forest.png")))
    assert is_png(figs.contrast_forest(analysed["contrasts"], level="fold", path=str(tmp_path / "forest_f.png")))


def test_per_patient_needs_the_same_hold_out_set(analysed, tmp_path):
    assert is_png(figs.per_patient(analysed["found"], "A1", "A2", path=str(tmp_path / "pp.png")))
    with pytest.raises(ValueError):
        figs.per_patient(analysed["found"], "A0", "A1")


def test_experiment_panels_save_a_png(analysed, tmp_path):
    agg = analysed["found"]["A2"]["agg"]
    assert is_png(figs.experiment_panels(agg, "A2", path=str(tmp_path / "a2.png")))


def test_split_colours_are_the_validated_pair():
    assert figs.SPLIT_COLOR == {"image": "#d9622b", "patient": "#00809a"}
    assert set(figs.PREP_MARKER) == set(mx.PREPROCESSING)
