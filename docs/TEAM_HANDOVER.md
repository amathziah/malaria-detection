# Team handover: malaria cell detection, Phase 3 final

**From** C Murali Madhav · **to** J Amathziah, Ravi Yadav and Pugazhendhi J · 2 November 2026

The project is finished and everything is on GitHub:
[github.com/amathziah/malaria-detection](https://github.com/amathziah/malaria-detection). This note covers:

- what is in the team pack;
- what we found;
- how to present it and answer questions;
- the one task left for the team: a blind triage of our errors, about an hour each for two of you.

## 1. What's in the team pack

| File | What it is | Use it for |
|---|---|---|
| `00_Team_Handover.pdf` | This note | Start here |
| `01_Presentation/Malaria_Phase3_Final.pptx` | The final deck, 24 slides, speaker notes on every slide | Presenting (PowerPoint: View → Notes) |
| `01_Presentation/Malaria_Phase3_Final.pdf` | The same deck as a PDF | Reading on a phone |
| `02_Documents/IEEE_Paper.pdf` | The 8-page IEEE-format paper | The full method and every number |
| `02_Documents/Project_Report.pdf` | The project report | Method, results, deviations from the paper |
| `02_Documents/Project_Guide.pdf` | A 36-page plain-language guide with a glossary and a one-page cheat sheet | Preparing for questions |
| `03_Blind_Triage/Triage_Gallery_172_cells.pdf` | 172 numbered cell images, 24 per page | The triage (section 6) |
| `03_Blind_Triage/Triage_Sheet.xlsx` | The answer sheet: dropdowns, plus a Rubric tab | The triage (section 6) |

## 2. The project in one minute

- **The question.** Papers report 96–99.9 % accuracy at sorting single red-blood-cell images from the NIH malaria
  dataset (27,558 cells, 200 patients) into parasitized and uninfected.
  - Most of them split the images at random, so one patient's cells sit in both training and test.
  - Does that accuracy survive patients the model has never seen?
- **Phase 2: we reproduced the base paper** (Marques et al. 2022, an EfficientNet-B0 ten-fold ensemble) from its
  authors' own code.
  - Ensemble accuracy: **97.62 %** against their 98.29 %, with every metric within 1 pp.
  - We found two errors in the paper: its text swaps precision and recall, and its code scores augmented test images.
- **Phase 3: two hypotheses, fixed in advance and tested with 30 new models**, changing one thing at a time.
  - **H1, "patient leakage inflates the scores": not supported.**
    - Split by patient, the ensemble scores **98.45 %** on 40 unseen patients.
    - Measured on identical cells, leakage is real but small: **0.85 pp of MCC**.
  - **H2, "YUV stain normalisation helps on unseen patients": rejected.**
    - It changes MCC by **−0.26 pp**, which is within ±1 pp of zero.
- **Phase 3b: four further analyses** of the saved predictions, also fixed in advance:
  - how large the YUV effect could be;
  - leakage on identical cells;
  - a per-patient diagnosis rule, which found **26 of 28** infected and **12 of 12** healthy unseen patients;
  - an error audit: false alarms cluster on infected patients' smears.

## 3. Numbers to know

| What | Number | Slide |
|---|---|---|
| Dataset | 27,558 cells from 200 patients (150 infected, 50 healthy), half of the cells parasitized | 4 |
| Reproduction | 97.62 % ensemble accuracy (paper 98.29 %); fold models 97.55 % vs the paper's 97.56 % | 9 |
| Training speed | about 11 min per fold on one RTX 4090, against 4 h 46 min in the paper; Phase 3's 30 models cost $6.95 | 10 |
| Unseen patients (A1) | 98.45 % accuracy (95 % CI 97.94–98.91) on 40 held-out patients | 2, 16 |
| H1, the pre-registered test | ensemble MCC +1.62 pp (95 % CI +0.01 to +3.12, Holm p = 0.15): no drop | 16 |
| H1 in cross-validation | fold MCC −1.65 pp (95 % CI −3.28 to −0.02, Holm p = 0.14): small and fragile | 16 |
| Leakage on identical cells | −0.85 pp MCC (95 % CI −2.02 to −0.05) on 17,591 cells of 160 patients; 0.00 on the 1,095 cells of the 40 held-out patients | 17 |
| H2, YUV on unseen patients | MCC −0.26 pp (95 % CI −0.85 to +0.23); within ±1 pp (90 % CI −0.73 to +0.16) | 18 |
| Errors of the A1 ensemble | 86 of 5,550 held-out cells: 55 missed parasites and 31 false alarms. Half of them come from 7 of the 40 patients; 30 of the 31 false alarms are on infected patients' smears | 19 |
| Recall-first threshold | recall 98.05 % → 99.22 %, at 93.93 % specificity | 20 |
| Per-patient rule | positive if at least 3 cells have P ≥ 0.80: 26 of 28 infected (92.9 %) and 12 of 12 healthy | 21 |

## 4. Presenting the deck

This is a suggested four-way split; change it as you like. Every slide's speaker notes can serve as your script.

| Part | Slides | Story |
|---|---|---|
| 1 · Why it matters | 1–6 | Title, the answer up front, the problem, the data, the patient-leakage trap, what 11 published studies did |
| 2 · Reproducing the paper | 7–11 | The code differs from the text, the model, the result within 1 pp, ten GPUs in parallel, the Phase 3 divider |
| 3 · The experiment | 12–17 | The two hypotheses, the 2 × 2 design, the two switches, how we decide, H1, leakage on identical cells |
| 4 · Results and limits | 18–23 | H2, where the errors are, recall first, from cells to patients, honest limits, conclusion |

Leave slide 24 (references) up during questions. Two things to say the same way every time:

- H1 is **"not supported"** and H2 is **"rejected"**. These are different verdicts (question 4).
- The patient-level result is **exploratory**: always add "on curated cells, not a real smear".

## 5. Questions we're likely to get

1. **If there is leakage, why is accuracy on unseen patients higher (98.45 %) than with the paper's split (97.64 %)?**
   - The two numbers come from different test sets, and the 40 held-out patients happen to be an easy draw.
   - The same A1 fold models average 98.22 % on them but 97.24 % on the unseen patients of cross-validation.
   - Comparing two different test sets could only detect leakage of about 2.2 pp of MCC, so we also measured it on
     identical cells.
2. **So is there leakage or not?**
   - Yes, but it is small. We scored the same 17,591 cells with both kinds of model.
   - Models that had seen other cells of the same patient scored 0.85 pp of MCC higher (95 % CI 0.05–2.02).
     That is about half a point of accuracy.
   - On the 1,095 cells that both hold-out sets share, the two ensembles make the same number of errors: 22 each.
3. **Why did the cross-validation p-value change from 0.023 to 0.14?**
   - The plan's Welch t-test treated the ten folds as independent, but they are not. Any two fold models share 8 of
     their 9 training parts, so their scores vary less than independent runs would.
   - The Nadeau–Bengio correction accounts for that overlap. With it, the Holm-corrected p is 0.14.
   - We report both values and call the result a fragile trend, not a significant effect.
4. **Why is H1 "not supported" but H2 "rejected"?**
   - H1 had a rule for support: the ensemble had to score significantly lower on unseen patients. It didn't.
     That is not proof of zero leakage, and the identical-cell test finds a small amount.
   - H2 had a rule for rejection: its gain had to be smaller than the fold-to-fold spread. It was: −0.60 pp
     against a spread of 1.51 pp.
5. **Why didn't YUV normalisation help?**
   - It equalises brightness (the Y channel) only and leaves stain colour unchanged.
   - The training augmentation already varies brightness and contrast, and every image comes from one hospital, so
     little was left to fix.
   - An equivalence test puts the effect within ±1 pp of MCC.
6. **What is MCC, and why use it?**
   - The Matthews correlation coefficient: one number from all four cells of the confusion matrix, ranging from
     −1 to 1. We show it × 100.
   - It is high only when both classes are predicted well, which makes it stricter than accuracy.
   - We fixed it as the primary metric before training.
7. **Why resample patients rather than cells?**
   - A patient's cells share stain, lighting and blood, so they are not independent.
   - Resampling whole patients gives honest intervals. For MCC, the variance is 2.6 times what a per-cell bootstrap
     would claim.
8. **What does "pre-registered" mean here?**
   - Before training any of the 30 new models, we committed the hypotheses, primary metric, tests and decision rules
     to GitHub (`docs/phase3_analysis_plan.md`).
   - We did the same with the Phase 3b addendum before running those analyses.
   - The commit dates prove the order.
9. **Could this diagnose malaria in a clinic?**
   - Not yet. The patient-level rule is exploratory: NIH curated the cell crops, so it isn't accuracy on a real smear.
   - All the data come from one hospital, and we have no external test set. MP-IDB, from another lab, would be the
     next test.
10. **What was wrong with the base paper?**
    - Its text swaps the ensemble's precision and recall, and its code scores randomly augmented test images.
    - The code also differs from the text in eight places, such as the noisy-student weights and a 20 % hold-out.
    - We followed the code and documented every difference.
11. **Why are almost all the false alarms on infected patients' smears?**
    - 30 of the 31 are. Either the labeller missed some parasites, or those cells are genuinely ambiguous.
    - Another team set aside about 5 % of the NIH cells as mislabelled or suspicious.
    - We can't tell which explanation is right without an expert. The blind triage below is our own first check.
12. **How long did training take, and what did it cost?**
    - We used one RTX 4090 per fold on RunPod: about 11 minutes per fold, against 4 h 46 min in the paper.
    - Phase 3's 30 models took about an hour and cost $6.95.

## 6. Team task: blind triage of our errors

**Why.** The A1 ensemble got 86 of the 5,550 held-out cells wrong. Each error could be:

- a labelling mistake;
- an ambiguous cell;
- a real mistake by the model.

If two of us sort these errors without knowing which is which, "possible label noise" becomes our own evidence.

**What.** The gallery mixes the 86 errors with 86 cells the model got right. They are shuffled and numbered 1–172,
so nobody can tell from the pictures which are which. That is the point.

**Who.** Two raters, chosen from Amathziah, Ravi and Pugazhendhi; decide in the group. Madhav coordinates and keeps
the answer key.

**How (about an hour each):**

1. Open `Triage_Gallery_172_cells.pdf` and `Triage_Sheet.xlsx`, and write your name in the sheet.
2. For each number from 1 to 172, choose **parasite_visible** (yes, no or unsure) and a **category** from the
   dropdowns. Notes are optional.
3. Work alone. Don't discuss any cell with the other rater until both sheets are in.
4. Don't open the answer key. It is not in the pack; on GitHub it is
   `results/phase3b/phase3b_error_gallery_KEY.csv`.
5. Zoom in as much as you like. Judge only what you see: "unsure" and "cannot tell" are fine answers.
6. Save the sheet as `Triage_Sheet_<YourName>.xlsx` and send it to Madhav.

**Rubric** (also in the sheet's Rubric tab):

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

**What happens next (fixed now, before anyone rates).** Once both sheets are in, Madhav opens the key and reports:

- the agreement between the two raters on parasite_visible (Cohen's κ);
- of the 31 false alarms (labelled uninfected, called parasitized), how many both raters marked "yes". These are
  candidates for parasites missed in the labels.
- of the 55 missed cells (labelled parasitized, called uninfected), how many both raters marked "no". These are
  candidates for wrong labels or for parasites too faint to see.
- the same counts for the 86 correctly classified cells, as a baseline for how often raters agree with the labels;
- the category counts in each group.

The labels are never changed, and accuracy on the original labels stays the headline.

**Optional cross-check.** This needs someone with an IEEE account:

- Michael Delves's relabelling of the NIH cells on IEEE DataPort sorts them into five folders: parasitised,
  uninfected, "weird", "bad segmentation" and "unsure".
- After the triage, Madhav can match our 172 file names against those folders, which gives an independent second
  opinion.

## 7. Where everything is on GitHub

| What | Where |
|---|---|
| Overview and all results | `README.md` |
| Deck, pptx and PDF | `slides/` |
| Paper | `docs/ieee/main.pdf` |
| Report and plain-language guide | `docs/report.md`, `docs/PROJECT_GUIDE.pdf` |
| Pre-registered plan and the Phase 3b addendum | `docs/phase3_analysis_plan.md`, `docs/phase3b_addendum.md` |
| Result tables and figures | `results/ablation/`, `results/phase3b/` |
| Triage pages and a CSV answer sheet | `results/phase3b/phase3b_triage_pages.pdf`, `results/phase3b/phase3b_error_gallery_triage_sheet.csv` |
