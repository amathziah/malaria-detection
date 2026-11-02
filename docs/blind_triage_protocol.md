# Blind triage of the A1 errors: protocol and scoring plan

The A1 ensemble gets 86 of the 5,550 held-out cells wrong: 55 missed parasites and 31 false alarms
([Phase 3b, E4](phase3b_addendum.md)). Each error could be:

- a labelling mistake;
- an ambiguous cell;
- a real mistake by the model.

**Purpose.** Two of us sort these errors without knowing which cells they are. That turns "possible label noise" into
our own evidence.

This protocol and its scoring plan were first committed on 2 November 2026 (commit `e2ce09a`), before anyone rated a
cell. The plan below is unchanged since then.

## Materials

| File | What it is |
|---|---|
| [`results/phase3b/phase3b_triage_pages.pdf`](../results/phase3b/phase3b_triage_pages.pdf) | The 172 cells at full resolution, 24 per A4 page, numbers only (`src/triage_kit.py`) |
| [`results/phase3b/phase3b_error_gallery_triage_sheet.csv`](../results/phase3b/phase3b_error_gallery_triage_sheet.csv) | The answer sheet: `id, parasite_visible, category, notes` (an Excel version with drop-downs is shared in the team) |
| `results/phase3b/phase3b_error_gallery_KEY.csv` | Labels and model calls. **Do not open until both sheets are in** |

**What the gallery contains.**

- All 86 errors, mixed with 86 correctly classified cells.
- The cells are shuffled and numbered 1–172, so nobody can tell from the pictures which are which.

## How to rate

**Who.**

- Two team members rate.
- A third member, who does not rate, opens the key and runs the scoring.

**For each number from 1 to 172:**

1. Choose **parasite_visible**: yes, no or unsure.
2. Choose one **category** from the rubric below.
3. Add notes if you want; they are optional.

**Rules.**

- Work alone, and don't discuss any cell with the other rater until both sheets are in.
- Zoom in as much as you like, but judge only what you see. "Unsure" and "cannot tell" are fine answers.

| Category | What it looks like |
|---|---|
| clear parasite | A distinct purple ring, dot-with-ring or larger purple body inside the cell |
| faint edge dot | A small, faint purple dot on the cell's edge: could be an early ring or debris |
| stain precipitate or debris | Dark specks or crystals, sharper than parasite material, often also outside the cell |
| platelet-like inclusion | A small purple granular body on or beside the cell (platelets are not inside red cells) |
| segmentation problem | The crop cuts the cell off or contains parts of other cells |
| blur or colour cast | Out of focus or oddly coloured, so the inside is hard to judge |
| nothing visible | A clean cell with no purple structure |
| cannot tell | You can't decide what you see |

## Scoring plan (fixed before rating)

Once both sheets are in, the key is opened and `src/triage_score.py` reports:

1. **Agreement** between the two raters on parasite_visible (Cohen's κ).
2. **Of the 31 false alarms** (labelled uninfected, called parasitized), how many both raters marked "yes". These are
   candidates for parasites missed in the labels.
3. **Of the 55 missed cells** (labelled parasitized, called uninfected), how many both raters marked "no". These are
   candidates for wrong labels or for parasites too faint to see.
4. **The same counts for the 86 correctly classified cells**, as a baseline for how often raters agree with the labels.
5. **The category counts in each group.**

```bash
python src/triage_score.py --sheets Triage_Sheet_RaterA.xlsx Triage_Sheet_RaterB.xlsx
# writes results/phase3b/phase3b_triage_scores.json and .md
```

**The labels are never changed.** Accuracy on the original labels stays the headline.

**Optional cross-check.** Michael Delves's relabelling of the NIH cells on IEEE DataPort sorts them into five folders:
parasitised, uninfected, "weird", "bad segmentation" and "unsure". Matching our 172 file names against those folders
would give an independent second opinion.

**Status (3 November 2026):** the materials and the scoring code are ready; the two ratings are pending.
