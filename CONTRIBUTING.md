# How we work (4 people)

**Only amathziah runs Kaggle.** Everyone else edits code, slides or the report and uploads straight to `main`. No branches, no pull requests.

## 1. Setup

None. We all use **amathziah's Mac**, folder `~/Downloads/Malaria_detection`, opened in VS Code. No Kaggle, GitHub login or GPU needed.

## 2. Every time you work: two commands (in the VS Code terminal)

```bash
./sync.sh                                   # BEFORE you start: get the latest
# ... edit your files ...
./sync.sh ravi "Slides: fixed footer"       # WHEN DONE: your name + a short note
```

Use **your own name**: `amathziah`, `murali`, `ravi` or `pugal`. That's how GitHub credits the work to you.
It only uploads **your** folder (murali → `notebooks/` `src/`, ravi → `slides/`, pugal → `docs/` `README.md`), so someone else's unfinished edits are never uploaded under your name.

- Save before you hand the laptop to the next person.
- Close the `.pptx` in PowerPoint before saving (PowerPoint keeps a lock file while it's open).

## 3. Who does what

### amathziah — owner, Kaggle runs
- Runs experiments on Kaggle when someone asks, then saves the output to `results/<experiment>/` and runs `./sync.sh amathziah "A1 results"`.
- Next up: run **A1, A2 and A3** (turn on all three flags in the `kaggle_run/` copy; about 4–5 h on 2× T4, one session).

### murali — code (`notebooks/`, `src/`)
- The notebook and `src/phase2_baseline_marques2022.py` hold the same code. **Change one, change the other.**
- Don't change the training settings in `CFG` (LR, epochs, image size, batch size, folds).
- Keep the A1–A3 flags `False` in what you upload. Tell amathziah which experiment to run.
- Before uploading the notebook: *Clear All Outputs* in VS Code.
- First task: read sections 8–11 of the notebook (A1–A3 experiments + conclusion), check they make sense, and fill in section 11's blanks with the A0 numbers from `results/A0_baseline/A0_summary.json`.

### ravi — slides (`slides/`)
- Work in `slides/Malaria_Phase2_Baseline_Hypothesis_filled.pptx`. Leave the original as-is.
- **Only you edit the deck.** If someone else needs a change, they tell you.
- Take numbers from `results/<experiment>/` files, never from memory.
- First task: check slide 18. The A0 results are filled in. Change the footer "(Kaggle T4 GPU)" to "(Kaggle 2× T4 GPU)".
- After A1–A3 run: add their results (`results/A1_slide_split/` etc.).

### pugal — report (`docs/`)
- Write the report in `docs/report.md` (or a `.docx` in `docs/`, but then only you edit it).
- First task: write the **Baseline reproduction** section: the method (from the notebook's intro and `README.md`), the A0 table (`results/A0_baseline/A0_vs_paper.csv`), and the plots `A0_curves_cm_roc.png` and `A0_vs_paper.png`.
- After A1–A3 run: write the **Hypothesis results** section.

## 4. Rules for everyone
- Stick to your own folder. Don't edit someone else's files. Tell them instead.
- Never upload models (`.keras`), `.zip` files or anything from `~/.kaggle/`. `.gitignore` already blocks these.
- Never use `git push -f`. It deletes other people's work.
- Never set `MALARIA_SMOKE_TEST`.

## Need a Kaggle run?
Save your code with `./sync.sh <your-name> "..."`, then tell amathziah what to run, e.g. *"Run A1 with my latest change"*. The results appear in `results/<experiment>/` on this Mac.
