#!/usr/bin/env python3
"""Run the paper-exact 10-fold experiments on RunPod: one pod per fold, results copied back here.

Two profiles, chosen with --experiments before the command:
    A0 (default)    the paper-exact replication (results/A0_10fold_paper/runpod/pods.json)
    A1,A2,A3        the ablation: each pod trains fold k of every listed experiment, one after another
                    (results/ablation_runpod/pods.json); e.g.
                    python src/runpod_10fold.py --experiments A1,A2,A3 up --folds 0-9 --setup-only
                    python src/runpod_10fold.py --experiments A1,A2,A3 go --folds 0-9
                    python src/runpod_10fold.py --experiments A1,A2,A3 watch
                    python src/runpod_10fold.py --experiments A1,A2,A3 start --folds 4 --only A2   # re-run one

Usage:
    python src/runpod_10fold.py up --folds 0          # create pods, install, start training (fold list: 0-9, 1,4,7)
    python src/runpod_10fold.py up --folds 0 --setup-only
    python src/runpod_10fold.py setup --folds 0       # (re)install the environment on an existing pod
    python src/runpod_10fold.py start --folds 0       # start training on a pod that is set up
    python src/runpod_10fold.py go --folds 1-9        # set up + start each pod the moment it is ready
    python src/runpod_10fold.py status                # stage of every pod + money spent
    python src/runpod_10fold.py watch                 # collect folds as they finish until all are home
    python src/runpod_10fold.py collect               # copy finished folds home and terminate their pods
    python src/runpod_10fold.py down                  # terminate every pod this script created
    python src/runpod_10fold.py down --folds 6        # terminate one pod (e.g. stuck while booting)

Needs the RunPod API key in $RUNPOD_API_KEY or ~/.runpod_key, and ~/.ssh/id_ed25519 registered in
RunPod (Settings > SSH public keys). Pod ids and timings are kept in results/A0_10fold_paper/runpod/pods.json.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519")
# Same names as marques2022_exact.EXPERIMENTS (a test checks it); kept here so the launcher needs no ML packages
EXPERIMENT_FOLDERS = {"A0": "A0_10fold_paper", "A1": "A1_slide_split", "A2": "A2_yuv_slide", "A3": "A3_yuv_image"}
PATIENT_SPLIT = {"A1", "A2"}  # these train on the committed results/<folder>/split.csv
ABLATION_NOTEBOOK = "Phase3_Ablation_A1_A3.ipynb"
PROFILE = {}  # filled by configure(): which experiments, notebook, uploads, state file, limits


def configure(experiments="A0"):
    """Select the A0 profile (the replication, unchanged) or the ablation profile (any of A1-A3)."""
    exps = [e.strip() for e in experiments.split(",") if e.strip()] if isinstance(experiments, str) else list(experiments)
    unknown = [e for e in exps if e not in EXPERIMENT_FOLDERS]
    if not exps or unknown:
        raise SystemExit(f"unknown experiment(s) {unknown or exps}: choose from {sorted(EXPERIMENT_FOLDERS)}")
    PROFILE.clear()
    if exps == ["A0"]:
        runpod_dir = os.path.join(REPO, "results", "A0_10fold_paper", "runpod")
        notebook = "Phase2_A0_10fold_PaperExact.ipynb"
        PROFILE.update(experiments=exps, name="a0-paper", notebook=notebook, runpod_dir=runpod_dir,
                       state=os.path.join(runpod_dir, "pods.json"), watchdog=2 * 3600, max_spend=6.0, hours=0.65,
                       uploads=["src/marques2022_exact.py", "src/runpod_requirements.txt", f"notebooks/{notebook}"])
    elif "A0" in exps:
        raise SystemExit("A0 is the replication profile: run it on its own (A0 is already trained)")
    else:
        runpod_dir = os.path.join(REPO, "results", "ablation_runpod")
        splits = [f"results/{EXPERIMENT_FOLDERS[e]}/split.csv" for e in exps if e in PATIENT_SPLIT]
        PROFILE.update(experiments=exps, name="ablation", notebook=ABLATION_NOTEBOOK, runpod_dir=runpod_dir,
                       state=os.path.join(runpod_dir, "pods.json"), watchdog=3 * 3600, max_spend=12.0,
                       hours=0.4 + 0.22 * len(exps),  # ~20 min setup + ~13 min per experiment and fold
                       uploads=["src/marques2022_exact.py", "src/ablation_stats.py", "src/ablation_figures.py",
                                "src/runpod_requirements.txt", f"notebooks/{ABLATION_NOTEBOOK}",
                                "results/ablation_splits.json"] + splits)
    return PROFILE


def pod_name(fold):
    return f"malaria-{PROFILE['name']}-fold{fold}"


configure("A0")

IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
GPU_TYPES = ["NVIDIA GeForce RTX 4090", "NVIDIA L40S", "NVIDIA RTX 6000 Ada Generation"]  # in order of preference
MIN_VCPU = 16   # the paper's augmentation runs on the CPU; fewer cores would starve the GPU
# EU-RO-1 had RTX 4090s in stock; an EUR-IS host could not download from PyPI (path-MTU blackhole to Fastly)
DATA_CENTERS = ["EU-RO-1", "EU-NL-1", "US-TX-4", "US-WA-1", "CA-MTL-1", "US-KS-2", "US-GA-2"]
MIN_RAM_GB = 40
PRICE_ESTIMATE = 0.8  # $/h per pod, for the balance check (RTX 4090 Secure Cloud was $0.74/h)
# A pod removes itself after PROFILE["watchdog"] seconds, whatever happens here

# Exact, pinned environment (TF 2.15 = last Keras 2; numpy<1.24 for imgaug 0.4.0), installed with uv:
# unpinned, pip backtracks for many minutes on sub-dependencies that now require a newer numpy.
REQUIREMENTS = "src/runpod_requirements.txt"
NO_DEPS = "albumentations|imgaug"  # their opencv-python dependency needs libGL; opencv-python-headless provides cv2

POD_SETUP = r"""#!/bin/bash
set -uo pipefail
W=/workspace; cd $W
stage() { echo "$1" > $W/STAGE; echo "[$(date +%T)] $1"; }
( sleep WATCHDOG; runpodctl remove pod $RUNPOD_POD_ID ) >/dev/null 2>&1 &
stage network-check
TF_WHEEL=$(curl -s -m 15 https://pypi.org/pypi/tensorflow/2.15.1/json | python -c "import json, sys; print([u['url'] for u in json.load(sys.stdin)['urls'] if 'cp311-cp311-manylinux' in u['filename'] and 'x86_64' in u['filename']][0])")
SPEED=$(curl -s -m 10 -r 0-50000000 -o /dev/null -w "%{speed_download}" "$TF_WHEEL" | cut -d. -f1)
echo "PyPI download speed: $((SPEED / 1000000)) MB/s"
[ "${SPEED:-0}" -gt 2000000 ] || { stage failed-network; exit 1; }
stage pip
export PIP_ROOT_USER_ACTION=ignore PIP_DISABLE_PIP_VERSION_CHECK=1
pip install -q uv || { stage failed-pip; exit 1; }
grep -vE "^(NO_DEPS)==" $W/repo/REQUIREMENTS > $W/req_main.txt
grep -E "^(NO_DEPS)==" $W/repo/REQUIREMENTS > $W/req_nodeps.txt
PY=$(which python)
uv pip install --python $PY --break-system-packages -r $W/req_main.txt "tensorflow[and-cuda]==2.15.1" || { stage failed-pip; exit 1; }
uv pip install --python $PY --break-system-packages --no-deps -r $W/req_nodeps.txt || { stage failed-pip; exit 1; }
python -m ipykernel install --user --name paper311 >/dev/null || { stage failed-kernel; exit 1; }
stage data
python -c "import sys; sys.path.insert(0, '$W/repo/src'); import marques2022_exact as mx; print(mx.find_or_download('$W/data'))" \
  || { stage failed-data; exit 1; }
stage gpu-check
python -c "import tensorflow as tf; g = tf.config.list_physical_devices('GPU'); print(tf.__version__, g); assert g" \
  || { stage failed-gpu; exit 1; }
stage ready
"""

POD_TRAIN = r"""#!/bin/bash
set -uo pipefail
FOLD=$1; W=/workspace
stage() { echo "$1" > $W/STAGE; echo "[$(date +%T)] $1"; }
NV=$(python -c "import site, os; print(os.path.join(site.getsitepackages()[0], 'nvidia', 'cuda_nvcc'))")
export XLA_FLAGS="--xla_gpu_cuda_data_dir=$NV" PATH="$NV/bin:$PATH" TF_GPU_THREAD_MODE=gpu_private TF_CPP_MIN_LOG_LEVEL=1
mkdir -p $W/out/executed
cd $W/repo/notebooks
stage train-fold-$FOLD
papermill NOTEBOOK $W/out/executed/fold_$FOLD.ipynb -k paper311 --log-output \
  -y "{FOLDS_TO_TRAIN: [$FOLD], AGGREGATE: false, DATA_DIR: $W/data, OUT_DIR: $W/out, CACHE_PATH: $W/cache.npy, N_WORKERS: null}" \
  && stage done-fold-$FOLD || stage failed-fold-$FOLD
"""

# Ablation: fold k of each experiment in turn. A failed experiment doesn't stop the next one; the pod then ends
# in stage partial-fold-k-failed-<exps> (collect copies what finished; `start --only` re-runs the rest).
POD_TRAIN_ABLATION = r"""#!/bin/bash
set -uo pipefail
FOLD=$1; EXPS=${2:-__EXPERIMENTS__}; W=__WORKSPACE__
stage() { echo "$1" > $W/STAGE; echo "[$(date +%T)] $1"; }
NV=$(python -c "import site, os; print(os.path.join(site.getsitepackages()[0], 'nvidia', 'cuda_nvcc'))")
export XLA_FLAGS="--xla_gpu_cuda_data_dir=$NV" PATH="$NV/bin:$PATH" TF_GPU_THREAD_MODE=gpu_private TF_CPP_MIN_LOG_LEVEL=1
mkdir -p $W/out/executed
cd $W/repo/notebooks
: > $W/FAILED
for EXP in ${EXPS//,/ }; do
  stage train-$EXP-fold-$FOLD
  if papermill __NOTEBOOK__ $W/out/executed/${EXP}_fold_$FOLD.ipynb -k paper311 --log-output \
      -y "{EXPERIMENTS: [$EXP], FOLDS_TO_TRAIN: [$FOLD], AGGREGATE: false, DATA_DIR: $W/data, CACHE_DIR: $W, RESULTS_ROOT: $W/repo/results, FOLDS_ROOT: $W/out, N_WORKERS: null}"; then
    echo $EXP >> $W/DONE
  else
    echo $EXP >> $W/FAILED
  fi
done
if [ -s $W/FAILED ]; then stage partial-fold-$FOLD-failed-$(paste -sd, $W/FAILED); else stage done-fold-$FOLD; fi
"""


def render_train_script(workspace="/workspace"):
    """The pod's pod_train.sh for the current profile."""
    if PROFILE["experiments"] == ["A0"]:
        return POD_TRAIN.replace("NOTEBOOK", PROFILE["notebook"])
    return (POD_TRAIN_ABLATION.replace("__EXPERIMENTS__", " ".join(PROFILE["experiments"]))
            .replace("__NOTEBOOK__", PROFILE["notebook"]).replace("__WORKSPACE__", workspace))


# ----------------------------------------------------------------------------- RunPod API
def api_key():
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        with open(os.path.expanduser("~/.runpod_key")) as fh:
            key = fh.read().strip()
    return key


def _headers():
    # RunPod's edge rejects urllib's default User-Agent with 403
    return {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json",
            "User-Agent": "malaria-detection-runpod-10fold/1.0"}


def rest(method, path, body=None):
    req = urllib.request.Request(f"https://rest.runpod.io/v1{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"RunPod {method} {path}: HTTP {e.code} {e.read().decode()[:400]}") from None
    return json.loads(raw) if raw else {}


def balance():
    q = json.dumps({"query": "query { myself { clientBalance currentSpendPerHr } }"}).encode()
    req = urllib.request.Request("https://api.runpod.io/graphql", data=q, method="POST",
                                 headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["data"]["myself"]


# ----------------------------------------------------------------------------- local state
def load_state():
    if os.path.exists(PROFILE["state"]):
        with open(PROFILE["state"]) as fh:
            return json.load(fh)
    return {"pods": {}}


def save_state(state):
    """Write the state, keeping "ended"/"collected" flags another launcher process may have written meanwhile."""
    path = PROFILE["state"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    on_disk = load_state()
    for k, disk_pod in on_disk["pods"].items():
        pod = state["pods"].get(k)
        if pod is not None and pod.get("id") == disk_pod.get("id"):
            for flag in ("ended", "collected"):
                if disk_pod.get(flag) and not pod.get(flag):
                    pod[flag] = disk_pod[flag]
    known = {p["id"] for p in state.get("replaced", [])}
    state.setdefault("replaced", []).extend(p for p in on_disk.get("replaced", []) if p["id"] not in known)
    with open(path + ".tmp", "w") as fh:
        json.dump(state, fh, indent=1)
    os.replace(path + ".tmp", path)


def spent(state):
    now = time.time()
    pods = list(state["pods"].values()) + state.get("replaced", [])
    return sum(p.get("costPerHr", 0) * ((p.get("ended") or now) - p["created"]) / 3600 for p in pods)


def parse_folds(text):
    folds = []
    for part in text.split(","):
        a, _, b = part.partition("-")
        folds += list(range(int(a), int(b) + 1)) if b else [int(a)]
    return folds


# ----------------------------------------------------------------------------- ssh
def ssh_base(pod):
    return ["-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30"]


def ssh(pod, command, check=True, timeout=600):
    cmd = ["ssh", *ssh_base(pod), "-p", str(pod["port"]), f"root@{pod['ip']}", command]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"ssh {pod['name']}: {command[:80]}... -> {r.returncode}\n{r.stderr[-800:]}")
    return r.stdout


def scp(pod, src, dst, upload):
    remote = lambda p: f"root@{pod['ip']}:{p}"
    args = [src, remote(dst)] if upload else [remote(src), dst]
    subprocess.run(["scp", "-r", "-q", *ssh_base(pod), "-P", str(pod["port"]), *args], check=True, timeout=1800)


# ----------------------------------------------------------------------------- pod lifecycle
HARDWARE = dict(cloud="SECURE", gpu_types=GPU_TYPES, data_centers=DATA_CENTERS, min_vcpu=MIN_VCPU)


def pod_request(fold):
    """The REST body for one pod (HARDWARE holds the cloud, GPU types, data centres and vCPU floor)."""
    body = {"name": pod_name(fold), "imageName": IMAGE, "gpuTypeIds": HARDWARE["gpu_types"],
            "gpuTypePriority": "custom", "gpuCount": 1, "cloudType": HARDWARE["cloud"],
            "minVCPUPerGPU": HARDWARE["min_vcpu"], "minRAMPerGPU": MIN_RAM_GB, "containerDiskInGb": 60,
            "volumeInGb": 0, "ports": ["22/tcp"], "supportPublicIp": True,
            "env": {"PUBLIC_KEY": open(SSH_KEY + ".pub").read().strip()}}
    if HARDWARE["data_centers"]:
        body.update(dataCenterIds=HARDWARE["data_centers"], dataCenterPriority="custom")
    return body


def create_pod(fold):
    return rest("POST", "/pods", pod_request(fold))


def wait_ready(pod, timeout=900):
    """Wait for a public IP + SSH port, then for sshd to answer."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        info = rest("GET", f"/pods/{pod['id']}")
        port = (info.get("portMappings") or {}).get("22")
        if info.get("publicIp") and port:
            pod.update(ip=info["publicIp"], port=port, costPerHr=float(info.get("costPerHr") or pod.get("costPerHr") or 0),
                       gpu=(info.get("machine") or {}).get("gpuTypeId") or (info.get("gpu") or {}).get("displayName"),
                       vcpu=info.get("vcpuCount"), ram=info.get("memoryInGb"))
            try:
                ssh(pod, "true", timeout=30)
                return pod
            except Exception:
                pass
        time.sleep(10)
    raise TimeoutError(f"{pod['name']} not reachable after {timeout}s")


def _upload_repo(pod):
    """Copy the profile's files to /workspace/repo/<same relative path> (latest notebook, module, splits)."""
    dirs = sorted({os.path.dirname(f"/workspace/repo/{rel}") for rel in PROFILE["uploads"]})
    ssh(pod, "mkdir -p /workspace/out " + " ".join(dirs))
    for rel in PROFILE["uploads"]:
        scp(pod, os.path.join(REPO, rel), f"/workspace/repo/{rel}", upload=True)


def setup(pod):
    _upload_repo(pod)
    script = (POD_SETUP.replace("WATCHDOG", str(PROFILE["watchdog"])).replace("REQUIREMENTS", REQUIREMENTS)
              .replace("NO_DEPS", NO_DEPS))
    _push_script(pod, "pod_setup.sh", script)
    _push_script(pod, "pod_train.sh", render_train_script())
    ssh(pod, "cd /workspace; setsid nohup bash pod_setup.sh > setup.log 2>&1 < /dev/null &")


def _push_script(pod, name, text):
    local = os.path.join(PROFILE["runpod_dir"], name)
    os.makedirs(os.path.dirname(local), exist_ok=True)
    with open(local, "w") as fh:
        fh.write(text)
    scp(pod, local, f"/workspace/{name}", upload=True)


def start(pod, only=None):
    """Start training on a set-up pod; `only` ("A2" or "A1,A3") re-runs some experiments of the ablation."""
    _upload_repo(pod)  # latest notebook/module
    extra = f" {only}" if only else ""
    # "cd ...; job &", not "cd ... && job &": the latter backgrounds a subshell that keeps this SSH session open
    ssh(pod, f"cd /workspace; setsid nohup bash pod_train.sh {pod['fold']}{extra} > train.log 2>&1 < /dev/null &")
    pod["started"] = time.time()


def stage(pod):
    return ssh(pod, "cat /workspace/STAGE 2>/dev/null || echo booting", check=False, timeout=30).strip() or "?"


def collect(pod, root=REPO):
    """Copy a pod's finished folds home (models to models/, which git ignores). Returns the experiments copied."""
    k = pod["fold"]
    if PROFILE["experiments"] == ["A0"]:
        done, remote_fold = ["A0"], lambda folder: f"/workspace/out/fold_{k}"
        remote_nb = lambda exp: f"/workspace/out/executed/fold_{k}.ipynb"
    else:
        listed = ssh(pod, "cat /workspace/DONE 2>/dev/null", check=False).split()
        done = [e for i, e in enumerate(listed) if e in EXPERIMENT_FOLDERS and e not in listed[:i]]
        remote_fold = lambda folder: f"/workspace/out/{folder}/fold_{k}"
        remote_nb = lambda exp: f"/workspace/out/executed/{exp}_fold_{k}.ipynb"
    for exp in done:
        folder = EXPERIMENT_FOLDERS[exp]
        dest = os.path.join(root, "results", folder, "folds")
        executed = os.path.join(root, "results", folder, "executed")
        models = os.path.join(root, "models", folder)
        for d in (dest, executed, models):
            os.makedirs(d, exist_ok=True)
        scp(pod, remote_fold(folder), dest, upload=False)
        scp(pod, remote_nb(exp), os.path.join(executed, f"fold_{k}.ipynb"), upload=False)
        h5 = os.path.join(dest, f"fold_{k}", f"fold_{k}_best.h5")
        if os.path.exists(h5):
            os.replace(h5, os.path.join(models, f"fold_{k}_best.h5"))  # models stay out of git
    runpod_dir = PROFILE["runpod_dir"] if root == REPO else os.path.join(root, "runpod")
    os.makedirs(runpod_dir, exist_ok=True)
    for log in ["setup.log", "train.log"]:
        scp(pod, f"/workspace/{log}", os.path.join(runpod_dir, f"fold_{k}_{log}"), upload=False)
    if PROFILE["experiments"] != ["A0"]:  # executed notebooks of every experiment, failed ones included (tracebacks)
        try:
            scp(pod, "/workspace/out/executed", os.path.join(runpod_dir, f"fold_{k}_executed"), upload=False)
        except Exception:
            pass
    return done


def terminate(pod):
    try:
        rest("DELETE", f"/pods/{pod['id']}")
    except RuntimeError as e:
        if "404" not in str(e):
            raise
    pod["ended"] = time.time()


# ----------------------------------------------------------------------------- commands
def cmd_up(args):
    state = load_state()
    folds = parse_folds(args.folds)
    have, estimate = balance()["clientBalance"], len(folds) * PRICE_ESTIMATE * PROFILE["hours"]
    print(f"Balance before: ${have:.2f} · estimated cost of {len(folds)} pod(s): ${estimate:.2f}")
    if have < estimate + 1 and not args.force:
        raise SystemExit("balance too low for this run (add credit, or pass --force)")
    new = []
    for k in folds:
        if str(k) in state["pods"] and not state["pods"][str(k)].get("ended"):
            print(f"fold {k}: pod already running, skipped")
            continue
        if str(k) in state["pods"]:  # keep terminated pods for the spend total
            state.setdefault("replaced", []).append(state["pods"].pop(str(k)))
        info = create_pod(k)
        pod = {"fold": k, "id": info["id"], "name": info.get("name"), "created": time.time(),
               "costPerHr": float(info.get("costPerHr") or 0)}
        state["pods"][str(k)] = pod
        save_state(state)
        new.append(pod)
        print(f"fold {k}: pod {pod['id']} created (${pod['costPerHr']}/h)")
    for pod in new:
        wait_ready(pod)
        save_state(state)
        setup(pod)
        print(f"fold {pod['fold']}: {pod['gpu']} · {pod['vcpu']} vCPU · {pod['ram']} GB · setup started")
    if args.setup_only:
        return
    for pod in new:
        while stage(pod) not in ("ready",) and not stage(pod).startswith("failed"):
            time.sleep(15)
        if stage(pod) == "ready":
            start(pod)
            print(f"fold {pod['fold']}: training started")
    save_state(state)


def cmd_setup(args):
    state = load_state()
    for k in parse_folds(args.folds):
        setup(state["pods"][str(k)])
        print(f"fold {k}: setup (re)started")


def cmd_start(args):
    state = load_state()
    for k in parse_folds(args.folds):
        pod = state["pods"][str(k)]
        start(pod, only=args.only)
        print(f"fold {k}: training started" + (f" ({args.only} only)" if args.only else ""))
    save_state(state)


def cmd_go(args):
    """Set up and start every pod in `--folds` as soon as it is ready, in parallel."""
    state = load_state()
    todo = {k for k in parse_folds(args.folds) if not state["pods"][str(k)].get("ended")}
    while todo:
        for k in sorted(todo):
            pod = state["pods"][str(k)]
            if "port" not in pod or not pod.get("setup"):
                info = rest("GET", f"/pods/{pod['id']}")
                port = (info.get("portMappings") or {}).get("22")
                if not (info.get("publicIp") and port):
                    continue
                pod.update(ip=info["publicIp"], port=port, vcpu=info.get("vcpuCount"), ram=info.get("memoryInGb"),
                           costPerHr=float(info.get("costPerHr") or pod.get("costPerHr") or 0))
                if ssh(pod, "test -f /workspace/STAGE && echo yes || echo no", check=False, timeout=30).strip() == "no":
                    try:
                        setup(pod)
                    except Exception as e:  # sshd not up yet
                        print(f"fold {k}: not reachable yet ({str(e)[:60]})")
                        continue
                pod["setup"] = True
                save_state(state)
                print(f"fold {k}: setup running")
            st = stage(pod)
            if st == "ready":
                start(pod)
                todo.discard(k)
                print(f"fold {k}: training started")
            elif st.startswith(("train", "done", "partial")):
                todo.discard(k)
            elif st.startswith("failed"):
                print(f"fold {k}: {st}")
                todo.discard(k)
            save_state(state)
        time.sleep(10)


def cmd_status(args, state=None):
    state = state or load_state()
    for k, pod in sorted(state["pods"].items(), key=lambda kv: int(kv[0])):
        if pod.get("ended"):
            print(f"fold {k}: {'collected' if pod.get('collected') else 'terminated'}")
            continue
        if "port" not in pod:
            print(f"fold {k}: booting")
            continue
        last = ssh(pod, "tail -n 1 /workspace/train.log 2>/dev/null || tail -n 1 /workspace/setup.log",
                   check=False, timeout=30).strip()[-110:]
        print(f"fold {k}: {stage(pod):18s} {pod.get('gpu')} | {last}")
    print(f"Spent so far (estimate): ${spent(state):.2f}")


def cmd_collect(args, state=None):
    state = state or load_state()
    for k, pod in state["pods"].items():
        if pod.get("ended") or "port" not in pod:
            continue
        s = stage(pod)
        if s.startswith("done-fold"):
            collect(pod)
            terminate(pod)
            pod["collected"] = True
            print(f"fold {k}: collected, pod terminated")
        elif s.startswith("partial") and pod.get("partial") != s:
            done = collect(pod)  # keep what finished; the pod stays up so the rest can be re-run with start --only
            pod["partial"] = s
            print(f"fold {k}: {s}; collected {done}; pod left running (start --folds {k} --only <exp>, or down)")
        elif s.startswith("failed"):
            print(f"fold {k}: FAILED at {s}; pod left running for inspection (see /workspace/*.log)")
        save_state(state)


def cmd_watch(args):
    cap = args.max_spend if args.max_spend is not None else PROFILE["max_spend"]
    while True:
        state = load_state()
        cmd_collect(args, state)
        if spent(state) > cap:
            print(f"Spend cap ${cap} reached: terminating everything")
            cmd_down(args)
            return
        live = [p for p in state["pods"].values() if not p.get("ended")]
        if not live:
            print("All folds collected.")
            return
        waiting = [p for p in live if "port" not in p or not stage(p).startswith(("failed", "partial"))]
        if not waiting:  # nothing is still running: don't keep paying for pods that need a person
            print(f"Nothing left running; {len(live)} pod(s) need attention (status / start --only / down).")
            return
        cmd_status(args, state)
        time.sleep(args.every)


def cmd_down(args):
    state = load_state()
    only = set(parse_folds(args.folds)) if getattr(args, "folds", None) else None
    for k, pod in state["pods"].items():
        if only is not None and int(k) not in only:
            continue
        if not pod.get("ended"):
            terminate(pod)
            print(f"fold {k}: pod {pod['id']} terminated")
    save_state(state)


# ----------------------------------------------------------------------------- run: everything, in parallel
POLL_SECONDS = 15     # between stage checks of one pod
STATUS_SECONDS = 60   # between status lines


def _log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _wait_stage(pod, wanted, timeout, stop):
    """Poll the pod's stage until it starts with one of `wanted` (or 'failed'); 'timeout'/'stopped' otherwise."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if stop.is_set():
            return "stopped"
        try:
            pod["stage"] = stage(pod)
        except Exception as e:  # a dropped SSH connection is not a failed pod
            pod["stage"] = f"unreachable ({str(e)[:40]})"
        if pod["stage"].startswith(tuple(wanted) + ("failed",)):
            return pod["stage"]
        time.sleep(POLL_SECONDS)
    return "timeout"


def _collect_with_retries(pod, tries=3):
    for i in range(tries):
        try:
            return collect(pod)
        except Exception as e:
            _log(f"fold {pod['fold']}: collect failed ({str(e)[:80]}), retry {i + 1}/{tries}")
            time.sleep(10 * (i + 1))
    raise RuntimeError("could not copy the results home")


def drive_fold(k, state, lock, opts, stop):
    """Fold k from pod creation to collected results. A pod that doesn't boot or set up in time is replaced;
    an experiment that fails is re-run once on the same pod. Returns the final stage."""
    def save():
        with lock:
            save_state(state)

    for attempt in range(1 + opts.retries):
        if stop.is_set():
            return "stopped"
        try:
            info = create_pod(k)
        except Exception as e:  # e.g. no stock right now
            _log(f"fold {k}: could not create a pod ({str(e)[:120]}); retrying in 30 s")
            time.sleep(30 if POLL_SECONDS else 0)
            continue
        pod = {"fold": k, "id": info["id"], "name": info.get("name"), "created": time.time(),
               "costPerHr": float(info.get("costPerHr") or 0), "attempt": attempt + 1}
        with lock:
            if str(k) in state["pods"]:
                state.setdefault("replaced", []).append(state["pods"].pop(str(k)))
            state["pods"][str(k)] = pod
        save()
        _log(f"fold {k}: pod {pod['id']} created (${pod['costPerHr']}/h, attempt {attempt + 1})")
        try:
            wait_ready(pod, timeout=opts.boot_timeout)
            save()
            setup(pod)
            pod["setup"] = True
            save()
            _log(f"fold {k}: {pod.get('gpu')} · {pod.get('vcpu')} vCPU · {pod.get('ram')} GB · setting up")
            st = _wait_stage(pod, ("ready",), opts.setup_timeout, stop)
            if st != "ready":
                raise RuntimeError(f"setup ended in stage {st}")
            start(pod)
            save()
            _log(f"fold {k}: training started")
        except Exception as e:
            _log(f"fold {k}: {str(e)[:120]}; terminating and replacing this pod")
            terminate(pod)
            save()
            continue

        st = _wait_stage(pod, ("done", "partial"), opts.train_timeout, stop)
        if st.startswith("partial") and opts.rerun:
            failed = st.split("-failed-")[-1]
            _log(f"fold {k}: {failed} failed; collecting the rest and re-running {failed} once")
            _collect_with_retries(pod)
            start(pod, only=failed)
            st = _wait_stage(pod, ("done", "partial"), opts.train_timeout, stop)
        if st.startswith(("done", "partial")):
            try:
                done = _collect_with_retries(pod)
            except RuntimeError:
                _log(f"fold {k}: results could not be copied; pod left running for inspection")
                return "collect-failed"
            pod["collected"] = True
            terminate(pod)
            save()
            _log(f"fold {k}: {st}; collected {done}; pod terminated")
            return st
        _log(f"fold {k}: training ended in {st}; pod left running for inspection (see /workspace/*.log)")
        save()
        return st
    _log(f"fold {k}: gave up after {1 + opts.retries} pods")
    return "gave-up"


def cmd_run(args):
    """Create one pod per fold and drive them all in parallel until the results are home."""
    state = load_state()
    folds = parse_folds(args.folds)
    have, estimate = balance()["clientBalance"], len(folds) * PRICE_ESTIMATE * PROFILE["hours"]
    cap = args.max_spend if args.max_spend is not None else PROFILE["max_spend"]
    _log(f"{PROFILE['experiments']} · folds {folds} · {HARDWARE['cloud']} {HARDWARE['gpu_types']} · "
         f">= {HARDWARE['min_vcpu']} vCPU · balance ${have:.2f}, estimate ${estimate:.2f}, cap ${cap:.2f}")
    if have < estimate + 1 and not args.force:
        raise SystemExit("balance too low for this run (add credit, or pass --force)")
    stop, lock = threading.Event(), threading.Lock()
    with ThreadPoolExecutor(max_workers=len(folds)) as ex:
        futures = {k: ex.submit(drive_fold, k, state, lock, args, stop) for k in folds}
        while not all(f.done() for f in futures.values()):
            time.sleep(STATUS_SECONDS)
            with lock:
                cost = spent(state)
                live = {k: p for k, p in state["pods"].items() if not p.get("ended")}
            if cost > cap and not stop.is_set():
                _log(f"spend cap ${cap:.2f} reached (${cost:.2f}): stopping and terminating every pod")
                stop.set()
                for pod in live.values():
                    terminate(pod)
                with lock:
                    save_state(state)
            _log(f"spent ≈ ${cost:.2f} · " + " · ".join(
                f"{k}:{'✓' if futures[k].done() else (live.get(str(k)) or {}).get('stage', 'starting')[:22]}"
                for k in folds))
    results = {k: f.result() for k, f in futures.items()}
    with lock:
        left = [p for p in state["pods"].values() if not p.get("ended")]
    _log(f"finished · spent ≈ ${spent(state):.2f} · " + ", ".join(f"fold {k}: {r}" for k, r in results.items()))
    if left:
        _log("still running (inspect, then `down`): " + ", ".join(f"fold {p['fold']} ({p['id']})" for p in left))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--experiments", default="A0", help="A0 (default) or a list of A1,A2,A3")
    ap.add_argument("--cloud", choices=["SECURE", "COMMUNITY"], default="SECURE")
    ap.add_argument("--gpus", help="GPU type ids in order of preference, comma-separated (default: 4090, L40S, 6000 Ada)")
    ap.add_argument("--min-vcpu", type=int, default=MIN_VCPU, help="vCPUs per GPU (augmentation runs on the CPU)")
    ap.add_argument("--any-datacenter", action="store_true", help="don't restrict the data centres")
    ap.add_argument("--state", help="a separate pods.json, e.g. for a second batch of folds while another run is live")
    sub = ap.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("up")
    up.add_argument("--folds", default="0-9")
    up.add_argument("--setup-only", action="store_true")
    up.add_argument("--force", action="store_true", help="start even if the balance looks too low")
    se = sub.add_parser("setup")
    se.add_argument("--folds", required=True)
    st = sub.add_parser("start")
    st.add_argument("--folds", required=True)
    st.add_argument("--only", help="ablation: re-run only these experiments on the pod, e.g. A2 or A1,A3")
    go = sub.add_parser("go")
    go.add_argument("--folds", default="0-9")
    sub.add_parser("status")
    sub.add_parser("collect")
    w = sub.add_parser("watch")
    w.add_argument("--every", type=int, default=60)
    w.add_argument("--max-spend", type=float, default=None, help="default: $6 for A0, $12 for the ablation")
    rn = sub.add_parser("run", help="create the pods and drive them all to collected results, in parallel")
    rn.add_argument("--folds", default="0-9")
    rn.add_argument("--retries", type=int, default=2, help="replacement pods per fold if one fails to boot/set up")
    rn.add_argument("--boot-timeout", type=int, default=600, help="seconds to wait for SSH before replacing a pod")
    rn.add_argument("--setup-timeout", type=int, default=900)
    rn.add_argument("--train-timeout", type=int, default=3 * 3600)
    rn.add_argument("--no-rerun", dest="rerun", action="store_false", help="don't re-run a failed experiment")
    rn.add_argument("--max-spend", type=float, default=None)
    rn.add_argument("--force", action="store_true")
    dn = sub.add_parser("down")
    dn.add_argument("--folds", help="only these folds (default: all)")
    args = ap.parse_args()
    configure(args.experiments)
    if args.state:
        PROFILE["state"] = os.path.abspath(args.state)
    HARDWARE.update(cloud=args.cloud, min_vcpu=args.min_vcpu,
                    data_centers=[] if (args.any_datacenter or args.cloud == "COMMUNITY") else DATA_CENTERS)
    if args.gpus:
        HARDWARE["gpu_types"] = [g.strip() for g in args.gpus.split(",") if g.strip()]
    {"up": cmd_up, "setup": cmd_setup, "start": cmd_start, "go": cmd_go, "status": cmd_status, "collect": cmd_collect,
     "watch": cmd_watch, "down": cmd_down, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
