# Results

One folder per experiment. Every number in the slides and report comes from these files.

| Folder | Experiment | Status |
|---|---|---|
| `A0_10fold_paper/` | Paper-exact reproduction from the paper's own code, all 10 folds (**reference baseline**) | done: RunPod, 10× RTX 4090 in parallel |
| `A0_baseline/` | First reproduction from the paper's text (image split, no preprocessing) | done: Kaggle 2× T4, 3 of 10 folds |
| `A1_slide_split/` | H1: slide-grouped split | not run yet |
| `A2_yuv_slide/` | H2: slide split + YUV | not run yet |
| `A3_yuv_image/` | Control: image split + YUV | not run yet |

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

Metrics are in %, including MCC (×100). The slides show MCC as a coefficient (0.95).
Trained models are kept out of git. The 10 fold models of `A0_10fold_paper` (17 MB each) are attached to the
[`v1.0-a0-10fold` release](https://github.com/amathziah/malaria-detection/releases/tag/v1.0-a0-10fold);
the `A0_baseline` models (`.keras`, 47 MB each) stay with the repository owner.
