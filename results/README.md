# Results

One folder per experiment. Every number in the slides and report comes from these files.

| Folder | Experiment | Status |
|---|---|---|
| `A0_10fold_paper/` | Paper-exact reproduction from the paper's own code, all 10 folds (**reference baseline**) | done: RunPod, 10× RTX 4090 in parallel |
| `A0_baseline/` | First reproduction from the paper's text (image split, no preprocessing) | done: Kaggle 2× T4, 3 of 10 folds |
| `A1_slide_split/` | H1: patient-level split (40 held-out patients), A0's recipe otherwise | done: 10 folds |
| `A2_yuv_slide/` | H2: patient split + YUV histogram-equalisation stain normalisation | done: 10 folds |
| `A3_yuv_image/` | Control: the paper's image split + YUV | done: 10 folds |
| `ablation/` | Hypothesis tests over A0–A3 (`src/ablation_stats.py`) and their figures | done |
| `ablation_runpod/` | RunPod bookkeeping and logs of the A1–A3 run (pods, timings, setup/training logs) | done |

The analysis plan for A1–A3 (hypotheses, primary metric, tests, decision rules) is in
[`docs/phase3_analysis_plan.md`](../docs/phase3_analysis_plan.md); it was committed before the runs.

## Files in `A0_10fold_paper/`

See [`A0_10fold_paper/README.md`](A0_10fold_paper/README.md): summary JSON, paper-vs-ours table, per-fold tables
(Table 5 and Table 6 of the paper), figures, each fold's predictions and history, and the RunPod logs.
`python src/check_results.py results/A0_10fold_paper` prints the comparison with the paper.

## Files in `A0_baseline/`

| File | What it is |
|---|---|
| `A0_summary.json` | Everything in one place: config, mean ± SD over folds, ensemble metrics, paper numbers |
| `A0_vs_paper.csv` | Paper vs. ours, headline metrics, with the difference |
| `A0_baseline_per_fold_val.csv` | Each fold on its validation split (epochs, minutes, all metrics, confusion counts) |
| `A0_baseline_per_model_test.csv` | Each fold model on the hold-out test set |
| `A0_curves_cm_roc.png` | Training curves, confusion matrix, ROC curve |
| `A0_vs_paper.png` | Bar chart: paper vs. ours |
| `samples.png`, `yuv_preview.png` | Example cells, and what the YUV preprocessing looks like |
| `kaggle_run_v2.log` | Full Kaggle log of the run |

A1–A3 get the same files under their own prefix (`A1_summary.json`, `A1_slide_split_per_fold_val.csv`, ...).
When more than one experiment runs in a session, the notebook also writes `ablation.csv`: one row per experiment (fold accuracy mean ± SD, fold recall and MCC, ensemble test accuracy and MCC).
`python src/check_results.py results/<folder>` prints any of them; `python src/compare_experiments.py` puts them side by side.

## Files in `A1_slide_split/`, `A2_yuv_slide/`, `A3_yuv_image/`

Same layout as `A0_10fold_paper/`, with the experiment ID as prefix (`A1_summary.json`, `A1_per_fold_val.csv`,
`A1_per_fold_val_clean.csv`, `A1_per_model_test.csv`, `A1_vs_paper.csv`, `A1_curves_cm_roc.png`, ...), plus:

| File | What it is |
|---|---|
| `split.csv` (A1, A2) | The patient split every pod trained on: file, label, patient, role (learn / holdout), fold |
| `folds/fold_<k>/` | Each fold's history, timings, metrics (`fold_<k>.json`) and softmax outputs (`fold_<k>_predictions.npz`) |
| `executed/fold_<k>.ipynb` | The notebook as it ran on the pod for that fold |
| `yuv_examples.png` (A2) | Original vs YUV-equalised cells from eight patients |

`results/ablation_splits.json` holds the fingerprints of both splits; every training run checks them.

## Files in `ablation/`

| File | What it is |
|---|---|
| `ablation_summary.md` | The report: experiments table, the three contrasts, verdicts, extras (clean evaluation, primary) |
| `ablation_summary.json` / `.csv` | The same numbers, machine-readable (every contrast, metric and level) |
| `ablation_experiments.csv` | One row per experiment: fold mean ± SD and ensemble values with 95 % patient-bootstrap CIs |
| `ablation_per_patient.csv` | Ensemble errors per hold-out patient |
| `ablation_fold_mcc.png`, `ablation_fold_accuracy.png` | Every fold of every experiment; grey lines join paired folds |
| `ablation_contrasts.png`, `ablation_contrasts_folds.png` | The three contrasts with 95 % CIs (ensemble and fold level) |
| `ablation_per_patient.png` | Each held-out patient, A1 vs A2 |
| `paper_protocol/` | The same analysis on augmented evaluation (the paper's protocol) |

`python src/ablation_stats.py` rebuilds everything in `ablation/` from the fold predictions (about 2 minutes).

Metrics are in %, including MCC (×100). The slides show MCC as a coefficient (0.95).
Trained models are kept out of git. The 10 fold models of `A0_10fold_paper` (17 MB each) are attached to the
[`v1.0-a0-10fold` release](https://github.com/amathziah/malaria-detection/releases/tag/v1.0-a0-10fold), and the
30 models of A1–A3 to the [`v2.0-ablation` release](https://github.com/amathziah/malaria-detection/releases/tag/v2.0-ablation);
the `A0_baseline` models (`.keras`, 47 MB each) stay with the repository owner.
