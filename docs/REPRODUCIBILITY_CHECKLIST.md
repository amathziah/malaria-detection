# Reproducibility checklist: Marques et al. (2022)

**Base paper:** G. Marques, A. Ferreras, I. de la Torre-Díez, *An ensemble-based approach for automated medical
diagnosis of malaria using EfficientNet*, Multimedia Tools and Applications 81 (2022) 28061–28078,
doi:10.1007/s11042-022-12624-6.

**Why this paper.**

- It is a strong result: 98.29 % accuracy and ROC-AUC 99.76 % on the NIH Malaria cell images.
- It uses a standard architecture: an EfficientNet-B0 ten-fold ensemble.
- Its authors published their executed notebook as a supplementary file
  ([MOESM1](https://static-content.springer.com/esm/art%3A10.1007%2Fs11042-022-12624-6/MediaObjects/11042_2022_12624_MOESM1_ESM.pdf)),
  so the recipe can be rebuilt exactly.

## The checklist

| Item | In the paper? | What the paper gives | What we found and did |
|---|---|---|---|
| Dataset public | Yes | NIH Malaria Cell Images, 27,558 crops | Downloaded automatically. Patient IDs are read from the file names and checked against NIH's patient mapping (`src/make_ablation_splits.py`) |
| Code public | Yes | The authors' executed notebook | We follow the code, not the text, wherever they differ |
| Model size | Yes | Table 2: 4,223,934 parameters (4,181,918 trainable) | Matched exactly; a test checks it |
| Hardware and time | Yes | GTX 1050, 4 h 46 min per fold | RTX 4090, about 11 min per fold, with the same float32 maths |
| Hyperparameters | Partly | The text differs from the code in 8 places (table below) | We follow the code |
| Library versions | Partly | Only in the notebook (TensorFlow 2.3, `efficientnet` 1.1.1) | TensorFlow 2.15, the last Keras 2 release; the same `efficientnet` 1.1.1 and `albumentations` 0.5.2 (`src/runpod_requirements.txt`) |
| Metrics | Partly | Accuracy, precision, recall, F1, ROC-AUC | The text swaps the ensemble's precision and recall; Table 6's "accuracy" is (precision + recall) / 2. We recompute everything from the printed reports |
| Data split | No | Random 80/20, then 10 stratified folds, unseeded | The paper's split cannot be recovered. We sort the file list, seed the split, and store a fingerprint with every fold |
| Evaluation protocol | No | Not stated | The code scored randomly augmented test images. We report clean and augmented evaluation; they differ by at most 0.23 pp |
| Patient-level evaluation | No | Random image split only | Became our hypothesis H1 (A1: a patient-level split) |
| Trained models | No | Not released | All 40 of our models are public: releases `v1.0-a0-10fold` and `v2.0-ablation` |

## The code differs from the text

| Setting | Paper's text / our first guess | Authors' code (what we follow) |
|---|---|---|
| Weights | ImageNet | noisy-student, qubvel `efficientnet` 1.1.1 |
| Head | GAP → dropout → 1 sigmoid | GAP → 128 → 64 → 32 (dropout 0.3) → 2 softmax |
| Loss | binary cross-entropy | categorical cross-entropy, label smoothing 0.1 |
| Schedule | ≤ 15 epochs, early stopping | 33 epochs, LR halved on plateau, best checkpoint |
| Batch size | 128 | 16 (1,240 steps per epoch) |
| Hold-out | 10 % | 20 % = 5,512 images, never trained on |
| Augmentation | flips, 90° rotations | heavy `albumentations`: noise, blur, distortions, CLAHE… |
| Evaluation | clean images | augmented images (one generator for all) |

## Outcome

Every headline metric is within 1 percentage point of the paper:

- mean fold accuracy: 97.55 % against 97.56 %;
- ensemble accuracy: 97.62 % against 98.29 %;
- ROC-AUC: 99.73 % against 99.76 %.

32 automated tests (`tests/test_marques2022_exact.py`) check the rebuild against the paper's printed outputs:

- the parameter counts;
- the split and fold sizes;
- the augmentation pipeline, verbatim;
- the image loading, pixel for pixel;
- the loss, optimiser and callbacks;
- the classification reports.

Details are in the [report](report.md#3-paper-exact-10-fold-reproduction) and the
[paper](../Malaria_IEEE_Paper.pdf) (§IV-A, §V-A).
