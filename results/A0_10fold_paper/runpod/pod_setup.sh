#!/bin/bash
set -uo pipefail
W=/workspace; cd $W
stage() { echo "$1" > $W/STAGE; echo "[$(date +%T)] $1"; }
( sleep 7200; runpodctl remove pod $RUNPOD_POD_ID ) >/dev/null 2>&1 &
stage network-check
TF_WHEEL=$(curl -s -m 15 https://pypi.org/pypi/tensorflow/2.15.1/json | python -c "import json, sys; print([u['url'] for u in json.load(sys.stdin)['urls'] if 'cp311-cp311-manylinux' in u['filename'] and 'x86_64' in u['filename']][0])")
SPEED=$(curl -s -m 10 -r 0-50000000 -o /dev/null -w "%{speed_download}" "$TF_WHEEL" | cut -d. -f1)
echo "PyPI download speed: $((SPEED / 1000000)) MB/s"
[ "${SPEED:-0}" -gt 2000000 ] || { stage failed-network; exit 1; }
stage pip
export PIP_ROOT_USER_ACTION=ignore PIP_DISABLE_PIP_VERSION_CHECK=1
pip install -q uv || { stage failed-pip; exit 1; }
grep -vE "^(albumentations|imgaug)==" $W/repo/src/runpod_requirements.txt > $W/req_main.txt
grep -E "^(albumentations|imgaug)==" $W/repo/src/runpod_requirements.txt > $W/req_nodeps.txt
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
