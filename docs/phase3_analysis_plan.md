# Phase 3 analysis plan: hypotheses H1 and H2 (experiments A1–A3)

Fixed on 2 November 2026, **before any A1–A3 model was trained**, and committed to the repository before the runs so
the timestamp shows the analysis was not chosen after seeing the results.

## What we test

The hypotheses are the ones on slides 28–29 of the Phase 2 deck:

- **H1 (validation).** Split by patient instead of by image, model unchanged. *Expect:* accuracy and MCC fall below the
  image-split baseline, and fold-to-fold spread widens. *Because:* cells from one patient share stain, lighting and the
  patient's blood, so a random image split lets the model recognise the patient instead of the parasite.
- **H2 (preprocessing).** RGB → YUV → histogram-equalise Y → RGB before EfficientNet-B0 (Umer *et al.* 2020), with the
  patient split kept. *Expect:* higher recall and MCC than H1 on unseen patients, and little change on the random split.
- **Falsification (as stated in the deck):**
  - If H2's gain over H1 is smaller than the fold-to-fold SD, we reject H2.
  - If grouped and random splits score the same, H1 is rejected.

| ID | Split | Preprocessing | Answers |
|---|---|---|---|
| A0 | image (paper) | none | baseline, Phase 2 (done) |
| A1 | patient | none | H1: A1 vs A0 |
| A2 | patient | YUV + hist-eq | H2: A2 vs A1 |
| A3 | image (paper) | YUV + hist-eq | control: A3 vs A0 |

Everything except the switch is A0's recipe, unchanged:
- the model and its weights;
- the loss, optimiser, LR schedule, 33 epochs and batch 16;
- the augmentation;
- the per-fold seeds;
- the 10-model averaging ensemble.

## Design decisions

1. **Patient key.** The file name's leading C-number (`C33P1thinF_...` → C33). It matches NIH's
   `patientid_cellmapping_{parasitized,uninfected}.csv` for all 27,558 cells: 200 patients, 150 infected and 50 healthy.
   NIH lists patient C47/P8 under two keys (two microscopes); the C-number merges them. Checked by
   `src/make_ablation_splits.py`.
2. **Patient split.**
   - `StratifiedGroupKFold(5, shuffle=True, random_state=1234)` gives five candidate hold-out sets.
   - We take the one closest to 20 % of the cells and 50 % parasitized, scored by |n/N − 0.2| + |p − 0.5|. This rule uses labels only.
   - Result: **5,550 cells from 40 patients (28 infected), 50.7 % parasitized**.
   - The remaining 160 patients are split by `StratifiedGroupKFold(10, shuffle=True, random_state=50)` into folds of 15–17 patients.
   - The split is committed as `results/A1_slide_split/split.csv` (fingerprint `ff94f8c3b200e708`); A2 uses the identical file.
3. **Image split.** A3 uses A0's split exactly (fingerprint `a0cc112e4a820ffb`, rebuilt and checked), so A3 vs A0 compares the same cells, fold by fold.
4. **YUV preprocessing.**
   - OpenCV at each image's native size: `COLOR_BGR2YUV`, then `equalizeHist` on Y only, then `COLOR_YUV2BGR`.
   - After that, A0's nearest-neighbour resize to 224 and the paper's augmentation run unchanged.
   - Deviations from Umer *et al.*: no 120 × 120 resize and no edge kernel (the paper does not specify the kernel).

## Analysis

- **Unit of independence: the patient.** All intervals come from a patient-cluster bootstrap, which resamples whole patients, with 10,000 resamples.
- **Primary protocol: clean (un-augmented) evaluation.** The paper's augmented protocol, used for A0's headline numbers, is reported alongside.
- **Primary metric: MCC.** Also reported: accuracy, recall (parasitized), specificity, balanced accuracy, F2 and ROC-AUC.
- **Paired contrasts** (A2 vs A1, A3 vs A0; the same cells in both arms):
  - Nadeau–Bengio corrected resampled t-test on the 10 per-fold differences;
  - paired patient bootstrap of the 10-model ensemble's hold-out difference.
- **A1 vs A0** (different hold-out sets): independent patient bootstraps per arm. The fold-level Welch test is descriptive only.
- **Multiple comparisons:** Holm correction over the three contrasts, per metric and level.
- **Decision rules:**
  - **H1** is supported if A1's ensemble MCC is lower than A0's, with the 95 % CI of the difference excluding 0
    (Holm p < 0.05). Wider fold SD is the secondary prediction.
  - **H2** is rejected, by the deck's rule, if A2's mean fold-MCC gain over A1 is smaller than A1's fold-MCC SD.
    The corrected t-test and the paired bootstrap are reported with it. If the rule and the tests disagree, H2 is called inconclusive.
  - **Control:** "little change" if |A3 − A0| in mean fold MCC is below A0's fold-MCC SD.
- **Extras on the same predictions** (no extra training):
  - errors per patient;
  - calibration (expected calibration error);
  - a recall-first threshold, chosen on the pooled out-of-fold CV predictions (max F2) and then applied to the hold-out set.

Code: `src/ablation_stats.py` (tests in `tests/test_ablation_stats.py`) and `notebooks/Phase3_Ablation_A1_A3.ipynb`.

## Known limitations

- Single-cell classification, not patient diagnosis: 75 % of the uninfected cells come from infected patients' smears.
- One patient hold-out of 40 patients; a different draw would move the numbers.
- Labels come from one expert; about 5 % of cells were questioned by Fuhad *et al.* (2020).
- All data comes from one hospital, so site effects are not tested; there is no external test set.
- One training run per fold and arm.
