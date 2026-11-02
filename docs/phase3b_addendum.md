# Phase 3b addendum: one correction and four exploratory analyses

Written on 2 November 2026, **after** the A1–A3 results in `results/ablation/` were known, and committed **before**
any of the analyses below was run. It does not change H1, H2 or their pre-registered verdicts
(`docs/phase3_analysis_plan.md`). Everything in it is exploratory.

What we already knew when we wrote it:

- every number in `results/ablation/`, including the per-patient error counts on the hold-out set;
- a literature review (`reports/Strengthening malaria ablation results.md`), which approximated some equivalence
  intervals from the reported 95 % CIs.

The margins and decision rules below come from that literature, not from those approximations. The new quantities
had not been computed:
- same-cell differences;
- patient-level calls;
- TOST p-values from the bootstrap replicates;
- candidate label errors.

## D1 · Correction: the unpaired fold test (A1 vs A0)

The plan compared A1's and A0's fold scores with a plain Welch t-test and called it descriptive. It still treated
each arm's ten fold scores as independent, but folds share about 89 % of their training data. The Nadeau–Bengio
correction exists for exactly this reason, and the plan already used it for the paired contrasts.

From now on, each arm's variance of the fold mean is `var × (1/k + n_test/n_train)` instead of `var / k`, with
Welch–Satterthwaite degrees of freedom (`ablation_stats.corrected_unpaired_ttest`). The first-reported value,
p = 0.0075 (Holm 0.023) for fold MCC, stays in the summary as `p_welch`, labelled as overstated. No other number
changes. The pre-registered H1 test, the ensemble on the hold-out set, is unaffected.

## E1 · Equivalence bounds and minimum detectable effects

*Question:* what effect sizes do the YUV contrasts rule out, and what could this design have detected at all?

- **Contrasts:** A2 − A1 (H2) and A3 − A0 (control). MCC is primary; accuracy is secondary. Clean protocol.
- **Margin:** ±1 pp MCC, about ±0.5 pp accuracy or 28 hold-out cells. It is smaller than the 1.51 pp fold SD that
  the plan used as the bar for a meaningful H2 gain, and half of Benavoli et al.'s (2017) ±1 % accuracy region of
  practical equivalence.
- **Test:** two one-sided tests at α = 0.05; equivalence holds when the 90 % CI lies inside ±1 pp.
  - Ensemble: the 5th–95th percentiles of the paired patient bootstrap (10,000 resamples, seed 0).
  - Folds: the corrected t interval, df = 9.
  - We also report the smallest margin each contrast passes.
- **Minimum detectable effect** (80 % power, two-sided α = 0.05) for every contrast, from its own standard error:
  - bootstrap SE × (z₀.₉₇₅ + z₀.₈₀);
  - corrected-t SE × (t₀.₉₇₅,₉ + t₀.₈₀,₉).
- **Design effect:** the variance of A1's hold-out MCC and accuracy under the patient bootstrap, divided by the
  variance under a cell bootstrap (10,000 resamples each).

## E2 · Leakage measured on identical cells

*Question:* on the same cells, does a model that saw other cells of the patient score higher than one that never
saw the patient? This removes the two problems of the H1 hold-out comparison: different test sets, and a 40-patient
draw that is about 1 pp easier than average.

- **Estimand:** metric(A1) − metric(A0) on identical cells, matching the H1 contrast. H1 predicts a negative value.
- **E2a (main):** the A0 and A1 ten-model ensembles on A0's hold-out cells that belong to A1's 40 held-out
  patients. A0 trained on other cells of these patients; A1 never saw them.
- **E2b (secondary):** the out-of-fold predictions on cells in both arms' cross-validation sets.
  - A0's fold model had seen other cells of the patient; A1's fold model had not.
  - These are single models, so the interval does not include run-to-run noise.
- **Statistics:** a paired patient-cluster bootstrap (10,000 resamples, seed 0) with a 95 % CI and p, plus the
  E1 TOST at ±1 pp MCC. Metrics are MCC, accuracy, recall and specificity.
- **Reading, fixed now:**
  - *leakage detected* if the 95 % CI lies entirely below 0;
  - *equivalent within ±1 pp* if the 90 % CI lies inside ±1 pp;
  - otherwise *inconclusive*.

## E3 · Patient-level diagnosis

*Question:* if the A1 model's cell calls are combined per patient, how well does it separate infected from
healthy patients it has never seen?

- **Truth:** a patient is infected if they have at least one cell labelled parasitized (28 of the 40 held-out
  patients, 122 of the 160 CV patients). Otherwise healthy (12 and 38).
- **Rule family:** a patient is positive if at least τ of their cells have P(parasitized) ≥ t.
  - t ∈ {A1's CV-chosen F2 threshold, 0.5, 0.8, 0.95, 0.99}.
  - τ ∈ {1, 2, 3, 4, 5, 6, 8, 10, 12, 15}.
- **Selection:** only on the 160 CV patients' out-of-fold predictions. The criterion is the highest Youden J among
  rules with CV specificity ≥ 95 % (if none qualifies, the highest J overall). Ties go to the higher specificity,
  then the smaller τ, then the smaller t.
- **Optimism check:** nested leave-one-fold-out. The rule is chosen on 9 folds' patients and scored on the
  10th's, pooled over the 10 folds.
- **Hold-out:**
  - The chosen rule is applied once to the 40 held-out patients with the A1 ensemble.
  - As a robustness check, it is also applied with each of the 10 A1 fold models.
  - We report sensitivity and specificity with exact Clopper–Pearson 95 % CIs, and name every misclassified
    patient.
- **Dilution stress test:**
  - Each infected held-out patient keeps only m ∈ {1, 2, 3, 5} randomly chosen parasitized cells, plus all of
    their uninfected cells.
  - 1,000 draws, seed 0; we report the mean sensitivity of the chosen rule.
- **Disclosure, to be printed with every result:**
  - NIH kept about 68 uninfected crops per patient but the parasitized cells were curated, so per-patient parasite
    counts are not natural parasitaemia.
  - There are only 12 healthy held-out patients.
  - There are no parasite densities.
  - This is exploratory aggregation on curated crops, not a diagnostic accuracy study.

## E4 · Error audit

*Question:* where do the remaining errors sit, and could some of them be label problems?

- **E4a · false alarms by patient status.** For the A1 ensemble on the hold-out set, and A1's out-of-fold
  predictions on the CV set, we compare uninfected-labelled cells flagged as parasitized at threshold 0.5 in
  infected patients' smears with those in healthy patients' smears. Each rate, and their difference, gets a 95 %
  CI from a bootstrap that resamples patients within each status group.
- **E4b · do errors cluster by patient?**
  - Statistic: the χ² dispersion of per-patient error counts against a common error rate within each label class.
  - Null: a permutation test that shuffles the error indicator across cells of the same label (10,000
    permutations, seed 0).
  - Data: the A1 hold-out set and A1's out-of-fold predictions.
- **E4c · candidate label errors** (confident learning, Northcutt et al. 2021, two classes).
  - A cell labelled c is a candidate when the predicted probability of the other class is at least that class's
    mean predicted probability among cells labelled with it. Candidates are ranked by the probability of their
    given label, lowest first.
  - This is run separately on A1's out-of-fold predictions and on the A1 hold-out ensemble.
  - They are **candidates**, never relabelled, and the original-label accuracy stays the headline.
- **E4d · do the verdicts survive?** We recompute the A2 − A1 and A3 − A0 ensemble contrasts after removing the
  hold-out cells flagged in E4c by either arm of the contrast. We report whether the sign and the 95 % CI change.
- **E4e · gallery and calibration.**
  - A blinded gallery mixes all 86 A1 hold-out errors with 86 correct cells matched by label, shuffled, with the
    answer key in a separate file. It is for the team's own triage: two people, the rubric in the report, Cohen's
    κ.
  - We also draw a reliability diagram of the A1 hold-out ensemble beside its ECE.

## Not done, and why

- **Test-time augmentation:** the expected change is 0–6 cells, so it would not change the conclusions.
- **A colour-augmentation training arm (H3):** not chosen. The expected same-site effect is below the minimum
  detectable effect.
- **External validation (MP-IDB):** 3–5 person-days; future work.
- **Cross-checking against Delves's relabelled dataset (IEEE DataPort):** needs a team login; left to the team.

Outputs: `src/phase3b_analysis.py` writes `results/phase3b/`.
