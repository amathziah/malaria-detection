#!/bin/bash
set -uo pipefail
FOLD=$1; W=/workspace
stage() { echo "$1" > $W/STAGE; echo "[$(date +%T)] $1"; }
NV=$(python -c "import site, os; print(os.path.join(site.getsitepackages()[0], 'nvidia', 'cuda_nvcc'))")
export XLA_FLAGS="--xla_gpu_cuda_data_dir=$NV" PATH="$NV/bin:$PATH" TF_GPU_THREAD_MODE=gpu_private TF_CPP_MIN_LOG_LEVEL=1
mkdir -p $W/out/executed
cd $W/repo/notebooks
stage train-fold-$FOLD
papermill Phase2_A0_10fold_PaperExact.ipynb $W/out/executed/fold_$FOLD.ipynb -k paper311 --log-output \
  -y "{FOLDS_TO_TRAIN: [$FOLD], AGGREGATE: false, DATA_DIR: $W/data, OUT_DIR: $W/out, CACHE_PATH: $W/cache.npy, N_WORKERS: null}" \
  && stage done-fold-$FOLD || stage failed-fold-$FOLD
