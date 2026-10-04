# Results

One folder per experiment. Every number in the slides and report comes from these files.

| Folder | Experiment | Status |
|---|---|---|
| `A0_baseline/` | Paper reproduction (image split, no preprocessing) | done: Kaggle 2× T4, 3 of 10 folds |
| `A1_slide_split/` | H1: slide-grouped split | not run yet |
| `A2_yuv_slide/` | H2: slide split + YUV | not run yet |
| `A3_yuv_image/` | Control: image split + YUV | not run yet |

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

Metrics are in %, including MCC (×100). The slides show MCC as a coefficient (0.95).
Trained models (`.keras`, 47 MB each) are kept out of git, in `models/` on the owner's Mac.
