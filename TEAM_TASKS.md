# Malaria project: your tasks (Murali, Ravi, Pugal)

Each of you does your own tasks **on your own laptop, logged in to your own GitHub account**. Every task gives you a starting draft. **Read it, make sure you understand it, and change anything you'd say differently.** You're the one who has to explain it if asked.

---

## 0. One-time setup (about 10 minutes)

**Mac:** open Terminal. **Windows:** install [Git for Windows](https://git-scm.com) and [GitHub CLI](https://cli.github.com), then open **Git Bash**.

```bash
git config --global user.name  "Your Name"
git config --global user.email "the-email-on-your-github-account"
gh auth login            # GitHub.com → HTTPS → Login with a web browser → YOUR account
gh auth setup-git
gh repo clone amathziah/malaria-detection
cd malaria-detection
gh auth status           # must show YOUR username
```

Open the `malaria-detection` folder in VS Code.

## Every task: same 3 steps

```bash
./sync.sh                              # 1. get the latest (always first)
# 2. make the change described in your task
./sync.sh "the commit message given"   # 3. save + upload
```

If it says *"conflicting change"*, nothing is lost. Tell Amathziah.

---

## Doing your tasks with Claude (optional, recommended)

You can use **your own Claude Code** on your own laptop to do your 3 tasks. The work is split evenly: **3 commits each**, about the same size.

1. Install Claude Code: in VS Code, open Extensions and install **"Claude Code"** (or see https://docs.claude.com/en/docs/claude-code), then sign in with **your own** Claude account.
2. Open the `malaria-detection` folder in VS Code, open Claude Code, and paste the prompt for your name:

**Murali**
> I'm Murali. Read TEAM_TASKS.md, section "Murali: code". Do my 3 commits one at a time. For each one: explain what you'll change, make the change, run anything that needs testing (e.g. `python src/check_results.py`), show me the diff, and wait for my OK. Then I'll run `./sync.sh "<commit message>"` myself. Don't change CFG or any training settings.

**Ravi**
> I'm Ravi. Read TEAM_TASKS.md, section "Ravi: slides". Help me do my 3 commits one at a time on `slides/Malaria_Phase2_Baseline_Hypothesis_filled.pptx`. Use python-pptx where it can do the edit cleanly and tell me when something is easier to do by hand in PowerPoint. Show me what changed and wait for my OK before I run `./sync.sh "<commit message>"`.

**Pugal**
> I'm Pugal. Read TEAM_TASKS.md, section "Pugal: report". Help me write my 3 sections of `docs/report.md` one at a time, using the drafts as a starting point but in my own words. Check every number against `results/A0_baseline/`. Show me each section and wait for my OK before I run `./sync.sh "<commit message>"`.

**Rules when using Claude:**
- **You** review every change and run `./sync.sh` yourself. Don't let it commit for you.
- Make sure you understand what was changed, because you'll have to explain it.
- Stay in your own files (Murali: `notebooks/` `src/` + one README line, Ravi: `slides/`, Pugal: `docs/`).
- Before each task, run `./sync.sh` to get the latest.

---

## Murali: code (3 commits)

### Commit 1: team cell at the top of the notebook
1. Open `notebooks/Phase2_Baseline_Reproduction_Marques2022.ipynb` in VS Code.
2. Click above the first cell → **+ Markdown** → paste:

```markdown
**Team:** Amathziah J (Kaggle runs, repo) · Murali Madhav C (code) · Ravi Yadav (slides) · Pugazhendhi J (report)

**Course project, Phase 2:** reproduce Marques et al. (2022) as our baseline (A0), then test our hypotheses H1 (slide-level leakage) and H2 (YUV stain normalisation) with experiments A1–A3.
```

3. Open `src/phase2_baseline_marques2022.py` and paste the same text at the very top, with each line starting with `# `.
4. Save both, then: `./sync.sh "Add team and project overview to notebook and script"`

### Commit 2: results-check script
1. Create a new file `src/check_results.py` and paste:

```python
"""Print an experiment's results and check them against the paper.

Usage:
    python src/check_results.py                          # A0 baseline
    python src/check_results.py results/A1_slide_split   # any experiment folder
"""
import glob
import json
import os
import sys

import pandas as pd

TOLERANCE_PP = 1.0  # success criterion: within about 1 percentage point of the paper


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "results/A0_baseline"
    summary_path = os.path.join(folder, "A0_summary.json")
    if not os.path.exists(summary_path):
        sys.exit(f"No summary found in {folder}/ (run the notebook on Kaggle first).")
    s = json.load(open(summary_path))

    print(f"Experiment folder : {folder}")
    print(f"Images / slides   : {s['n_images']:,} / {s['n_slides']}")
    print(f"Folds run         : {s['folds_run']} of {s['config']['N_FOLDS']}\n")

    for f in glob.glob(os.path.join(folder, "*_per_fold_val.csv")):
        folds = pd.read_csv(f)
        print("Per-fold validation:")
        print(folds[["fold", "epochs", "minutes", "accuracy", "recall", "precision", "mcc"]].round(2).to_string(index=False))
        print()

    paper, mean, sd, ens = s["paper"], s["mean_fold"], s["sd_fold"], s["ensemble"]
    rows = [
        ("Mean fold accuracy", paper["mean_fold_accuracy"], mean["accuracy"]),
        ("Ensemble accuracy",  paper["accuracy"],           ens["accuracy"]),
        ("Recall",             paper["recall"],             ens["recall"]),
        ("Precision",          paper["precision"],          ens["precision"]),
        ("F1",                 paper["f1"],                 ens["f1"]),
        ("ROC-AUC",            paper["auc"],                ens["auc"]),
    ]
    print(f"{'Metric':20s} {'Paper':>8s} {'Ours':>8s} {'Δ pp':>7s}")
    for name, p, o in rows:
        flag = "" if abs(o - p) <= TOLERANCE_PP else "  ← more than 1 pp"
        print(f"{name:20s} {p:8.2f} {o:8.2f} {o - p:+7.2f}{flag}")
    print(f"{'MCC':20s} {'—':>8s} {ens['mcc'] / 100:8.2f}")
    print(f"\nMean fold accuracy SD: ±{sd['accuracy']:.2f}")

    ok = all(abs(o - p) <= TOLERANCE_PP for _, p, o in rows[:2])
    print("\nVerdict:", "✅ reproduction within 1 pp of the paper" if ok else "❌ more than 1 pp from the paper")


if __name__ == "__main__":
    main()
```

2. Test it: `pip install pandas` (if needed), then `python src/check_results.py`. It should end with **"✅ reproduction within 1 pp of the paper"**.
3. `./sync.sh "Add script to check experiment results against the paper"`

### Commit 3: document it in the README
1. In `README.md`, under the A0 results table, add:

```markdown
To print the per-fold results and check them against the paper:

    python src/check_results.py                 # A0 baseline
    python src/check_results.py results/<experiment>
```

2. `./sync.sh "README: how to check results"`

---

## Ravi: slides (3 commits)

Work in `slides/Malaria_Phase2_Baseline_Hypothesis_filled.pptx`. **Close PowerPoint before every `./sync.sh`.**

### Commit 1: team slide
1. In PowerPoint, right-click **slide 1** → **Duplicate**, so you keep the deck's style. Drag the copy to the position of your choice (e.g. right after slide 1 or at the end).
2. Replace the text with:

> **Our team**
> Amathziah J: Kaggle experiments, repository
> Murali Madhav C: code (notebook, scripts)
> Ravi Yadav: slides
> Pugazhendhi J: report

3. Save, close PowerPoint, then: `./sync.sh "Slides: add team slide"`

### Commit 2: results figures slide
1. Duplicate **slide 18** and place the copy right after it.
2. Delete the tables on the copy. Set the title to **"A0 results at a glance"**.
3. **Insert → Pictures** → `results/A0_baseline/A0_vs_paper.png` (left) and `results/A0_baseline/A0_curves_cm_roc.png` (right).
4. Add a caption: *Within 1 pp of the paper on both headline accuracies; recall is 2 pp lower (44 missed infected cells).*
5. Fix the slide-number text in the corner if needed. Save, close, then: `./sync.sh "Slides: add A0 results figures"`

### Commit 3: speaker notes + check
1. On the figures slide, in **Notes**, write in your own words what each chart shows: paper vs. ours bars, training curves, confusion matrix, ROC.
2. Check slides 18–20 against `results/A0_baseline/A0_summary.json` (or ask Murali to run `python src/check_results.py`).
3. `./sync.sh "Slides: speaker notes for results figures"`

---

## Pugal: report (3 commits)

Edit `docs/report.md` in VS Code (preview it with **Cmd/Ctrl+Shift+V**).

### Commit 1: introduction
Add this **above** `## 1. Baseline reproduction` and renumber the sections below it (1→2, 2→3):

```markdown
## 1. Introduction

Malaria is diagnosed by looking at Giemsa-stained blood smears under a microscope, where a trained technician checks each red blood cell for parasites. This works, but it is slow (each slide holds hundreds of cells), it depends on scarce expert skill (especially in the rural regions where malaria is common), and results vary between observers and labs.

Our goal is an automated deep-learning system that classifies single red-blood-cell images as **parasitized** or **uninfected**, accurately and consistently, and light enough to eventually run at the point of care.

Phase 1 surveyed 11 published studies. In Phase 2 (this report) we reproduce the strongest-documented one, Marques et al. (2022), as our baseline, then test whether its accuracy holds up once slide-level leakage is removed.
```

Then: `./sync.sh "Report: introduction"`

### Commit 2: dataset
Add after the introduction:

```markdown
## 2. Dataset

We use the **NIH Malaria Cell Images** dataset, the common benchmark across all 11 studies we reviewed. It was built from Giemsa-stained thin blood smears collected at Chittagong Medical College Hospital, Bangladesh, and segmented into single cells.

- **27,558** cell images, balanced: 13,779 parasitized and 13,779 uninfected
- **200** patients/slides (150 infected, 50 healthy). We extract a slide ID from each file name, which our hypothesis H1 needs
- Cell crops vary in size (roughly 70–230 px); all are resized to 224 × 224 for EfficientNet-B0

**Known issue:** Fuhad et al. found staining artifacts mislabelled as parasites and cleaned the set to 26,161 verified images. We use the original set, to match the paper we reproduce.

![Example cells](../results/A0_baseline/samples.png)
```

Then: `./sync.sh "Report: dataset section"`

### Commit 3: contributions + next steps
Add at the end of the report:

```markdown
## Next steps

Run experiments A1 (slide-grouped split), A2 (+ YUV stain normalisation) and A3 (control) with the same recipe as A0, and report mean ± SD over folds, recall and MCC for each.

## Contributions

| Member | Contribution |
|---|---|
| Amathziah J | (fill in) |
| Murali Madhav C | (fill in) |
| Ravi Yadav | (fill in) |
| Pugazhendhi J | (fill in) |
```

Fill in the Contributions table **together as a team**, honestly. Then: `./sync.sh "Report: next steps and contributions"`

---

**Order:** anyone can go first, since you edit different files. Just run `./sync.sh` before each task.
