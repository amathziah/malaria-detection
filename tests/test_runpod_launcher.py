"""Tests for src/runpod_10fold.py: the A0 profile is unchanged; the ablation profile runs A1-A3 per pod."""
import os
import stat
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import marques2022_exact as mx  # noqa: E402
import runpod_10fold as rp  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def a0_profile_afterwards():
    yield
    rp.configure("A0")


def test_default_profile_keeps_the_a0_paths():
    p = rp.configure("A0")
    assert p["state"] == os.path.join(REPO, "results", "A0_10fold_paper", "runpod", "pods.json")
    assert p["notebook"] == "Phase2_A0_10fold_PaperExact.ipynb"
    assert p["uploads"] == ["src/marques2022_exact.py", "src/runpod_requirements.txt",
                            "notebooks/Phase2_A0_10fold_PaperExact.ipynb"]
    assert rp.pod_name(3) == "malaria-a0-paper-fold3"
    assert p["watchdog"] == 2 * 3600 and p["max_spend"] == 6.0


def test_ablation_profile_uploads_the_committed_splits():
    p = rp.configure("A1,A2,A3")
    assert p["experiments"] == ["A1", "A2", "A3"]
    assert p["state"] == os.path.join(REPO, "results", "ablation_runpod", "pods.json")
    assert rp.pod_name(0) == "malaria-ablation-fold0"
    for rel in ["results/A1_slide_split/split.csv", "results/A2_yuv_slide/split.csv", "results/ablation_splits.json",
                "notebooks/Phase3_Ablation_A1_A3.ipynb", "src/marques2022_exact.py"]:
        assert rel in p["uploads"]
    for rel in p["uploads"]:
        assert os.path.exists(os.path.join(REPO, rel)), rel


def test_profiles_refuse_unknown_or_mixed_experiments():
    with pytest.raises(SystemExit):
        rp.configure("A1,A9")
    with pytest.raises(SystemExit):
        rp.configure("A0,A1")


def test_experiment_folders_match_the_training_module():
    assert rp.EXPERIMENT_FOLDERS == {k: v["folder"] for k, v in mx.EXPERIMENTS.items()}
    assert rp.PATIENT_SPLIT == {k for k, v in mx.EXPERIMENTS.items() if v["split"] == "patient"}


def fake_bin(tmp_path, papermill_body):
    """A bin/ with fake `papermill` and `python` so the pod's train script can run here."""
    b = tmp_path / "bin"
    b.mkdir()
    for name, body in [("papermill", papermill_body), ("python", 'echo "$PWD"')]:
        f = b / name
        f.write_text("#!/bin/bash\n" + body + "\n")
        f.chmod(f.stat().st_mode | stat.S_IEXEC)
    return str(b)


def run_train_script(tmp_path, papermill_body, *args):
    rp.configure("A1,A2,A3")
    w = tmp_path / "ws"
    (w / "repo" / "notebooks").mkdir(parents=True)
    script = w / "pod_train.sh"
    script.write_text(rp.render_train_script(workspace=str(w)))
    env = dict(os.environ, PATH=fake_bin(tmp_path, papermill_body) + os.pathsep + os.environ["PATH"])
    r = subprocess.run(["bash", str(script), *args], capture_output=True, text=True, env=env)
    read = lambda name: (w / name).read_text().split() if (w / name).exists() else []
    return r, read, w


def test_train_script_runs_every_experiment_and_continues_after_a_failure(tmp_path):
    # papermill fails for A2 only
    r, read, w = run_train_script(tmp_path, 'echo "$@" >> "$(dirname "$0")/calls"; [[ "$*" != *"[A2]"* ]]', "3")
    assert r.returncode == 0, r.stderr
    assert read("DONE") == ["A1", "A3"]
    assert read("FAILED") == ["A2"]
    assert read("STAGE") == ["partial-fold-3-failed-A2"]
    calls = (tmp_path / "bin" / "calls").read_text().splitlines()
    assert len(calls) == 3
    assert "FOLDS_TO_TRAIN: [3]" in calls[0] and "EXPERIMENTS: [A1]" in calls[0]
    assert f"FOLDS_ROOT: {w}/out" in calls[0] and f"RESULTS_ROOT: {w}/repo/results" in calls[0]
    assert "Phase3_Ablation_A1_A3.ipynb" in calls[0] and f"{w}/out/executed/A1_fold_3.ipynb" in calls[0]


def test_train_script_reports_done_when_all_succeed_and_can_rerun_one_experiment(tmp_path):
    r, read, _ = run_train_script(tmp_path, "true", "7", "A2")
    assert r.returncode == 0, r.stderr
    assert read("DONE") == ["A2"] and read("FAILED") == []
    assert read("STAGE") == ["done-fold-7"]


def test_collect_copies_each_finished_experiment_into_its_folder(tmp_path, monkeypatch):
    rp.configure("A1,A2,A3")
    copied = []

    def fake_scp(pod, src, dst, upload):
        copied.append((src, dst))
        if src.endswith("/fold_2"):  # the fold folder arrives with its checkpoint
            os.makedirs(os.path.join(dst, "fold_2"), exist_ok=True)
            open(os.path.join(dst, "fold_2", "fold_2_best.h5"), "w").close()

    monkeypatch.setattr(rp, "scp", fake_scp)
    monkeypatch.setattr(rp, "ssh", lambda pod, cmd, **kw: "A1\nA3\n" if "DONE" in cmd else "")
    done = rp.collect({"fold": 2, "name": "x"}, root=str(tmp_path))
    assert done == ["A1", "A3"]
    assert ("/workspace/out/A1_slide_split/fold_2", str(tmp_path / "results" / "A1_slide_split" / "folds")) in copied
    assert ("/workspace/out/executed/A3_fold_2.ipynb",
            str(tmp_path / "results" / "A3_yuv_image" / "executed" / "fold_2.ipynb")) in copied
    assert not any("A2_yuv_slide" in d for _, d in copied)
    assert os.path.exists(tmp_path / "models" / "A1_slide_split" / "fold_2_best.h5")
    assert not os.path.exists(tmp_path / "results" / "A1_slide_split" / "folds" / "fold_2" / "fold_2_best.h5")
