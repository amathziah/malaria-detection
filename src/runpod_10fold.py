#!/usr/bin/env python3
"""Run the paper-exact 10-fold replication on RunPod: one pod per fold, results copied back here.

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
import time
import urllib.error
import urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(REPO, "results", "A0_10fold_paper")
MODELS = os.path.join(REPO, "models", "A0_10fold_paper")
STATE = os.path.join(RESULTS, "runpod", "pods.json")
NOTEBOOK = "Phase2_A0_10fold_PaperExact.ipynb"
UPLOADS = ["src/marques2022_exact.py", "src/runpod_requirements.txt", f"notebooks/{NOTEBOOK}"]
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519")

IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
GPU_TYPES = ["NVIDIA GeForce RTX 4090", "NVIDIA L40S", "NVIDIA RTX 6000 Ada Generation"]  # in order of preference
MIN_VCPU = 16   # the paper's augmentation runs on the CPU; fewer cores would starve the GPU
# EU-RO-1 had RTX 4090s in stock; an EUR-IS host could not download from PyPI (path-MTU blackhole to Fastly)
DATA_CENTERS = ["EU-RO-1", "EU-NL-1", "US-TX-4", "US-WA-1", "CA-MTL-1", "US-KS-2", "US-GA-2"]
MIN_RAM_GB = 40
WATCHDOG_SECONDS = 2 * 3600  # a pod removes itself after this, whatever happens here

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
    if os.path.exists(STATE):
        with open(STATE) as fh:
            return json.load(fh)
    return {"pods": {}}


def save_state(state):
    """Write the state, keeping "ended"/"collected" flags another launcher process may have written meanwhile."""
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    on_disk = load_state()
    for k, disk_pod in on_disk["pods"].items():
        pod = state["pods"].get(k)
        if pod is not None and pod.get("id") == disk_pod.get("id"):
            for flag in ("ended", "collected"):
                if disk_pod.get(flag) and not pod.get(flag):
                    pod[flag] = disk_pod[flag]
    known = {p["id"] for p in state.get("replaced", [])}
    state.setdefault("replaced", []).extend(p for p in on_disk.get("replaced", []) if p["id"] not in known)
    with open(STATE + ".tmp", "w") as fh:
        json.dump(state, fh, indent=1)
    os.replace(STATE + ".tmp", STATE)


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
def create_pod(fold):
    body = {"name": f"malaria-a0-paper-fold{fold}", "imageName": IMAGE, "gpuTypeIds": GPU_TYPES,
            "gpuTypePriority": "custom", "gpuCount": 1, "cloudType": "SECURE",
            "dataCenterIds": DATA_CENTERS, "dataCenterPriority": "custom",
            "minVCPUPerGPU": MIN_VCPU, "minRAMPerGPU": MIN_RAM_GB, "containerDiskInGb": 60, "volumeInGb": 0,
            "ports": ["22/tcp"], "supportPublicIp": True,
            "env": {"PUBLIC_KEY": open(SSH_KEY + ".pub").read().strip()}}
    return rest("POST", "/pods", body)


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


def setup(pod):
    ssh(pod, "mkdir -p /workspace/repo/src /workspace/repo/notebooks /workspace/out")
    for rel in UPLOADS:
        if os.path.exists(os.path.join(REPO, rel)):
            scp(pod, os.path.join(REPO, rel), f"/workspace/repo/{rel}", upload=True)
    script = (POD_SETUP.replace("WATCHDOG", str(WATCHDOG_SECONDS)).replace("REQUIREMENTS", REQUIREMENTS)
              .replace("NO_DEPS", NO_DEPS))
    _push_script(pod, "pod_setup.sh", script)
    _push_script(pod, "pod_train.sh", POD_TRAIN.replace("NOTEBOOK", NOTEBOOK))
    ssh(pod, "cd /workspace; setsid nohup bash pod_setup.sh > setup.log 2>&1 < /dev/null &")


def _push_script(pod, name, text):
    local = os.path.join(RESULTS, "runpod", name)
    os.makedirs(os.path.dirname(local), exist_ok=True)
    with open(local, "w") as fh:
        fh.write(text)
    scp(pod, local, f"/workspace/{name}", upload=True)


def start(pod):
    for rel in UPLOADS:  # latest notebook/module
        scp(pod, os.path.join(REPO, rel), f"/workspace/repo/{rel}", upload=True)
    # "cd ...; job &", not "cd ... && job &": the latter backgrounds a subshell that keeps this SSH session open
    ssh(pod, f"cd /workspace; setsid nohup bash pod_train.sh {pod['fold']} > train.log 2>&1 < /dev/null &")
    pod["started"] = time.time()


def stage(pod):
    return ssh(pod, "cat /workspace/STAGE 2>/dev/null || echo booting", check=False, timeout=30).strip() or "?"


def collect(pod):
    k = pod["fold"]
    dest = os.path.join(RESULTS, "folds")
    os.makedirs(dest, exist_ok=True)
    os.makedirs(os.path.join(RESULTS, "executed"), exist_ok=True)
    os.makedirs(MODELS, exist_ok=True)
    scp(pod, f"/workspace/out/fold_{k}", dest, upload=False)
    scp(pod, f"/workspace/out/executed/fold_{k}.ipynb", os.path.join(RESULTS, "executed", f"fold_{k}.ipynb"), upload=False)
    for log in ["setup.log", "train.log"]:
        scp(pod, f"/workspace/{log}", os.path.join(RESULTS, "runpod", f"fold_{k}_{log}"), upload=False)
    h5 = os.path.join(dest, f"fold_{k}", f"fold_{k}_best.h5")
    if os.path.exists(h5):
        os.replace(h5, os.path.join(MODELS, f"fold_{k}_best.h5"))  # models stay out of git


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
    print(f"Balance before: ${balance()['clientBalance']:.2f}")
    new = []
    for k in parse_folds(args.folds):
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
        start(pod)
        print(f"fold {k}: training started")
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
            elif st.startswith("train-fold") or st.startswith("done"):
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
        elif s.startswith("failed"):
            print(f"fold {k}: FAILED at {s}; pod left running for inspection (see /workspace/*.log)")
        save_state(state)


def cmd_watch(args):
    while True:
        state = load_state()
        cmd_collect(args, state)
        if spent(state) > args.max_spend:
            print(f"Spend cap ${args.max_spend} reached: terminating everything")
            cmd_down(args)
            return
        live = [p for p in state["pods"].values() if not p.get("ended")]
        if not live:
            print("All folds collected.")
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("up")
    up.add_argument("--folds", default="0-9")
    up.add_argument("--setup-only", action="store_true")
    se = sub.add_parser("setup")
    se.add_argument("--folds", required=True)
    st = sub.add_parser("start")
    st.add_argument("--folds", required=True)
    go = sub.add_parser("go")
    go.add_argument("--folds", default="0-9")
    sub.add_parser("status")
    sub.add_parser("collect")
    w = sub.add_parser("watch")
    w.add_argument("--every", type=int, default=60)
    w.add_argument("--max-spend", type=float, default=6.0)
    dn = sub.add_parser("down")
    dn.add_argument("--folds", help="only these folds (default: all)")
    args = ap.parse_args()
    {"up": cmd_up, "setup": cmd_setup, "start": cmd_start, "go": cmd_go, "status": cmd_status, "collect": cmd_collect,
     "watch": cmd_watch, "down": cmd_down}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
