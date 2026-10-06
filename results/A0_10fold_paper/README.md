# A0 — full 10-fold reproduction, following the paper's code

All 10 folds of Marques et al. (2022), trained with the recipe from the paper's own executed notebook
(Springer supplementary file MOESM1): noisy-student EfficientNet-B0, the 128-64-32 dense head, label smoothing 0.1,
batch 16, 33 epochs, ReduceLROnPlateau (factor 0.5), 20 % hold-out set, the albumentations pipeline.
Notebook: `notebooks/Phase2_A0_10fold_PaperExact.ipynb` (recipe in `src/marques2022_exact.py`, checked by
`tests/test_marques2022_exact.py`). One RunPod RTX 4090 per fold, launched with `src/runpod_10fold.py`.

`results/A0_baseline/` (the first, 3-fold reproduction from the paper's text) is unchanged.

Two evaluation views:
* **paper protocol** — every prediction is made on a randomly augmented image, as in the paper's code
  (its test and validation generators used the augmenting `ImageDataAugmentor`). These are the headline numbers.
* **clean** — the same models on the original images (`*_clean*` files).

| File | What it is |
|---|---|
| `A0_10fold_summary.json` | Everything in one place: recipe, mean ± SD over folds, ensemble (both views), the paper's numbers |
| `A0_10fold_vs_paper.csv` | Paper vs. ours, headline metrics |
| `A0_10fold_per_fold_val.csv` | Each fold model on its CV test part (the paper's Table 5), paper protocol; `_clean` = clean view |
| `A0_10fold_per_model_test.csv` | Each fold model on the 5,512-image hold-out set (the paper's Table 6); `_clean` = clean view |
| `A0_10fold_curves_cm.png` | Validation curves of all folds and the ensemble confusion matrix |
| `A0_10fold_roc_vs_paper.png` | ROC curves (folds + ensemble) and paper vs. ours |
| `folds/fold_k/` | Per fold: `fold_k.json` (history, timings, every metric) and `fold_k_predictions.npz` (softmax outputs) |
| `executed/fold_k.ipynb` | The notebook as it ran on fold k's pod, with the training log |
| `runpod/` | Pod ids, GPU, timings (`pods.json`), the setup/training scripts and logs |

Metrics are in %, MCC ×100, like `results/A0_baseline/`. `python src/check_results.py results/A0_10fold_paper`
prints the summary. The trained weights (`fold_k_best.h5`, 17 MB each) are in `models/A0_10fold_paper/` (git-ignored).

**Comparing with the paper:** its text swaps the ensemble's precision and recall. Its own printed report
(2,744 parasitized cells, 62 missed; 2,768 uninfected, 32 flagged) gives recall 97.74 % and precision 98.82 %,
which is what we compare against.
