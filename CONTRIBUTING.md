# How we work (4 people)

**Only the repo owner runs Kaggle.** Everyone else changes code, slides or docs, opens a pull request, and the owner runs anything that needs a GPU.

## Roles (fill in names)

| Who | Works on | Files they edit |
|---|---|---|
| Owner: amathziah| runs Kaggle, merges PRs, commits results | `results/`, `kaggle_run/` |
| Member 2:murali| code (A1–A3 experiments, fixes) | `notebooks/`, `src/` |
| Member 3: ravi| slides | `slides/` |
| Member 4: pugal| report / write-up | `docs/`, `README.md` |

Swap roles freely. The point is that **two people shouldn't edit the same file at the same time.**

## One-time setup (on your own Mac)

```bash
git config --global user.name  "Your Name"
git config --global user.email "the-email-on-your-github-account"

brew install gh          # skip if you already have it
gh auth login            # GitHub.com → HTTPS → log in with browser

# accept the collaborator invite from your email first, then:
gh repo clone <owner>/malaria-detection
cd malaria-detection
```

No Kaggle, TensorFlow or GPU needed.

## Every change: branch → commit → pull request

```bash
git checkout main && git pull          # always start from the latest main
git checkout -b slides-results         # short name describing your change

# ...edit files...

git add <the files you changed>
git commit -m "Slides: add A1 results to slide 19"
git push -u origin slides-results
gh pr create --fill                    # or open the PR on github.com
```

The owner reviews and merges. Afterwards everyone runs `git checkout main && git pull`.

## Rules

**Code (`notebooks/`, `src/`)**
- The notebook and `src/phase2_baseline_marques2022.py` contain the same code. If you change one, make the same change in the other.
- Don't change the training settings in `CFG` (LR, epochs, image size, batch size, folds). Every experiment has to use the paper's recipe to be comparable.
- Keep the A1–A3 flags `False` in your PR. In the PR, write which experiment you want run, and the owner turns the flag on for that Kaggle run.
- Before committing the notebook: *Clear All Outputs* (VS Code / Jupyter). This keeps diffs small.
- Never set `MALARIA_SMOKE_TEST`.

**Slides (`slides/`)**
- `.pptx` files can't be merged by git. **Only one person edits the deck at a time.** Say in the group chat "I'm editing the slides" and pull right before you start.
- Edit `Malaria_Phase2_Baseline_Hypothesis_filled.pptx` (the working deck). Leave the original as-is.
- Take numbers from `results/<experiment>/` files. Don't type them from memory.

**Never commit:** `.keras` models, `.zip` files, anything from `~/.kaggle/`. `.gitignore` already blocks these.

## When you need a run

Open a PR (or a GitHub issue) saying what to run, e.g. *"Run A1 with my change from PR #3"*. The owner runs it on Kaggle and commits the output to `results/<experiment>/`. Then you pull to get the numbers.
