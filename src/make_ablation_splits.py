#!/usr/bin/env python3
"""Build the ablation's splits once, check them, and save them so every pod trains on exactly these.

Usage:
    python src/make_ablation_splits.py --data outputs/data/cell_images

Writes results/A1_slide_split/split.csv and results/A2_yuv_slide/split.csv (the same patient split: A2
differs from A1 only by the YUV preprocessing) and results/A2_yuv_slide/yuv_examples.png. It checks:
  * the patient key (C-number) against NIH's own patient-to-cell mapping files;
  * no patient on both sides of the hold-out split or of any fold;
  * the image split rebuilt here is A0's split (same fingerprint as the 10 A0 fold records), so A3 is
    paired with A0 cell for cell.
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marques2022_exact as mx  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NIH_MAPPING = "https://data.lhncbc.nlm.nih.gov/public/Malaria/patientid_cellmapping_{}.csv"


def nih_patient_mapping(folder):
    """{(label, file): NIH patient key} from patientid_cellmapping_{parasitized,uninfected}.csv.

    Each line is "<key>,[<python list of file names>],,,," (the trailing commas break csv/literal_eval).
    """
    out = {}
    for label in mx.TIPOS:
        path = os.path.join(folder, f"patientid_cellmapping_{label.lower()}.csv")
        if not os.path.exists(path):
            os.makedirs(folder, exist_ok=True)
            urllib.request.urlretrieve(NIH_MAPPING.format(label.lower()), path)
        with open(path) as fh:
            for line in fh:
                key = line.split(",", 1)[0].strip()
                for f in re.findall(r"'([^']+\.png)'", line):
                    out[(label, f)] = key
    return out


def check_against_nih(df, mapping):
    missing = [(l, f) for f, l in zip(df["file"], df["label"]) if (l, f) not in mapping]
    if missing or len(mapping) != len(df):
        sys.exit(f"NIH mapping mismatch: {len(missing)} files unmapped, {len(mapping)} mapped vs {len(df)} files")
    ours = {(l, f): mx.patient_id(f) for f, l in zip(df["file"], df["label"])}
    key_to_ours = {}
    for k, key in mapping.items():
        key_to_ours.setdefault(key, set()).add(ours[k])
    split_keys = {key: p for key, p in key_to_ours.items() if len(p) > 1}
    if split_keys:
        sys.exit(f"an NIH patient key spans several C-numbers: {split_keys}")
    merged = {}
    for key, p in key_to_ours.items():
        merged.setdefault(p.pop(), []).append(key)
    multi = {p: keys for p, keys in merged.items() if len(keys) > 1}
    print(f"NIH mapping: all {len(df):,} files mapped; {len(key_to_ours)} NIH keys -> {len(merged)} patients "
          f"(merged: {multi})")


def a0_fingerprint():
    found = {json.load(open(p))["split_fingerprint"]
             for p in glob.glob(os.path.join(REPO, "results", "A0_10fold_paper", "folds", "fold_*", "fold_*.json"))}
    return found.pop() if len(found) == 1 else None


def describe(name, learn, val, folds):
    pts = lambda d: d["file"].map(mx.patient_id).nunique()
    par = (val["label"] == "Parasitized").sum()
    print(f"{name}: learning set {len(learn):,} cells / {pts(learn)} patients; hold-out {len(val):,} cells / "
          f"{pts(val)} patients, {par:,} parasitized ({100 * par / len(val):.1f} %)")
    for k, (tr, te) in enumerate(folds):
        t = learn.iloc[te]
        print(f"  fold {k}: train {len(tr):,}, test {len(te):,} cells / {pts(t)} patients, "
              f"{100 * (t['label'] == 'Parasitized').mean():.1f} % parasitized")


def yuv_examples(df, out_path, seed=1234):
    """4 parasitized + 4 uninfected cells from 8 different patients: original vs YUV-equalised."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(seed)
    picks = []
    for label in mx.TIPOS:
        sub = df[df["label"] == label]
        for p in rng.permutation(sub["file"].map(mx.patient_id).unique()):
            if len([x for x in picks if x[1] == label]) == 4:
                break
            if p in {mx.patient_id(f) for f, _, _ in picks}:
                continue
            row = sub[sub["file"].map(mx.patient_id) == p].sample(1, random_state=seed).iloc[0]
            picks.append((row["file"], label, row["path"]))
    fig, axes = plt.subplots(2, 8, figsize=(16, 4.6))
    for c, (f, label, path) in enumerate(picks):
        axes[0, c].imshow(mx.load_resized(path))
        axes[0, c].set_title(f"{label}\n{mx.patient_id(f)}", fontsize=9)
        axes[1, c].imshow(mx.load_resized(path, preprocess="yuv"))
    axes[0, 0].set_ylabel("original (A0, A1)")
    axes[1, 0].set_ylabel("YUV + hist-eq (A2, A3)")
    for a in axes.ravel():
        a.set_xticks([])
        a.set_yticks([])
    fig.suptitle("H2 input: luma (Y) histogram-equalised at native size, colour (U, V) unchanged", fontsize=12)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130)
    print("Saved", os.path.relpath(out_path, REPO))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "outputs", "data", "cell_images"))
    ap.add_argument("--mapping-dir", default=os.path.join(REPO, "outputs", "data", "nih_patient_mapping"))
    args = ap.parse_args()

    df = mx.index_dataset(mx.find_or_download(args.data))
    print(f"Images: {len(df):,} {df['label'].value_counts().to_dict()}")
    check_against_nih(df, nih_patient_mapping(args.mapping_dir))

    learn, val, folds = mx.make_split(df, "image")
    fp_image, fp_a0 = mx.split_fingerprint(learn, val, folds), a0_fingerprint()
    print(f"Image split (A0, A3): fingerprint {fp_image}; A0 fold records: {fp_a0}")
    if fp_a0 is not None and fp_image != fp_a0:
        sys.exit("the image split rebuilt here is not A0's split: A3 would not be paired with A0")

    learn, val, folds = mx.make_split(df, "patient")
    describe("Patient split (A1, A2)", learn, val, folds)
    fp_patient = mx.split_fingerprint(learn, val, folds)
    for exp in ["A1", "A2"]:
        folder = os.path.join(REPO, "results", mx.EXPERIMENTS[exp]["folder"])
        os.makedirs(folder, exist_ok=True)
        path = mx.save_split(os.path.join(folder, "split.csv"), learn, val, folds)
        again = mx.split_fingerprint(*mx.load_split(path, df))
        assert again == fp_patient, (again, fp_patient)
        print(f"Saved {os.path.relpath(path, REPO)} (fingerprint {fp_patient})")
    with open(os.path.join(REPO, "results", "ablation_splits.json"), "w") as fh:
        json.dump({"image": fp_image, "patient": fp_patient}, fh, indent=1)
    yuv_examples(df, os.path.join(REPO, "results", mx.EXPERIMENTS["A2"]["folder"], "yuv_examples.png"))


if __name__ == "__main__":
    main()
