# Phase 3b: exploratory analyses (docs/phase3b_addendum.md)

Saved predictions only; clean protocol; 95 % intervals resample whole patients unless stated. Differences are new − reference in percentage points (pp); MCC × 100. Exploratory: fixed in the addendum before running, after the A1–A3 results were known.

## E1 · Equivalence (±1 pp MCC) and minimum detectable effects

| Contrast | Level | Metric | Δ | 90 % CI | Equivalent at ±1 pp? | TOST p | Smallest margin passed | MDE (80 % power) |
|---|---|---|---|---|---|---|---|---|
| A2 vs A1 | ensemble | mcc | -0.26 | [-0.73, +0.16] | yes | 0.0081 | 0.73 | 0.77 |
| A2 vs A1 | fold | mcc | -0.60 | [-1.27, +0.06] | no | 0.153 | 1.27 | 1.15 |
| A2 vs A1 | ensemble | accuracy | -0.13 | [-0.36, +0.08] | yes | 0.0001 | 0.36 | 0.37 |
| A2 vs A1 | fold | accuracy | -0.28 | [-0.60, +0.03] | yes | 0.00127 | 0.60 | 0.55 |
| A3 vs A0 | ensemble | mcc | +0.00 | [-0.44, +0.44] | yes | 0.0002 | 0.44 | 0.76 |
| A3 vs A0 | fold | mcc | -0.37 | [-0.77, +0.03] | yes | 0.00925 | 0.77 | 0.69 |
| A3 vs A0 | ensemble | accuracy | +0.00 | [-0.22, +0.22] | yes | 0.0001 | 0.22 | 0.38 |
| A3 vs A0 | fold | accuracy | -0.19 | [-0.39, +0.01] | yes | 1.87e-05 | 0.39 | 0.34 |
| A1 vs A0 | ensemble (different cells) | mcc | +1.62 | – | – | – | – | 2.21 |
| A1 vs A0 | fold (corrected, unpaired) | mcc | -1.65 | – | – | – | – | 2.28 |
| A1 vs A0 | ensemble (different cells) | accuracy | +0.81 | – | – | – | – | 1.08 |
| A1 vs A0 | fold (corrected, unpaired) | accuracy | -0.54 | – | – | – | – | 1.02 |

Design effect of patient clustering on A1's hold-out set: MCC 2.6, accuracy 2.3 (variance under the patient bootstrap ÷ under a cell bootstrap).

## E2 · Leakage on identical cells (A1 − A0; H1 predicts negative)

| Cells | n cells / patients | Metric | Δ [95 % CI] | p | 90 % CI | MDE | Reading |
|---|---|---|---|---|---|---|---|
| A0 hold-out cells of A1's held-out patients (ensembles) | 1,095 / 40 | mcc | +0.00 [-0.90, +0.98] | 1 | [-0.76, +0.79] | 1.32 | equivalent within ±1 pp |
| A0 hold-out cells of A1's held-out patients (ensembles) | 1,095 / 40 | accuracy | +0.00 [-0.44, +0.47] | 1 | [-0.37, +0.39] | 0.64 |  |
| A0 hold-out cells of A1's held-out patients (ensembles) | 1,095 / 40 | recall | +0.00 [-0.51, +0.69] | 1 | [-0.42, +0.55] | 0.85 |  |
| A0 hold-out cells of A1's held-out patients (ensembles) | 1,095 / 40 | specificity | +0.00 [-0.71, +0.71] | 1 | [-0.54, +0.54] | 0.98 |  |
| out-of-fold cells shared by both CVs (single models) | 17,591 / 160 | mcc | -0.85 [-2.02, -0.05] | 0.0304 | [-1.80, -0.13] | 1.45 | leakage detected |
| out-of-fold cells shared by both CVs (single models) | 17,591 / 160 | accuracy | -0.43 [-1.02, -0.03] | 0.0316 | [-0.91, -0.06] | 0.73 |  |
| out-of-fold cells shared by both CVs (single models) | 17,591 / 160 | recall | -0.75 [-1.94, -0.01] | 0.0454 | [-1.71, -0.07] | 1.45 |  |
| out-of-fold cells shared by both CVs (single models) | 17,591 / 160 | specificity | -0.10 [-0.35, +0.15] | 0.445 | [-0.31, +0.10] | 0.35 |  |

For comparison: the pre-registered hold-out comparison (different cells) gives MCC +1.62 [+0.01, +3.12]; the cross-validation folds give -1.65 [-3.28, -0.02].

## E3 · Patient-level diagnosis (A1)

**Disclosure.** NIH kept about 68 uninfected crops per patient but curated the parasitized cells, so per-patient parasite counts are not natural parasitaemia; only 12 held-out patients are healthy; there are no parasite densities. This is exploratory aggregation on curated crops, not a diagnostic accuracy study.

Rule chosen on the 160 CV patients' out-of-fold predictions (122 infected, 38 healthy): **positive if at least 3 cells have P(parasitized) ≥ 0.800** (CV sensitivity 96.7 %, specificity 100.0 %).

| Evaluation | Sensitivity | Specificity |
|---|---|---|
| CV patients, rule chosen on them (optimistic) | 96.7 % | 100.0 % |
| CV patients, nested (rule chosen on the other 9 folds) | 118/122 = 96.7 % | 37/38 = 97.4 % |
| **40 held-out patients, A1 ensemble, applied once** | **26/28 = 92.9 %** [76.5, 99.1] | **12/12 = 100.0 %** [73.5, 100.0] |

Exact 95 % CIs (Clopper–Pearson). Misclassified held-out patients: C53, C73. With each A1 fold model alone: sensitivity 92.9–96.4 %, specificity 100.0–100.0 %. Nested rules per fold: (t 0.80, τ 3), (t 0.80, τ 3), (t 0.80, τ 3), (t 0.80, τ 3), (t 0.80, τ 3), (t 0.80, τ 3), (t 0.50, τ 3), (t 0.80, τ 3), (t 0.80, τ 3), (t 0.80, τ 3).

Dilution stress test (each infected held-out patient keeps only m parasitized cells): m = 1: sensitivity 3.6 %, m = 2: sensitivity 12.3 %, m = 3: sensitivity 74.9 %, m = 5: sensitivity 90.0 %.

## E4 · Error audit (A1)

| Data | False alarms in infected patients' smears | In healthy patients' smears | Difference [95 % CI] |
|---|---|---|---|
| holdout | 30/1913 = 1.57 % (28 patients) | 1/822 = 0.12 % (12 patients) | +1.45 [+0.82, +2.14] |
| oof | 199/8451 = 2.35 % (122 patients) | 22/2593 = 0.85 % (38 patients) | +1.51 [+0.89, +2.11] |

Error clustering by patient (χ² dispersion, permutation within label): holdout: 86 errors over 40 patients, χ² = 111.2, p = 0.0001; oof: 619 errors over 160 patients, χ² = 578.7, p = 0.0001.

Candidate label errors (confident learning; candidates, not confirmed errors): holdout: 8 of 5,550 cells (7 labelled parasitized, 1 labelled uninfected; 8 of them among the model's 86 errors); oof: 134 of 22,008 cells (101 labelled parasitized, 33 labelled uninfected; 134 of them among the model's 619 errors).

| Contrast | Cells | n | MCC Δ [95 % CI] |
|---|---|---|---|
| A2 vs A1 | all cells | 5,550 | -0.26 [-0.85, +0.23] |
| A2 vs A1 | without flagged cells | 5,535 | -0.25 [-0.85, +0.23] |
| A3 vs A0 | all cells | 5,512 | +0.00 [-0.52, +0.53] |
| A3 vs A0 | without flagged cells | 5,490 | +0.04 [-0.48, +0.57] |

A1 hold-out ensemble ECE: 0.065 (reliability diagram: phase3b_reliability.png).

Blinded gallery: 172 numbered cells (86 model errors, the rest correct cells with the same labels), phase3b_error_gallery.png. Triage it before opening phase3b_error_gallery_KEY.csv.
