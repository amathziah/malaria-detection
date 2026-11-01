#!/bin/bash
set -uo pipefail
FOLD=$1; EXPS=${2:-A1 A2 A3}; W=/workspace
stage() { echo "$1" > $W/STAGE; echo "[$(date +%T)] $1"; }
NV=$(python -c "import site, os; print(os.path.join(site.getsitepackages()[0], 'nvidia', 'cuda_nvcc'))")
export XLA_FLAGS="--xla_gpu_cuda_data_dir=$NV" PATH="$NV/bin:$PATH" TF_GPU_THREAD_MODE=gpu_private TF_CPP_MIN_LOG_LEVEL=1
mkdir -p $W/out/executed
cd $W/repo/notebooks
: > $W/FAILED
for EXP in ${EXPS//,/ }; do
  stage train-$EXP-fold-$FOLD
  if papermill Phase3_Ablation_A1_A3.ipynb $W/out/executed/${EXP}_fold_$FOLD.ipynb -k paper311 --log-output \
      -y "{EXPERIMENTS: [$EXP], FOLDS_TO_TRAIN: [$FOLD], AGGREGATE: false, DATA_DIR: $W/data, CACHE_DIR: $W, RESULTS_ROOT: $W/repo/results, FOLDS_ROOT: $W/out, N_WORKERS: null}"; then
    echo $EXP >> $W/DONE
  else
    echo $EXP >> $W/FAILED
  fi
done
if [ -s $W/FAILED ]; then stage partial-fold-$FOLD-failed-$(paste -sd, $W/FAILED); else stage done-fold-$FOLD; fi
