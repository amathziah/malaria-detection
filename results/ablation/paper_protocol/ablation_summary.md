# Ablation A0–A3: results and hypothesis tests

Primary protocol: **paper** evaluation. Intervals: 95 % patient-cluster bootstrap (10,000 resamples). Metrics in %; MCC × 100.

## Experiments

| ID | Split | Preproc. | Hold-out cells / patients | Fold MCC (mean ± SD) | Fold acc. (mean ± SD) | Ens. acc. [95 % CI] | Ens. MCC [95 % CI] | Ens. recall [95 % CI] | Ens. AUC | Missed / flagged | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | image | none | 5,512 / 200 | 95.11 ± 0.60 | 97.55 ± 0.30 | 97.62 [97.01, 98.14] | 95.25 [94.01, 96.28] | 97.07 [95.91, 97.96] | 99.73 | 80 / 51 | 0.058 |
| A1 | patient | none | 5,550 / 40 | 93.67 ± 2.04 | 97.12 ± 0.92 | 98.40 [97.85, 98.86] | 96.80 [95.52, 97.70] | 98.05 [96.80, 98.82] | 99.80 | 55 / 34 | 0.068 |
| A2 | patient | yuv | 5,550 / 40 | 92.85 ± 1.62 | 96.74 ± 0.75 | 98.31 [97.63, 98.89] | 96.61 [95.09, 97.76] | 98.15 [96.87, 99.00] | 99.77 | 52 / 42 | 0.064 |
| A3 | image | yuv | 5,512 / 200 | 95.00 ± 0.40 | 97.50 ± 0.20 | 97.66 [97.06, 98.16] | 95.32 [94.12, 96.30] | 97.11 [95.94, 97.99] | 99.69 | 79 / 50 | 0.057 |

## Contrasts (difference = new − reference, in pp)

Fold level: Nadeau–Bengio corrected resampled t-test when the folds are paired; Welch t-test (descriptive) when they are not. Ensemble level: patient bootstrap. Holm correction over the three contrasts, per metric.

### A1 vs A0: H1: patient-level split vs the paper's image split (leakage)

| Metric | Fold Δ | Fold p | Fold p (Holm) | Ensemble Δ [95 % CI] | Ensemble p | Ensemble p (Holm) |
|---|---|---|---|---|---|---|
| mcc | -1.44 | 0.0572 | 0.172 | +1.54 [-0.12, +3.04] | 0.0682 | 0.205 |
| accuracy | -0.43 | 0.187 | 0.373 | +0.77 [+0.01, +1.53] | 0.0476 | 0.143 |
| recall | -0.93 | 0.0991 | 0.255 | +0.98 [-0.55, +2.35] | 0.198 | 0.594 |
| specificity | -0.34 | 0.348 | 1 | +0.59 [-0.21, +1.36] | 0.142 | 0.425 |
| balanced_accuracy | -0.63 | 0.0787 | 0.236 | +0.78 [-0.08, +1.55] | 0.0752 | 0.226 |
| f2 | -0.93 | 0.0774 | 0.202 | +0.92 [-0.47, +2.07] | 0.172 | 0.517 |
| auc | -0.24 | 0.0544 | 0.0957 | +0.08 [-0.12, +0.26] | 0.416 | 0.518 |

### A2 vs A1: H2: YUV stain normalisation on unseen patients

| Metric | Fold Δ | Fold p | Fold p (Holm) | Ensemble Δ [95 % CI] | Ensemble p | Ensemble p (Holm) |
|---|---|---|---|---|---|---|
| mcc | -0.82 | 0.0881 | 0.176 | -0.18 [-0.90, +0.42] | 0.618 | 1 |
| accuracy | -0.38 | 0.0852 | 0.256 | -0.09 [-0.44, +0.20] | 0.665 | 1 |
| recall | -0.43 | 0.085 | 0.255 | +0.11 [-0.19, +0.42] | 0.517 | 1 |
| specificity | -0.25 | 0.425 | 1 | -0.29 [-1.02, +0.22] | 0.427 | 0.854 |
| balanced_accuracy | -0.34 | 0.134 | 0.268 | -0.09 [-0.45, +0.21] | 0.632 | 1 |
| f2 | -0.44 | 0.0673 | 0.202 | +0.03 [-0.24, +0.29] | 0.781 | 1 |
| auc | -0.14 | 0.0478 | 0.0957 | -0.04 [-0.11, +0.03] | 0.259 | 0.518 |

### A3 vs A0: Control: YUV stain normalisation when patients are shared

| Metric | Fold Δ | Fold p | Fold p (Holm) | Ensemble Δ [95 % CI] | Ensemble p | Ensemble p (Holm) |
|---|---|---|---|---|---|---|
| mcc | -0.11 | 0.68 | 0.68 | +0.07 [-0.44, +0.59] | 0.79 | 1 |
| accuracy | -0.05 | 0.681 | 0.681 | +0.04 [-0.22, +0.29] | 0.84 | 1 |
| recall | +0.02 | 0.947 | 0.947 | +0.04 [-0.34, +0.42] | 0.917 | 1 |
| specificity | -0.13 | 0.538 | 1 | +0.04 [-0.33, +0.40] | 0.929 | 0.929 |
| balanced_accuracy | -0.05 | 0.68 | 0.68 | +0.04 [-0.22, +0.30] | 0.785 | 1 |
| f2 | -0.01 | 0.962 | 0.962 | +0.04 [-0.28, +0.35] | 0.815 | 1 |
| auc | -0.16 | 0.024 | 0.0719 | -0.03 [-0.07, +0.00] | 0.0634 | 0.19 |

## Verdicts

- **H1 (leakage)**: ensemble MCC 95.25 → 96.80 (Δ +1.54 pp, 95 % CI -0.12 to +3.04, Holm p = 0.205); accuracy Δ +0.77 pp. Fold SD of accuracy 0.30 → 0.92 pp. **Not supported** at the 5 % level: the patient-level split does not score clearly lower.
- **H2 (YUV on unseen patients)**: mean fold MCC gain -0.82 pp vs A1's fold SD 2.04 pp → pre-registered rule: **reject H2**. Ensemble MCC Δ -0.18 pp (95 % CI -0.90 to +0.42, Holm p = 1); recall Δ +0.11 pp; fold t-test p = 0.0881. H2 is not supported.
- **Control (YUV, shared patients)**: mean fold MCC Δ -0.11 pp (A0 fold SD 0.60 pp); ensemble MCC Δ +0.07 pp (95 % CI -0.44 to +0.59). As expected, YUV changes little when patients are shared.

## Extras on the same predictions

| ID | CV-chosen threshold (max F2) | Hold-out recall at it | Specificity at it |
|---|---|---|---|
| A0 | 0.166 | 99.16 | 93.96 |
| A1 | 0.192 | 99.15 | 93.42 |
| A2 | 0.189 | 99.08 | 93.42 |
| A3 | 0.172 | 99.16 | 93.85 |
