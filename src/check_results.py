"""Print an experiment's results and check them against the paper.

Usage:
    python src/check_results.py                          # A0 baseline
    python src/check_results.py results/A1_slide_split   # any experiment folder
"""
import glob
import json
import os
import sys

import pandas as pd

TOLERANCE_PP = 1.0  # success criterion: within about 1 percentage point of the paper
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # works from any folder


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "results", "A0_baseline")
    found = sorted(glob.glob(os.path.join(folder, "*_summary.json")))
    if not found:
        sys.exit(f"No *_summary.json in {folder}/ (run the notebook on Kaggle first).")
    s = json.load(open(found[0]))

    print(f"Experiment folder : {folder}")
    if "split" in s:
        print(f"Split / preprocess: {s['split']} / {s['preprocess']}")
    print(f"Images / slides   : {s['n_images']:,} / {s['n_slides']}")
    print(f"Folds run         : {s['folds_run']} of {s['config']['N_FOLDS']}\n")

    for f in glob.glob(os.path.join(folder, "*_per_fold_val.csv")):
        folds = pd.read_csv(f)
        print("Per-fold validation:")
        print(folds[["fold", "epochs", "minutes", "accuracy", "recall", "precision", "mcc"]].round(2).to_string(index=False))
        print()

    paper, mean, sd, ens = s["paper"], s["mean_fold"], s["sd_fold"], s["ensemble"]
    rows = [
        ("Mean fold accuracy", paper["mean_fold_accuracy"], mean["accuracy"]),
        ("Ensemble accuracy",  paper["accuracy"],           ens["accuracy"]),
        ("Recall",             paper["recall"],             ens["recall"]),
        ("Precision",          paper["precision"],          ens["precision"]),
        ("F1",                 paper["f1"],                 ens["f1"]),
        ("ROC-AUC",            paper["auc"],                ens["auc"]),
    ]
    print(f"{'Metric':20s} {'Paper':>8s} {'Ours':>8s} {'Δ pp':>7s}")
    for name, p, o in rows:
        flag = "" if abs(o - p) <= TOLERANCE_PP else "  ← more than 1 pp"
        print(f"{name:20s} {p:8.2f} {o:8.2f} {o - p:+7.2f}{flag}")
    print(f"{'MCC':20s} {'—':>8s} {ens['mcc'] / 100:8.2f}")
    print(f"\nMean fold accuracy SD: ±{sd['accuracy']:.2f}")
    print(f"Test set: {ens['FN']} infected cells missed, {ens['FP']} healthy cells flagged")

    # The 1 pp target only applies to the reproduction (image split, no preprocessing).
    # A1–A3 change the protocol on purpose, so a gap there is a result, not a failure.
    if s.get("split", "image") != "image" or s.get("preprocess", "none") != "none":
        print("\nVerdict: not a reproduction run; compare it with A0: python src/compare_experiments.py")
        return
    ok = all(abs(o - p) <= TOLERANCE_PP for _, p, o in rows[:2])
    print("\nVerdict:", "✅ within 1 pp of the paper" if ok else "❌ more than 1 pp from the paper")


if __name__ == "__main__":
    main()
