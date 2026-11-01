# Ablation A0–A3: results and hypothesis tests

Primary protocol: **clean** evaluation. Intervals: 95 % patient-cluster bootstrap (10,000 resamples). Metrics in %; MCC × 100.

## Experiments

| ID | Split | Preproc. | Hold-out cells / patients | Fold MCC (mean ± SD) | Fold acc. (mean ± SD) | Ens. acc. [95 % CI] | Ens. MCC [95 % CI] | Ens. recall [95 % CI] | Ens. AUC | Missed / flagged | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | image | none | 5,512 / 200 | 95.57 ± 0.60 | 97.78 ± 0.30 | 97.64 [97.02, 98.17] | 95.29 [94.03, 96.32] | 97.18 [96.03, 98.06] | 99.68 | 77 / 53 | 0.053 |
| A1 | patient | none | 5,550 / 40 | 93.92 ± 1.51 | 97.24 ± 0.66 | 98.45 [97.94, 98.91] | 96.90 [95.70, 97.79] | 98.05 [96.79, 98.85] | 99.80 | 55 / 31 | 0.065 |
| A2 | patient | yuv | 5,550 / 40 | 93.32 ± 1.66 | 96.96 ± 0.75 | 98.32 [97.71, 98.86] | 96.65 [95.23, 97.68] | 98.22 [97.02, 99.02] | 99.76 | 50 / 43 | 0.060 |
| A3 | image | yuv | 5,512 / 200 | 95.20 ± 0.37 | 97.60 ± 0.19 | 97.64 [97.02, 98.17] | 95.29 [94.04, 96.32] | 97.14 [95.94, 98.05] | 99.66 | 78 / 52 | 0.052 |

## Contrasts (difference = new − reference, in pp)

Fold level: Nadeau–Bengio corrected resampled t-test when the folds are paired; Welch t-test (descriptive) when they are not. Ensemble level: patient bootstrap. Holm correction over the three contrasts, per metric.

### A1 vs A0: H1: patient-level split vs the paper's image split (leakage)

| Metric | Fold Δ | Fold p | Fold p (Holm) | Ensemble Δ [95 % CI] | Ensemble p | Ensemble p (Holm) |
|---|---|---|---|---|---|---|
| mcc | -1.65 | 0.00752 | 0.0226 | +1.62 [+0.01, +3.12] | 0.0488 | 0.146 |
| accuracy | -0.54 | 0.0358 | 0.108 | +0.81 [+0.06, +1.57] | 0.034 | 0.102 |
| recall | -1.27 | 0.0174 | 0.0521 | +0.87 [-0.67, +2.25] | 0.249 | 0.748 |
| specificity | -0.26 | 0.342 | 0.687 | +0.77 [+0.00, +1.53] | 0.0484 | 0.118 |
| balanced_accuracy | -0.77 | 0.0074 | 0.0222 | +0.82 [-0.04, +1.59] | 0.0594 | 0.178 |
| f2 | -1.20 | 0.0169 | 0.0507 | +0.86 [-0.52, +2.02] | 0.19 | 0.571 |
| auc | -0.23 | 0.0398 | 0.12 | +0.12 [-0.10, +0.32] | 0.288 | 0.593 |

### A2 vs A1: H2: YUV stain normalisation on unseen patients

| Metric | Fold Δ | Fold p | Fold p (Holm) | Ensemble Δ [95 % CI] | Ensemble p | Ensemble p (Holm) |
|---|---|---|---|---|---|---|
| mcc | -0.60 | 0.132 | 0.246 | -0.26 [-0.85, +0.23] | 0.319 | 0.637 |
| accuracy | -0.28 | 0.137 | 0.243 | -0.13 [-0.41, +0.11] | 0.378 | 0.756 |
| recall | -0.20 | 0.304 | 0.609 | +0.18 [-0.11, +0.53] | 0.255 | 0.748 |
| specificity | -0.33 | 0.229 | 0.687 | -0.44 [-0.92, -0.04] | 0.0392 | 0.118 |
| balanced_accuracy | -0.26 | 0.149 | 0.243 | -0.13 [-0.41, +0.14] | 0.358 | 0.716 |
| f2 | -0.23 | 0.171 | 0.342 | +0.06 [-0.20, +0.33] | 0.609 | 1 |
| auc | -0.18 | 0.075 | 0.12 | -0.04 [-0.09, +0.02] | 0.198 | 0.593 |

### A3 vs A0: Control: YUV stain normalisation when patients are shared

| Metric | Fold Δ | Fold p | Fold p (Holm) | Ensemble Δ [95 % CI] | Ensemble p | Ensemble p (Holm) |
|---|---|---|---|---|---|---|
| mcc | -0.37 | 0.123 | 0.246 | +0.00 [-0.52, +0.53] | 1 | 1 |
| accuracy | -0.19 | 0.121 | 0.243 | +0.00 [-0.26, +0.27] | 1 | 1 |
| recall | -0.10 | 0.513 | 0.609 | -0.04 [-0.43, +0.33] | 0.935 | 0.935 |
| specificity | -0.27 | 0.313 | 0.687 | +0.04 [-0.36, +0.43] | 0.917 | 0.917 |
| balanced_accuracy | -0.19 | 0.122 | 0.243 | -0.00 [-0.27, +0.27] | 0.999 | 0.999 |
| f2 | -0.13 | 0.219 | 0.342 | -0.02 [-0.35, +0.28] | 0.889 | 1 |
| auc | -0.16 | 0.0599 | 0.12 | -0.02 [-0.11, +0.05] | 0.663 | 0.663 |

## Verdicts

- **H1 (leakage)**: ensemble MCC 95.29 → 96.90 (Δ +1.62 pp, 95 % CI +0.01 to +3.12, Holm p = 0.146); accuracy Δ +0.81 pp. Fold SD of accuracy 0.30 → 0.66 pp. **Not supported** at the 5 % level: the patient-level split does not score clearly lower.
- **H2 (YUV on unseen patients)**: mean fold MCC gain -0.60 pp vs A1's fold SD 1.51 pp → pre-registered rule: **reject H2**. Ensemble MCC Δ -0.26 pp (95 % CI -0.85 to +0.23, Holm p = 0.637); recall Δ +0.18 pp; fold t-test p = 0.132. H2 is not supported.
- **Control (YUV, shared patients)**: mean fold MCC Δ -0.37 pp (A0 fold SD 0.60 pp); ensemble MCC Δ +0.00 pp (95 % CI -0.52 to +0.53). As expected, YUV changes little when patients are shared.

## Extras on the same predictions

| ID | CV-chosen threshold (max F2) | Hold-out recall at it | Specificity at it |
|---|---|---|---|
| A0 | 0.192 | 98.72 | 95.22 |
| A1 | 0.189 | 99.22 | 93.93 |
| A2 | 0.143 | 99.22 | 91.74 |
| A3 | 0.159 | 98.75 | 94.14 |
