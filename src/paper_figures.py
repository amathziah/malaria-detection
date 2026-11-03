#!/usr/bin/env python3
"""Redraw the figures the paper and the deck print, from saved results only: no statistic is recomputed.

Reads the saved fold predictions, results/ablation/ablation_summary.json and results/phase3b/phase3b_summary.json,
and rewrites only PNG files:

- results/ablation/ablation_fold_mcc.png, ablation_fold_accuracy.png  (paper Fig. 4, deck)
- results/ablation/ablation_contrasts.png (deck, one row) and ablation_contrasts_2x2.png (paper Fig. 5)
- results/ablation/ablation_contrasts_folds.png
- results/phase3b/phase3b_leakage.png (paper Fig. 3, deck) and phase3b_equivalence.png
- results/A2_yuv_slide/yuv_examples.png (paper Fig. 1), when the cell images are in outputs/data/cell_images

docs/figures/make_architecture.py draws paper Fig. 2.

    python src/paper_figures.py
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ablation_figures as figs  # noqa: E402
import ablation_stats as st  # noqa: E402
import make_ablation_splits as splits  # noqa: E402
import marques2022_exact as mx  # noqa: E402
import phase3b_analysis as p3  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(results=os.path.join(REPO, "results"), images=os.path.join(REPO, "outputs", "data", "cell_images")):
    abl_dir, p3_dir = os.path.join(results, "ablation"), os.path.join(results, "phase3b")
    abl = json.load(open(os.path.join(abl_dir, "ablation_summary.json")))
    s3 = json.load(open(os.path.join(p3_dir, "phase3b_summary.json")))
    found = {exp: st.load_experiment(results, exp) for exp in ["A0", "A1", "A2", "A3"]}
    found = {exp: e for exp, e in found.items() if e is not None}
    written = [figs.fold_strip(found, "mcc", path=os.path.join(abl_dir, "ablation_fold_mcc.png")),
               figs.fold_strip(found, "accuracy", path=os.path.join(abl_dir, "ablation_fold_accuracy.png")),
               figs.contrast_forest(abl["contrasts"], path=os.path.join(abl_dir, "ablation_contrasts.png")),
               figs.contrast_forest(abl["contrasts"], ncols=2, path=os.path.join(abl_dir, "ablation_contrasts_2x2.png")),
               figs.contrast_forest(abl["contrasts"], level="fold",
                                    path=os.path.join(abl_dir, "ablation_contrasts_folds.png")),
               p3.leakage_figure(abl, s3["E2"], os.path.join(p3_dir, "phase3b_leakage.png")),
               p3.equivalence_figure(s3["E1"], os.path.join(p3_dir, "phase3b_equivalence.png"))]
    if os.path.isdir(images):
        out = os.path.join(results, mx.EXPERIMENTS["A2"]["folder"], "yuv_examples.png")
        splits.yuv_examples(mx.index_dataset(images), out)
        written.append(out)
    for path in written:
        print("Saved", os.path.relpath(path, REPO))


if __name__ == "__main__":
    main()
