#!/usr/bin/env python3
"""Score the Phase 3b blind triage against the answer key (docs/blind_triage_protocol.md, scoring plan).

Two raters each fill in a sheet for the 172 numbered gallery cells without knowing which are errors. Once both sheets
are in, this script opens the key and reports what the scoring plan fixed before anyone rated, and nothing more:

- Cohen's kappa between the raters on parasite_visible (yes / no / unsure), the raw percent agreement, and how many
  cells both answered;
- for each group (false alarms, misses, correctly called parasitized and uninfected cells): n, the cells both raters
  marked "yes", the cells both marked "no", and the rest;
- each rater's category counts in each group.

Blank answers count as missing. The labels are never changed. The report holds counts only, never a cell's id or file.

Usage:
    python src/triage_score.py --sheets Triage_Sheet_RaterA.xlsx Triage_Sheet_RaterB.xlsx
    # reads results/phase3b/phase3b_error_gallery_KEY.csv, writes results/phase3b/phase3b_triage_scores.json and .md
    # and prints the markdown; --key and --out change those paths, and the sheets may also be .csv
"""
import argparse
import json
import os

import pandas as pd
from sklearn.metrics import cohen_kappa_score

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
COLUMNS = ["id", "parasite_visible", "category", "notes"]  # columns A-D of a sheet
VISIBLE = ["yes", "no", "unsure"]
CATEGORIES = ["clear parasite", "faint edge dot", "stain precipitate or debris", "platelet-like inclusion",
              "segmentation problem", "blur or colour cast", "nothing visible", "cannot tell"]
MISSING = "missing"  # a blank category, in the category counts
GROUPS = {("uninfected", "parasitized"): "false_alarm", ("parasitized", "uninfected"): "miss",  # (label, model call)
          ("parasitized", "parasitized"): "correct_parasitized", ("uninfected", "uninfected"): "correct_uninfected"}


def _text(value):
    """A cell's text, stripped; None when blank."""
    text = "" if value is None else str(value).strip()
    return text or None


def _answer(value):
    """A cell's text, stripped and lower-cased; None when blank."""
    text = _text(value)
    return text and text.lower()


def read_sheet(path):
    """A rater's sheet as a DataFrame of id, parasite_visible, category and notes, blanks as None.

    .xlsx: columns A-D of the worksheet "Triage" below its header row; the instructions panel beside them is ignored.
    .csv: the same four columns. Answers are stripped and lower-cased; an id that is not a whole number, or an answer
    outside the rubric, raises ValueError naming it. Whether the ids are the key's is checked by score().
    """
    name = os.path.basename(path)
    if path.lower().endswith(".xlsx"):
        from openpyxl import load_workbook
        cells = load_workbook(path, data_only=True)["Triage"].iter_rows(min_row=2, max_col=4, values_only=True)
    else:
        cells = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig").iloc[:, :4].values.tolist()
    rows = [[_text(i), _answer(v), _answer(c), _text(n)] for i, v, c, n in cells]
    sheet = pd.DataFrame([row for row in rows if any(row)], columns=COLUMNS)  # rows blank in A-D hold no answer
    ids = pd.to_numeric(sheet["id"], errors="coerce")
    bad = sheet["id"][ids.isna() | (ids % 1 != 0)].tolist()
    if bad:
        raise ValueError(f"{name}: ids must be whole numbers, found {bad}")
    sheet["id"] = ids.astype(int)
    for column, allowed in (("parasite_visible", VISIBLE), ("category", CATEGORIES)):
        bad = sheet[sheet[column].notna() & ~sheet[column].isin(allowed)]
        if len(bad):
            found = ", ".join(f"{value!r} at id {i}" for i, value in zip(bad["id"], bad[column]))
            raise ValueError(f"{name}: {column} must be one of {allowed}; found {found}")
    return sheet


def cell_groups(key):
    """Each cell's group, indexed by id: false_alarm (labelled uninfected, called parasitized), miss (labelled
    parasitized, called uninfected), correct_parasitized or correct_uninfected."""
    return pd.Series([GROUPS[pair] for pair in zip(key["label"], key["model_call"])], index=key["id"], name="group")


def _aligned(sheet, ids, rater):
    """The sheet indexed by id, in the key's order. ValueError naming any id missing from it, extra or repeated."""
    got = sheet["id"]
    problems = {"missing": set(ids) - set(got), "extra": set(got) - set(ids),
                "duplicated": set(got[got.duplicated()])}
    found = [f"{what} ids {sorted(int(i) for i in bad)}" for what, bad in problems.items() if bad]
    if found:
        raise ValueError(f"sheet {rater}: " + "; ".join(found))
    return sheet.set_index("id").loc[ids]


def _kappa(a, b):
    """Cohen's kappa of paired answers; None when it is undefined: no pairs, or both raters gave one identical answer
    throughout (chance agreement is then 1, so kappa is 0 / 0)."""
    if len(set(a) | set(b)) < 2:
        return None
    return float(cohen_kappa_score(list(a), list(b), labels=VISIBLE))


def _both(a, b):
    """n, the cells both raters marked "yes", both marked "no", and the rest."""
    yes, no = int(((a == "yes") & (b == "yes")).sum()), int(((a == "no") & (b == "no")).sum())
    return {"n": len(a), "both_yes": yes, "both_no": no, "rest": len(a) - yes - no}


def _counts(categories):
    """How often each category was chosen, zeros included and blanks as "missing"."""
    counts = categories.fillna(MISSING).value_counts()
    return {c: int(counts.get(c, 0)) for c in CATEGORIES + [MISSING]}


def score(key, sheet_a, sheet_b):
    """The scores fixed in the scoring plan, as a JSON-serialisable dict. Sheets are as read_sheet returns them, and
    their ids must be exactly the key's (ValueError otherwise).

    parasite_visible: kappa, percent_agreement and n_both_answered, over the cells both raters answered. kappa is None
        when undefined (no such cell, or one identical answer throughout); percent_agreement is None with no such cell.
    missing: blank answers per rater, for parasite_visible and category.
    groups: per group, n, both_yes, both_no and rest (the raters disagree, or either said "unsure" or left it blank).
    categories: per rater and group, the count of each category and of "missing".
    """
    groups = cell_groups(key)
    sheets = {"A": _aligned(sheet_a, groups.index, "A"), "B": _aligned(sheet_b, groups.index, "B")}
    a, b = sheets["A"]["parasite_visible"], sheets["B"]["parasite_visible"]
    both = a.notna() & b.notna()
    n = int(both.sum())
    return {
        "parasite_visible": {"kappa": _kappa(a[both], b[both]),
                             "percent_agreement": 100 * int((a[both] == b[both]).sum()) / n if n else None,
                             "n_both_answered": n},
        "missing": {r: {c: int(s[c].isna().sum()) for c in ("parasite_visible", "category")}
                    for r, s in sheets.items()},
        "groups": {g: _both(a[groups == g], b[groups == g]) for g in GROUPS.values()},
        "categories": {r: {g: _counts(s["category"][groups == g]) for g in GROUPS.values()}
                       for r, s in sheets.items()},
    }


def report_markdown(scores):
    """The scores as a markdown report: counts only, never a cell's id, file or label."""
    pv, files = scores["parasite_visible"], scores.get("sheets")  # main() records the sheets' file names
    kappa = ("undefined (no cell answered by both, or one identical answer throughout)" if pv["kappa"] is None
             else f"{pv['kappa']:.3f}")
    agreement = "undefined" if pv["percent_agreement"] is None else f"{pv['percent_agreement']:.1f} %"
    names = [g.replace("_", " ").capitalize() for g in GROUPS.values()]
    lines = ["# Blind triage: scores against the answer key", ""]
    if files:
        lines += [f"Rater A: `{files['A']}`. Rater B: `{files['B']}`.", ""]
    lines += ["Counts only. The labels are not changed.", "",
              "## Agreement on parasite_visible (yes / no / unsure)", "",
              f"- Cohen's kappa: {kappa}",
              f"- Raw agreement: {agreement}",
              f"- Cells both raters answered: {pv['n_both_answered']}",
              "- Blank answers: " + "; ".join(f"rater {r} {m['parasite_visible']} parasite_visible, "
                                              f"{m['category']} category" for r, m in scores["missing"].items()),
              "", "## Cells both raters marked yes or no, by group", "",
              "| Group | Label | Model call | n | Both yes | Both no | Rest |", "|---|---|---|---:|---:|---:|---:|"]
    for ((label, call), group), name in zip(GROUPS.items(), names):
        c = scores["groups"][group]
        lines.append(f"| {name} | {label} | {call} | {c['n']} | {c['both_yes']} | {c['both_no']} | {c['rest']} |")
    lines += ["",
              "- False alarms both yes: candidates for parasites the labeller missed. Compare: correct uninfected.",
              "- Misses both no: candidates for wrong labels or parasites too faint to see. Compare: correct "
              "parasitized.",
              "- Rest: the raters disagree, or at least one answered unsure or left the cell blank."]
    for rater, by_group in scores["categories"].items():
        lines += ["", f"## Categories, rater {rater}", "",
                  "| Category | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
        lines += [f"| {c} | " + " | ".join(str(by_group[g][c]) for g in GROUPS.values()) + " |"
                  for c in CATEGORIES + [MISSING]]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sheets", nargs=2, required=True, metavar=("A", "B"),
                    help="the two raters' sheets, .xlsx or .csv")
    ap.add_argument("--key", default=os.path.join(REPO, "results", "phase3b", "phase3b_error_gallery_KEY.csv"))
    ap.add_argument("--out", default=os.path.join(REPO, "results", "phase3b", "phase3b_triage_scores"),
                    help="writes <out>.json and <out>.md")
    args = ap.parse_args()
    scores = {"sheets": dict(zip("AB", map(os.path.basename, args.sheets))),
              **score(pd.read_csv(args.key), *map(read_sheet, args.sheets))}
    md = report_markdown(scores)
    with open(args.out + ".json", "w") as fh:
        json.dump(scores, fh, indent=2)
    with open(args.out + ".md", "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md, end="")


if __name__ == "__main__":
    main()
