"""Fill the "Metric | Paper | Ours" table on the results slide from an experiment's summary JSON.

Usage:
    python src/fill_slide_table.py                       # A0 → the slide with the results table
    python src/fill_slide_table.py --summary results/A0_baseline/A0_summary.json --slide 18

Without --slide it finds the table itself, so adding or moving slides doesn't break it.

Only run.text is edited, so the deck's fonts and colours stay as they are.
"""
import argparse
import json
import sys

from pptx import Presentation

ROWS = {  # slide row label -> (section in the summary JSON, metric key)
    "Mean fold accuracy":   ("mean_fold", "accuracy"),
    "Ensemble accuracy":    ("ensemble", "accuracy"),
    "Recall (sensitivity)": ("ensemble", "recall"),
    "Precision":            ("ensemble", "precision"),
    "F1-score":             ("ensemble", "f1"),
    "ROC-AUC":              ("ensemble", "auc"),
    "MCC":                  ("ensemble", "mcc"),
}


def fmt(label, value):
    # MCC is stored ×100 in the JSON; the slide shows it as a coefficient
    return f"{value / 100:.2f}" if label == "MCC" else f"{value:.2f} %"


def is_results_table(shape):
    return shape.has_table and [c.text.strip() for c in shape.table.rows[0].cells][:3] == ["Metric", "Paper", "Ours"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="results/A0_baseline/A0_summary.json")
    ap.add_argument("--deck", default="slides/Malaria_Phase2_Baseline_Hypothesis_filled.pptx")
    ap.add_argument("--slide", type=int, help="slide number (default: search the whole deck)")
    args = ap.parse_args()

    summary = json.load(open(args.summary))
    deck = Presentation(args.deck)
    if args.slide and not 1 <= args.slide <= len(deck.slides):
        sys.exit(f"--slide {args.slide}: the deck has {len(deck.slides)} slides")
    slides = [deck.slides[args.slide - 1]] if args.slide else list(deck.slides)
    found = [(n, sh.table) for n, sl in enumerate(deck.slides, 1) if sl in slides
             for sh in sl.shapes if is_results_table(sh)]
    if not found:
        sys.exit("No 'Metric | Paper | Ours' table found" + (f" on slide {args.slide}" if args.slide else ""))
    slide_no, table = found[0]
    print(f"Results table on slide {slide_no}")

    for row in list(table.rows)[1:]:
        label = row.cells[0].text.strip()
        if label not in ROWS:
            continue
        section, key = ROWS[label]
        runs = [r for p in row.cells[2].text_frame.paragraphs for r in p.runs]
        if not runs:  # empty cell: add a run so the text keeps the paragraph's formatting
            runs = [row.cells[2].text_frame.paragraphs[0].add_run()]
        runs[0].text = fmt(label, summary[section][key])
        for r in runs[1:]:
            r.text = ""
        print(f"{label:22s} {runs[0].text}")

    deck.save(args.deck)
    print(f"Saved {args.deck}")


if __name__ == "__main__":
    main()
