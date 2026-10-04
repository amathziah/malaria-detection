# How we work (4 people)

**Only amathziah runs Kaggle.** Everyone edits code, slides or the report together on amathziah's Mac and uploads straight to `main`. No branches, no pull requests.

## 1. Setup

None. We all use **amathziah's Mac**, folder `~/Downloads/Malaria_detection`, opened in VS Code. No Kaggle, GitHub login or GPU needed.

## 2. Every time you work: two commands (in the VS Code terminal)

```bash
./sync.sh                                        # BEFORE you start: get the latest
# ... edit files together ...
./sync.sh "Slides: add team slide" ravi pugal    # WHEN DONE: note + who worked on it
```

Commits are made from amathziah's account. List the people who **actually worked on that change** after the note (`murali`, `ravi`, `pugal`), and GitHub credits them as **co-authors**: their name and avatar appear on the commit and it counts in their contribution graph. Only list people who really worked on it.

- Close the `.pptx` in PowerPoint before saving (PowerPoint keeps a lock file while it's open).

## 3. Who does what

### amathziah — owner, Kaggle runs
- Runs experiments on Kaggle when someone asks, then saves the output to `results/<experiment>/` and runs `./sync.sh "A1 results"`.
- Next up: run **A1, A2 and A3** (turn on all three flags in the `kaggle_run/` copy; about 4–5 h on 2× T4, one session).

### murali — code (`notebooks/`, `src/`)
- The notebook and `src/phase2_baseline_marques2022.py` hold the same code. **Change one, change the other.**
- Don't change the training settings in `CFG` (LR, epochs, image size, batch size, folds).
- Keep the A1–A3 flags `False` in what you upload. Tell amathziah which experiment to run.
- Before uploading the notebook: *Clear All Outputs* in VS Code.
- Next task: read the notebook top to bottom, fix any unclear comment or typo, and add a short markdown cell at the top listing the team. Same text changes in `src/`.

### ravi — slides (`slides/`)
- Work in `slides/Malaria_Phase2_Baseline_Hypothesis_filled.pptx`. Leave the original as-is.
- **Only you edit the deck.** If someone else needs a change, they tell you.
- Take numbers from `results/<experiment>/` files, never from memory.
- Next task: add a team slide (names + roles) and check slides 18–20 against `results/A0_baseline/A0_summary.json`.
- After A1–A3 run: add their results (`results/A1_slide_split/` etc.).

### pugal — report (`docs/`)
- Write the report in `docs/report.md` (or a `.docx` in `docs/`, but then only you edit it).
- Next task: `docs/report.md` has the baseline section. Write the **Introduction & dataset** section above it, using slides 2–4 as the source.
- After A1–A3 run: write the **Hypothesis results** section.

## 4. Rules for everyone
- Stick to your own folder. Don't edit someone else's files. Tell them instead.
- Never upload models (`.keras`), `.zip` files or anything from `~/.kaggle/`. `.gitignore` already blocks these.
- Never use `git push -f`. It deletes other people's work.
- Only add someone as a co-author if they really worked on that change.
- Never set `MALARIA_SMOKE_TEST`.

## Need a Kaggle run?
Save your code with `./sync.sh "..." <names>`, then tell amathziah what to run, e.g. *"Run A1 with my latest change"*. The results appear in `results/<experiment>/` on this Mac.
