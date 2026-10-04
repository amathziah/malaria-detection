"""Put every finished experiment side by side and answer H1/H2 from the numbers.

Usage:
    python src/compare_experiments.py                 # reads results/*/*_summary.json
    python src/compare_experiments.py --out docs/ablation.md

Experiments that haven't been run yet are listed as "not run".
"""
import argparse
import glob
import json
import os

EXPERIMENTS = [  # id, folder, split, preprocessing
    ("A0", "A0_baseline",    "image", "none"),
    ("A1", "A1_slide_split", "slide", "none"),
    ("A2", "A2_yuv_slide",   "slide", "YUV + hist-eq"),
    ("A3", "A3_yuv_image",   "image", "YUV + hist-eq"),
]
QUESTIONS = [  # (experiment, compared with, what the difference tells us)
    ("A1", "A0", "H1: accuracy change once slide leakage is removed"),
    ("A2", "A1", "H2: gain from YUV stain normalisation on unseen slides"),
    ("A3", "A0", "Control: gain from YUV when slides are shared"),
]


def load(root):
    found = {}
    for exp_id, folder, _, _ in EXPERIMENTS:
        paths = glob.glob(os.path.join(root, folder, "*_summary.json"))
        if paths:
            found[exp_id] = json.load(open(paths[0]))
    return found


def table(found):
    lines = ["| ID | Split | Preprocessing | Fold acc. (mean ± SD) | Ens. acc. | Recall | MCC | Folds |",
             "|---|---|---|---|---|---|---|---|"]
    for exp_id, _, split, prep in EXPERIMENTS:
        s = found.get(exp_id)
        if s is None:
            lines.append(f"| {exp_id} | {split} | {prep} | not run | | | | |")
            continue
        m, sd, e = s["mean_fold"], s["sd_fold"], s["ensemble"]
        lines.append(f"| {exp_id} | {split} | {prep} | {m['accuracy']:.2f} ± {sd['accuracy']:.2f} | "
                     f"{e['accuracy']:.2f} | {e['recall']:.2f} | {e['mcc'] / 100:.2f} | "
                     f"{s['folds_run']}/{s['config']['N_FOLDS']} |")
    return "\n".join(lines)


def answers(found):
    lines = []
    for a, b, question in QUESTIONS:
        if a in found and b in found:
            d_fold = found[a]["mean_fold"]["accuracy"] - found[b]["mean_fold"]["accuracy"]
            d_ens = found[a]["ensemble"]["accuracy"] - found[b]["ensemble"]["accuracy"]
            lines.append(f"- {question} ({a} − {b}): fold accuracy {d_fold:+.2f} pp, ensemble {d_ens:+.2f} pp")
        else:
            lines.append(f"- {question} ({a} − {b}): waiting for {' and '.join(x for x in (a, b) if x not in found)}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", help="also write the table to this markdown file")
    args = ap.parse_args()

    found = load(args.results)
    text = table(found) + "\n\n" + answers(found) + "\n"
    print(text)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
        print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
