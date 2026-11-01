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


# --------------------------------------------------------------------------- run: parallel driver
class FakeCloud:
    """Stands in for the RunPod API + SSH: scripted stages per pod, records what the driver did."""

    def __init__(self, stages_per_pod, boots=None):
        self.stages = list(stages_per_pod)   # one list of stage strings per created pod, in creation order
        self.boots = list(boots or [])       # per created pod: False = never reachable
        self.created, self.started, self.terminated, self.collected = [], [], [], []

    def install(self, monkeypatch, tmp_path):
        rp.configure("A1,A2,A3")
        monkeypatch.setitem(rp.PROFILE, "state", str(tmp_path / "pods.json"))
        monkeypatch.setattr(rp, "POLL_SECONDS", 0)
        monkeypatch.setattr(rp, "create_pod", self.create_pod)
        monkeypatch.setattr(rp, "wait_ready", self.wait_ready)
        monkeypatch.setattr(rp, "setup", lambda pod: None)
        monkeypatch.setattr(rp, "start", lambda pod, only=None: self.started.append((pod["id"], only)))
        monkeypatch.setattr(rp, "stage", lambda pod: pod["_stages"].pop(0) if len(pod["_stages"]) > 1 else pod["_stages"][0])
        monkeypatch.setattr(rp, "collect", lambda pod: self.collected.append(pod["id"]) or ["A1", "A2", "A3"])
        monkeypatch.setattr(rp, "terminate", lambda pod: self.terminated.append(pod["id"]) or pod.update(ended=1.0))

    def create_pod(self, fold):
        n = len(self.created)
        self.created.append(fold)
        return {"id": f"pod{n}", "name": f"malaria-ablation-fold{fold}", "costPerHr": 0.5}

    def wait_ready(self, pod, timeout=900):
        n = int(pod["id"][3:])
        if self.boots and not self.boots[n]:
            raise TimeoutError("no ssh")
        pod.update(ip="1.2.3.4", port=22, gpu="RTX 4090", vcpu=16, ram=62, _stages=list(self.stages[n]))
        return pod


def run_opts(**kw):
    from types import SimpleNamespace
    return SimpleNamespace(**{"retries": 2, "boot_timeout": 1, "setup_timeout": 5, "train_timeout": 5, "rerun": True,
                              **kw})


def test_drive_fold_replaces_a_pod_that_never_boots(monkeypatch, tmp_path):
    import threading
    cloud = FakeCloud(stages_per_pod=[[], ["ready", "train-A1-fold-3", "done-fold-3"]], boots=[False, True])
    cloud.install(monkeypatch, tmp_path)
    state = {"pods": {}}
    result = rp.drive_fold(3, state, threading.Lock(), run_opts(), threading.Event())
    assert result == "done-fold-3"
    assert cloud.terminated == ["pod0", "pod1"]          # the stuck pod, then the finished one
    assert [p["id"] for p in state["replaced"]] == ["pod0"]
    assert state["pods"]["3"]["collected"] is True
    assert cloud.started == [("pod1", None)]


def test_drive_fold_reruns_a_failed_experiment_once(monkeypatch, tmp_path):
    import threading
    cloud = FakeCloud(stages_per_pod=[["ready", "train-A1-fold-1", "partial-fold-1-failed-A2", "train-A2-fold-1",
                                       "done-fold-1"]])
    cloud.install(monkeypatch, tmp_path)
    state = {"pods": {}}
    result = rp.drive_fold(1, state, threading.Lock(), run_opts(), threading.Event())
    assert result == "done-fold-1"
    assert cloud.started == [("pod0", None), ("pod0", "A2")]
    assert cloud.collected == ["pod0", "pod0"]           # what finished first, then everything
    assert cloud.terminated == ["pod0"]


def test_drive_fold_leaves_a_failed_training_pod_for_inspection(monkeypatch, tmp_path):
    import threading
    cloud = FakeCloud(stages_per_pod=[["ready", "failed-fold-2"]])
    cloud.install(monkeypatch, tmp_path)
    result = rp.drive_fold(2, {"pods": {}}, threading.Lock(), run_opts(), threading.Event())
    assert result == "failed-fold-2"
    assert cloud.terminated == [] and cloud.collected == []


def test_run_refuses_to_start_when_the_balance_is_too_low(monkeypatch, tmp_path):
    rp.configure("A1,A2,A3")
    monkeypatch.setitem(rp.PROFILE, "state", str(tmp_path / "pods.json"))
    monkeypatch.setattr(rp, "balance", lambda: {"clientBalance": 1.0})
    monkeypatch.setattr(rp, "create_pod", lambda fold: pytest.fail("no pod may be created"))
    with pytest.raises(SystemExit, match="balance"):
        rp.cmd_run(run_opts(folds="0-9", max_spend=None, force=False))


def test_community_requests_drop_the_data_centre_list(monkeypatch):
    rp.configure("A1,A2,A3")
    monkeypatch.setattr(rp, "HARDWARE", dict(cloud="COMMUNITY", gpu_types=["NVIDIA GeForce RTX 5090"],
                                             data_centers=[], min_vcpu=16))
    monkeypatch.setattr(rp, "SSH_KEY", __file__)  # any readable file stands in for the public key
    monkeypatch.setattr(rp.os.path, "exists", lambda p: True)
    import builtins
    real_open = builtins.open
    monkeypatch.setattr(builtins, "open", lambda p, *a, **k: real_open(__file__, *a, **k) if p.endswith(".pub") else real_open(p, *a, **k))
    body = rp.pod_request(4)
    assert body["cloudType"] == "COMMUNITY" and "dataCenterIds" not in body
    assert body["gpuTypeIds"] == ["NVIDIA GeForce RTX 5090"] and body["minVCPUPerGPU"] == 16
    assert body["supportPublicIp"] is True and body["name"] == "malaria-ablation-fold4"
