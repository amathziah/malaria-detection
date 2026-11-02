"""Tests for src/triage_score.py: scoring the Phase 3b blind triage against the answer key.

Every key and sheet here is synthetic. The real key is never read, so no test output can show a rater an answer.
"""
import json
import os
import re
import subprocess
import sys

import openpyxl
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import triage_score as ts  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "src", "triage_score.py")
COLUMNS = ["id", "parasite_visible", "category", "notes"]

# A synthetic key in the real key's columns. False alarms (labelled uninfected, called parasitized): 1, 5, 9.
# Misses (labelled parasitized, called uninfected): 2, 6, 7, 11. Correct: parasitized 4, 8; uninfected 3, 10, 12.
KEY = pd.DataFrame(dict(
    id=range(1, 13),
    file=[f"cell_{i}.png" for i in range(1, 13)],
    label=["uninfected", "parasitized", "uninfected", "parasitized", "uninfected", "parasitized",
           "parasitized", "parasitized", "uninfected", "uninfected", "parasitized", "uninfected"],
    p_parasitized=[0.91, 0.12, 0.05, 0.97, 0.66, 0.31, 0.08, 0.88, 0.73, 0.02, 0.44, 0.10],
    model_call=["parasitized", "uninfected", "uninfected", "parasitized", "parasitized", "uninfected",
                "uninfected", "parasitized", "parasitized", "uninfected", "uninfected", "uninfected"],
    error=[True, True, False, False, True, True, True, False, True, False, True, False]))

# The two raters' answers to KEY's cells. None is a blank.
#           id   rater A: parasite_visible, category          rater B: parasite_visible, category
ANSWERS = [(1,  "yes",    "clear parasite",           "yes",    "clear parasite"),
           (2,  "no",     "nothing visible",          "no",     "nothing visible"),
           (3,  "no",     "nothing visible",          "no",     "stain precipitate or debris"),
           (4,  "yes",    "clear parasite",           "yes",    "clear parasite"),
           (5,  "yes",    "faint edge dot",           "no",     "nothing visible"),
           (6,  "no",     "nothing visible",          "unsure", "cannot tell"),
           (7,  "no",     "blur or colour cast",      "no",     "nothing visible"),
           (8,  "yes",    "clear parasite",           None,     None),
           (9,  "unsure", "platelet-like inclusion",  "unsure", "cannot tell"),
           (10, "no",     "nothing visible",          None,     "nothing visible"),
           (11, "yes",    "faint edge dot",           "yes",    "clear parasite"),
           (12, "yes",    "segmentation problem",     "yes",    "faint edge dot")]
ROWS_A = [[i, visible, category, None] for i, visible, category, _, _ in ANSWERS]
ROWS_B = [[i, visible, category, None] for i, _, _, visible, category in ANSWERS]


def frame(rows):
    """A sheet as read_sheet returns it."""
    return pd.DataFrame(rows, columns=COLUMNS)


def visible_only(answers):
    """A sheet for ids 1..n holding only these parasite_visible answers."""
    return frame([[i, v, None, None] for i, v in enumerate(answers, start=1)])


def write_xlsx(path, rows):
    """A workbook laid out like the team's Triage_Sheet.xlsx, with traps: another tab comes first, and an instructions
    panel in F-I holds a name, a formula and an example row that repeats the header with answers outside the rubric.
    Only columns A-D of the "Triage" tab are answers."""
    wb = openpyxl.Workbook()
    wb.active.title = "Rubric"
    wb.active.append(COLUMNS)
    wb.active.append([1, "maybe", "not a category", None])
    ws = wb.create_sheet("Triage")
    ws.append(COLUMNS)
    for row in rows:
        ws.append(row)
    ws["F1"], ws["F2"], ws["G2"] = "How to fill in this sheet", "Your name:", "Rater"
    ws["F3"], ws["G3"] = "Progress:", '=COUNTA(B2:B173)&" of 172 cells done"'
    for col, header, example in zip("FGHI", COLUMNS, ["e.g.", "maybe", "not a category", "an example"]):
        ws[f"{col}20"], ws[f"{col}21"] = header, example
    wb.save(path)


def write_csv(path, rows):
    frame(rows).to_csv(path, index=False)


# --------------------------------------------------------------------------- groups and counts
def test_cell_groups_name_each_cell_by_its_label_and_the_models_call():
    key = pd.DataFrame(dict(id=[3, 1, 4, 2], file=["c.png", "a.png", "d.png", "b.png"],
                            label=["uninfected", "parasitized", "parasitized", "uninfected"],
                            p_parasitized=[0.8, 0.3, 0.9, 0.1],
                            model_call=["parasitized", "uninfected", "parasitized", "uninfected"],
                            error=[True, True, False, False]))
    assert ts.cell_groups(key).to_dict() == {3: "false_alarm", 1: "miss", 4: "correct_parasitized",
                                             2: "correct_uninfected"}


def test_score_counts_cells_both_raters_marked_yes_or_no_in_each_group():
    groups = ts.score(KEY, frame(ROWS_A), frame(ROWS_B))["groups"]
    assert groups == {"false_alarm": dict(n=3, both_yes=1, both_no=0, rest=2),          # 5 yes/no, 9 unsure twice
                      "miss": dict(n=4, both_yes=1, both_no=2, rest=1),                 # 6 no/unsure
                      "correct_parasitized": dict(n=2, both_yes=1, both_no=0, rest=1),  # 8 yes/blank
                      "correct_uninfected": dict(n=3, both_yes=1, both_no=1, rest=1)}   # 10 no/blank


def test_score_counts_each_raters_categories_and_blanks_in_each_group():
    s = ts.score(KEY, frame(ROWS_A), frame(ROWS_B))
    nonzero = {rater: {g: {c: n for c, n in counts.items() if n} for g, counts in by_group.items()}
               for rater, by_group in s["categories"].items()}
    assert nonzero == {
        "A": {"false_alarm": {"clear parasite": 1, "faint edge dot": 1, "platelet-like inclusion": 1},
              "miss": {"nothing visible": 2, "blur or colour cast": 1, "faint edge dot": 1},
              "correct_parasitized": {"clear parasite": 2},
              "correct_uninfected": {"nothing visible": 2, "segmentation problem": 1}},
        "B": {"false_alarm": {"clear parasite": 1, "nothing visible": 1, "cannot tell": 1},
              "miss": {"nothing visible": 2, "cannot tell": 1, "clear parasite": 1},
              "correct_parasitized": {"clear parasite": 1, "missing": 1},
              "correct_uninfected": {"stain precipitate or debris": 1, "nothing visible": 1, "faint edge dot": 1}}}
    assert s["categories"]["A"]["miss"]["cannot tell"] == 0  # every category is listed, zeros too
    assert s["missing"] == {"A": {"parasite_visible": 0, "category": 0},
                            "B": {"parasite_visible": 2, "category": 1}}


# --------------------------------------------------------------------------- agreement on parasite_visible
# Hand-computed: the raters agree on 7 of 10 cells; each answered yes / no / unsure 4 / 4 / 2 times, so chance
# agreement is .4 * .4 + .4 * .4 + .2 * .2 = .36, and kappa = (.70 - .36) / (1 - .36) = 0.53125.
HAND_A = ["yes", "yes", "yes", "yes", "no", "no", "no", "no", "unsure", "unsure"]
HAND_B = ["yes", "yes", "yes", "no", "no", "no", "no", "unsure", "unsure", "yes"]


def test_kappa_and_raw_agreement_match_a_hand_computed_example():
    s = ts.score(KEY[KEY.id <= 10], visible_only(HAND_A), visible_only(HAND_B))
    assert s["parasite_visible"] == pytest.approx({"kappa": 0.53125, "percent_agreement": 70.0,
                                                   "n_both_answered": 10})


def test_blank_answers_are_counted_as_missing_and_left_out_of_kappa():
    s = ts.score(KEY, visible_only(HAND_A + [None, "no"]), visible_only(HAND_B + ["yes", None]))
    assert s["parasite_visible"] == pytest.approx({"kappa": 0.53125, "percent_agreement": 70.0,
                                                   "n_both_answered": 10})
    assert [s["missing"][rater]["parasite_visible"] for rater in "AB"] == [1, 1]


@pytest.mark.filterwarnings("error::RuntimeWarning")  # undefined means not computed: no 0 / 0 and its warning
@pytest.mark.parametrize("a, b, expected", [
    # one identical answer throughout: chance agreement is 1, so kappa would be 0 / 0
    (["no"] * 4, ["no"] * 4, {"kappa": None, "percent_agreement": 100.0, "n_both_answered": 4}),
    # no cell answered by both: nothing to compare
    ([None, "yes", None, "no"], ["no", None, "yes", None],
     {"kappa": None, "percent_agreement": None, "n_both_answered": 0})])
def test_kappa_is_none_when_it_is_undefined(a, b, expected):
    s = ts.score(KEY[KEY.id <= 4], visible_only(a), visible_only(b))
    assert s["parasite_visible"] == expected
    json.dumps(s, allow_nan=False)  # still valid JSON


# --------------------------------------------------------------------------- sheets that do not fit
@pytest.mark.parametrize("ids, offending", [([1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12], 7),           # 7 missing
                                            ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11, 12], 11),   # 11 twice
                                            ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 13)])  # not in the key
def test_score_refuses_a_sheet_whose_ids_are_not_exactly_the_keys(ids, offending):
    sheet = frame([[i, "yes", "clear parasite", None] for i in ids])
    with pytest.raises(ValueError, match=rf"\b{offending}\b"):
        ts.score(KEY, frame(ROWS_A), sheet)


@pytest.mark.parametrize("column, value", [("parasite_visible", "maybe"), ("category", "clear parasites")])
def test_read_sheet_refuses_an_answer_outside_the_rubric_naming_its_id_and_value(tmp_path, column, value):
    rows = [[6, "yes", "clear parasite", None], [7, "no", "nothing visible", None]]
    rows[1][COLUMNS.index(column)] = value
    write_csv(tmp_path / "sheet.csv", rows)
    with pytest.raises(ValueError) as refusal:
        ts.read_sheet(str(tmp_path / "sheet.csv"))
    assert value in str(refusal.value) and re.search(r"\b7\b", str(refusal.value))


def test_read_sheet_refuses_an_id_that_is_not_a_whole_number(tmp_path):
    write_csv(tmp_path / "sheet.csv", [[1, "yes", "clear parasite", None], ["2b", "no", "nothing visible", None]])
    with pytest.raises(ValueError, match="2b"):
        ts.read_sheet(str(tmp_path / "sheet.csv"))


# --------------------------------------------------------------------------- reading sheets
TYPED = [[1, " Yes", "Clear parasite ", "purple ring"],  # stray spaces and capitals, as a rater might type them
         [2, "no", "NOTHING VISIBLE", None],
         [3, None, None, None]]                          # left blank


@pytest.mark.parametrize("suffix, write", [(".xlsx", write_xlsx), (".csv", write_csv)])
def test_read_sheet_returns_each_ids_answers_normalised_with_blanks_as_none(tmp_path, suffix, write):
    write(tmp_path / f"sheet{suffix}", TYPED)
    sheet = ts.read_sheet(str(tmp_path / f"sheet{suffix}"))
    assert list(sheet.columns) == COLUMNS
    assert sheet.values.tolist() == [[1, "yes", "clear parasite", "purple ring"],
                                     [2, "no", "nothing visible", None],
                                     [3, None, None, None]]


# --------------------------------------------------------------------------- command line
def test_main_writes_json_and_markdown_and_prints_the_markdown(tmp_path):
    key, a, b = tmp_path / "key.csv", tmp_path / "Triage_Sheet_A.xlsx", tmp_path / "Triage_Sheet_B.csv"
    KEY.to_csv(key, index=False)
    write_xlsx(a, ROWS_A)
    write_csv(b, ROWS_B)
    r = subprocess.run([sys.executable, SCRIPT, "--sheets", str(a), str(b), "--key", str(key),
                        "--out", str(tmp_path / "scores")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    scores = json.loads((tmp_path / "scores.json").read_text())
    md = (tmp_path / "scores.md").read_text()
    assert r.stdout == md
    assert scores["sheets"] == {"A": "Triage_Sheet_A.xlsx", "B": "Triage_Sheet_B.csv"}
    # 10 cells answered by both, 8 agree; yes / no / unsure 5 / 4 / 1 times (A) and 4 / 4 / 2 times (B), so chance
    # agreement is .38, and kappa = (.8 - .38) / (1 - .38) = 21 / 31 = 0.677
    assert scores["parasite_visible"] == pytest.approx({"kappa": 21 / 31, "percent_agreement": 80.0,
                                                        "n_both_answered": 10})
    assert "0.677" in md

    def numbers(group):  # n, both yes, both no and rest, from the group's row of the markdown table
        line = next(line for line in md.splitlines() if line.startswith(f"| {group} |"))
        return [int(x) for x in re.findall(r"\b\d+\b", line)]
    assert [numbers(g) for g in ["False alarm", "Miss", "Correct parasitized", "Correct uninfected"]] == [
        [3, 1, 0, 2], [4, 1, 2, 1], [2, 1, 0, 1], [3, 1, 1, 1]]
    assert "cell_" not in md + json.dumps(scores)  # counts only: no cell's file name reaches the report
