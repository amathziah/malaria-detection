# Automated Malaria Cell Detection — Phase 2

Reproduction of Marques et al. (2022) — EfficientNet-B0 on the NIH malaria cell images — plus our hypothesis experiments on slide-level leakage (H1) and YUV stain normalisation (H2).

## Team

| Member | GitHub | Role |
|---|---|---|
| Amathziah J | [@amathziah](https://github.com/amathziah) | Kaggle runs, repo |
| Murali Madhav C | [@HackHeroic](https://github.com/HackHeroic) | Code (notebook, script) |
| Ravi Yadav | [@RAVIYADAV6522](https://github.com/RAVIYADAV6522) | Slides |
| Pugazhendhi J | [@pugazhjs9](https://github.com/pugazhjs9) | Report |

## Folder structure

```
malaria-detection/
├── README.md               this file
├── CONTRIBUTING.md         team roles + git workflow (read this first)
├── requirements.txt
├── notebooks/
│   ├── Phase2_Baseline_Reproduction_Marques2022.ipynb   ← source of truth (run on Kaggle)
│   ├── Phase2_Baseline_Reproduction_Marques2022_executed.ipynb   the actual Kaggle A0 run, with all outputs
│   └── Phase2_A0_Results.ipynb                           reproduced A0 results, with outputs
├── src/
│   ├── phase2_baseline_marques2022.py                    same code as a plain script
│   ├── check_results.py                                  one experiment vs. the paper
│   ├── compare_experiments.py                            A0–A3 side by side (H1/H2)
│   └── fill_slide_table.py                               results table on the slides
├── kaggle_run/
│   └── kernel-metadata.json                              owner only: Kaggle push config
├── results/
│   ├── A0_baseline/        paper reproduction (done)
│   ├── A1_slide_split/     H1  (to do)
│   ├── A2_yuv_slide/       H2  (to do)
│   └── A3_yuv_image/       control (to do)
├── docs/
│   └── report.md           report / write-up
├── slides/
│   ├── Malaria_Phase2_Baseline_Hypothesis.pptx           original
│   └── Malaria_Phase2_Baseline_Hypothesis_filled.pptx    slide 18 filled with A0 results
├── models/                 trained .keras files (git-ignored, 47 MB each)
└── archive/                failed v1 run, results zip (git-ignored)
```

## Experiments

| ID | Split | Preprocessing | Tests | Status |
|---|---|---|---|---|
| A0 | image-level (paper) | none | baseline reproduction | **done** |
| A1 | slide-grouped | none | H1: does accuracy drop once leakage is removed? | to do |
| A2 | slide-grouped | YUV + hist-eq | H2: does stain normalisation recover it? (vs A1) | to do |
| A3 | image-level | YUV + hist-eq | control: is the gain specific to unseen slides? (vs A0) | to do |

## A0 baseline result (Kaggle, 2× Tesla T4, 3 of 10 folds)

| Metric | Paper | Ours |
|---|---|---|
| Mean single-fold accuracy | 97.70 % | 97.38 ± 0.74 % |
| Ensemble accuracy | 98.29 % | 97.57 % |
| Recall | 98.82 % | 96.81 % |
| Precision | 97.74 % | 98.31 % |
| F1 | 98.28 % | 97.55 % |
| ROC-AUC | 99.76 % | 99.76 % |
| MCC | — | 0.95 |

Within 1 pp of the paper on both headline accuracies; recall is 2 pp lower. Two GPUs → global batch 128 (64 per GPU). Details: `results/A0_baseline/`.

To print the per-fold results and check them against the paper (no GPU needed):

    pip install -r requirements.txt                  # once: pandas + python-pptx
    python src/check_results.py                      # A0 baseline
    python src/check_results.py results/<experiment>
    python src/compare_experiments.py                # A0–A3 table + H1/H2 differences

**Executed Kaggle run:** [notebooks/Phase2_Baseline_Reproduction_Marques2022_executed.ipynb](notebooks/Phase2_Baseline_Reproduction_Marques2022_executed.ipynb) · **Results notebook:** [notebooks/Phase2_A0_Results.ipynb](notebooks/Phase2_A0_Results.ipynb) · **Full write-up:** [docs/report.md](docs/report.md) · **File guide:** [results/README.md](results/README.md) · **Team workflow:** [CONTRIBUTING.md](CONTRIBUTING.md) · **Team tasks:** [TEAM_TASKS.md](TEAM_TASKS.md)

## Running on Kaggle (repo owner only)

Teammates don't need Kaggle. They push code, then tell the owner what to run (see CONTRIBUTING.md).

```bash
cp notebooks/Phase2_Baseline_Reproduction_Marques2022.ipynb kaggle_run/
#   (turn on an A1–A3 flag in the kaggle_run/ copy only, if needed)
kaggle kernels push -p kaggle_run
kaggle kernels status akoshi/malaria-phase2-baseline
kaggle kernels output akoshi/malaria-phase2-baseline -p results/<experiment>
mv results/<experiment>/outputs/*.keras models/      # keep models out of git
```
