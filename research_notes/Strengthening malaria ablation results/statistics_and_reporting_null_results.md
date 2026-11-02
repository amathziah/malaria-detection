# Statistics and reporting for a pre-registered ML ablation with null or negative results (NIH malaria, EfficientNet-B0 reproduction)

Conventions used below:
- "pp" means percentage points of MCC × 100, unless the text says "accuracy pp".
- "Computed" means my own arithmetic from the team's reported numbers. I ran it with SciPy t and normal quantiles in a scratch script. Where only a 95 % cluster-bootstrap CI was available, I derived each side's SE as half-width / 1.96. The team should recompute the exact percentile values from its saved 10,000 bootstrap replicates.
- On this balanced dataset MCC ≈ 2 × accuracy − 1. Check on A0: 2 × 0.9764 − 1 = 0.9528, against the reported 0.9529. So a difference of 1 pp MCC is about 0.5 pp of accuracy.
- Sources were fetched on 2 Nov 2026.

## Q1. Equivalence testing and the smallest effect size of interest: TOST with bootstrap CIs, defensible margins, ML examples, and the ±1 pp MCC check

### Takeaway
At a ±1 pp MCC margin, both paired hold-out ensemble contrasts pass the equivalence test:
- A2 − A1: 90 % CI ≈ [−0.76, +0.15], TOST p ≈ 0.007.
- A3 − A0: 90 % CI ≈ [−0.44, +0.45], TOST p ≈ 0.0001.

The fold-level A2 − A1 contrast does not pass: 90 % CI [−1.25, +0.05], TOST p ≈ 0.14. It passes only for margins of at least 1.25 pp. That includes the pre-registered 1.51 pp threshold, where TOST p ≈ 0.015.

No equivalence margin was pre-registered, so all of these tests are exploratory. Report them that way, together with the smallest margin at which each contrast would pass.

### Cited Findings
**How TOST works and how to decide**
- Under TOST, equivalence means "the observed effect falls within the equivalence bounds and is close enough to zero to be practically equivalent". [Lakens 2017, SPPS 8(4):355–362](https://doi.org/10.1177/1948550617697177)
- For α = 0.05, the decision uses "A 90% confidence interval (CI; 1 − 2α) … instead of a 95% CI (1 − α)". Lakens adds: "Readers are free to replace decisions based on p values by decisions based on 90% CIs if they wish." [Lakens 2017](https://doi.org/10.1177/1948550617697177)
- Combining a null-hypothesis test with an equivalence test gives four possible outcomes. Two of them are "statistically different from zero but not statistically equivalent" and "undetermined (neither statistically different from zero nor statistically equivalent)". [Lakens 2017](https://doi.org/10.1177/1948550617697177)
- Lakens on non-significance:
  - "It is not possible to conclude there is no effect when p > α."
  - "nonsignificant test results are hardly indicative of the absence of a true effect."
  - "It is statistically impossible to support the hypothesis that a true effect size is exactly zero."

  Source: [Lakens 2017](https://doi.org/10.1177/1948550617697177)

**Ways to set the margin (SESOI)**
- Feasibility: researchers can "set the bounds to the smallest effect size they have sufficient power to detect". [Lakens 2017](https://doi.org/10.1177/1948550617697177)
- Small telescopes (Simonsohn): set the bound to "the effect size that would have given an original study 33% power". [Lakens 2017](https://doi.org/10.1177/1948550617697177)
- Lakens warns that bounds can be too wide: "the extremely large equivalence bounds will make it clear they can at best reject extremely large effects". [Lakens 2017](https://doi.org/10.1177/1948550617697177)
- He also warns: "When theories do not specify which effect sizes are too small to be meaningful, theories can't be falsified." [Lakens 2017](https://doi.org/10.1177/1948550617697177)
- The AMPPS tutorial introduces TOST as a way to "reject the presence of a smallest effect size of interest (SESOI)" and explains a range of approaches to choosing the SESOI. Its abstract says: "Equivalence tests are an important extension of the statistical tools psychologists currently use." [Lakens, Scheel & Isager 2018, AMPPS 1:259–269](https://doi.org/10.1177/2515245918770963)
  - I could not read the full text (HTTP 403); see Gaps.

**ML worked example: a ±1 % accuracy "rope"**
- "In classification, it is sensible to define that two classifiers whose mean difference of accuracies is less that 1% are practically equivalent. The interval [−0.01, 0.01] thus defines a region of practical equivalence (rope)". [Benavoli, Corani, Demšar & Zaffalon 2017, JMLR 18:1–36](https://jmlr.org/papers/v18/16-305.html)
- Their footnote: "In classification 1% seems to be a reasonable choice. However, in other domains a different value could be more suitable." [Benavoli et al. 2017](https://jmlr.org/papers/v18/16-305.html)
- Benavoli et al. on what a p-value can tell you: "rejecting a null hypothesis does not provide any information about the magnitude of the effect and whether or not the effect is trivial." [Benavoli et al. 2017](https://jmlr.org/papers/v18/16-305.html)
- On cross-validation, "the usual t-test is not calibrated … its rate of Type I errors is much larger than α (Dietterich, 1998)". The Nadeau–Bengio heuristic ρ = n_te/n_tot gives "the correlated t-test … to account for the correlation due to the overlapping training sets". [Benavoli et al. 2017](https://jmlr.org/papers/v18/16-305.html)
- Their worked example of the Bayesian correlated t-test uses ρ = 1/10 for 10-fold CV. The posterior gives P(practically negative), P(inside the rope) and P(practically positive). The authors note that under their prior settings the Bayesian posterior probability and the frequentist correlated-t p-value are numerically equivalent. [Benavoli et al. 2017](https://jmlr.org/papers/v18/16-305.html); [Corani & Benavoli 2015, Mach Learn 100:285–304](https://doi.org/10.1007/s10994-015-5486-z)

**ML worked example: a "meaningful improvement" threshold**
- Bouthillier et al. call A better than B when the probability of outperforming satisfies P(A>B) ≥ γ, "with a threshold of 0.75". The CI comes from a percentile bootstrap.
  - Significance requires P(A>B) − CI_min > 0.5.
  - Meaningfulness requires P(A>B) + CI_max > γ.

  Source: [Bouthillier et al. 2021, MLSys, arXiv:2103.03098](https://arxiv.org/abs/2103.03098)
- They also write: "Improvements smaller than this variance observed on a given test set will not generalize." [Bouthillier et al. 2021](https://arxiv.org/abs/2103.03098)

**Medical-imaging recommendation for superiority testing**
- Varoquaux & Cheplygina:
  - "recommend to replace traditional null-hypothesis testing with superiority testing"
  - "a method should be accepted based on evidence that it brings a sizable improvement"
  - "measuring a tiny improvement on a benchmark is seldom useful"

  Source: [Varoquaux & Cheplygina 2022, npj Digit Med](https://doi.org/10.1038/s41746-022-00592-y)

**Anchors from the original paper (Marques et al. 2022)**
- Design: cell-level stratified 10-fold CV on 22,046 images, plus a separate 5,512-image validation set with 2,756 per class.
- The mean single-model accuracy on that set was 97.70 %, with fold models ranging from 97.34 % to 97.96 %.
- The ensemble reached 98.29 % accuracy, with recall 98.82 %, precision 97.74 %, FPR 0.0222 and FNR 0.0118.
- The authors call this a "25.75% error decrease" over the averaged models.
- The paper does not report MCC and does not mention patient-level splitting.

  Source: [Marques, Ferreras & de la Torre-Díez 2022, Multimed Tools Appl 81:28061–28078](https://doi.org/10.1007/s11042-022-12624-6)

**Seed noise in a 2026 malaria study**
- Under slide-disjoint evaluation, the seed SDs of accuracy were ±0.36 to ±1.19 pp across eight architectures (EfficientNet-B0: ±0.60 pp; 3 seeds). [Hou et al. 2026, Biosensors 16(7):358](https://doi.org/10.3390/bios16070358)

### Inferences
**1. How to run TOST with the patient-cluster bootstrap they already have**
- Resample the same patients for both arms of each paired contrast. The A2−A1 and A3−A0 contrasts are paired because they use the same hold-out cells.
- Compute Δ* = MCC_B* − MCC_A* in each of the 10,000 replicates.
- Declare equivalence at α = 0.05 if the 5th and 95th percentiles of Δ* both lie inside (−δ, +δ).
- By test–CI duality, the one-sided p-values are p_low = P*(Δ* ≤ −δ) and p_high = P*(Δ* ≥ +δ). The TOST p is the larger of the two.
- Apply Holm across the family of equivalence tests.
- For fold contrasts, use the NB-corrected t with df = 9 and its 90 % CI.

**2. Computed equivalence table** (margin ±1 pp MCC, which is about ±0.5 pp accuracy)

| Contrast | Data / test | Δ MCC (pp) | Reported 95 % CI | 90 % CI (computed) | Smallest δ that passes TOST | Equivalent at ±1? | TOST p at ±1 | Lakens outcome at ±1 |
|---|---|---|---|---|---|---|---|---|
| A2 − A1 | 10 paired folds, NB-corrected t, df 9 (SE 0.354) | −0.60 | ≈[−1.4, +0.2] | [−1.25, +0.05] | 1.25 | **No** | 0.14 | undetermined |
| A2 − A1 | Same 40-patient hold-out, paired cluster bootstrap | −0.26 | [−0.85, +0.23] | ≈[−0.76, +0.15] | ≈0.76 | **Yes** (the 95 % CI is inside too) | ≈0.007 | equivalent, not different |
| A3 − A0 | Same image-split hold-out, paired cluster bootstrap | 0.00 | [−0.52, +0.53] | ≈[−0.44, +0.45] | ≈0.45 | **Yes** (also at ±0.5: p ≈ 0.03) | ≈0.0001 | equivalent, not different |
| A1 − A0 (H1) | Different hold-outs, unpaired | +1.62 | [+0.01, +3.12] | ≈[+0.27, +2.88] | ≈2.9 | No | ≈0.79 | undetermined after Holm (p = 0.15) |

- Check on the fold row: the SE implied by the CI gives a two-sided p of 0.124, which matches the reported 0.13.
- Holm across the three ±1 pp equivalence tests:
  - A3−A0: 0.0001 × 3 ≈ 0.0003, passes.
  - A2−A1 ensemble: 0.007 × 2 ≈ 0.014, passes.
  - A2−A1 fold: 0.14, fails.

**3. Menu of defensible margins**
- Each margin is shown with the contrasts that pass it.
- State the margin's rationale explicitly, as TRIPOD+AI and Lakens require (see Q3 and the findings above).

| Margin (MCC pp) | Rationale | Source | A2−A1 fold | A2−A1 hold-out | A3−A0 hold-out |
|---|---|---|---|---|---|
| ±0.5 (≈0.25 acc) | Stricter than any noise estimate | none (illustrative) | fail | fail (p ≈ 0.21) | pass (p ≈ 0.03) |
| ±1.0 (≈0.5 acc) | The brief's margin; about half of Benavoli's rope | none | fail | pass | pass |
| ≈±1.2 (≈0.59 acc) | The ensemble gain Marques et al. reported as their contribution (97.70 → 98.29 % accuracy) | [Marques 2022](https://doi.org/10.1007/s11042-022-12624-6) | fail (needs 1.25) | pass | pass |
| ±1.51 | A1's fold SD; the team's own pre-registered threshold for H2; noise-based ([Bouthillier 2021](https://arxiv.org/abs/2103.03098)) | pre-registration | pass (p ≈ 0.015) | pass | pass |
| ±2.0 (≈1.0 acc) | Benavoli's rope of 1 % accuracy, converted to MCC | [Benavoli 2017](https://jmlr.org/papers/v18/16-305.html) | pass | pass | pass |

- The original paper's gain behaves like a "small telescopes"-style anchor. If stain normalisation changes MCC by less than the gain that justified the original publication, the change is negligible by the field's own standard.
- I derived MCC ≈ 96.6 for Marques's ensemble from their FPR and FNR on the balanced set. This is not a reported number. The team's A0 MCC of 95.29 is therefore about 1.3 pp lower, a reproduction gap close in size to the margins above.

**4. Bayesian complement for the fold contrast** (computed)
- Use the Bayesian correlated t-test with ρ = 1/10 and the default prior. Its posterior equals the NB-corrected t with location −0.60, SE 0.354 and df 9.
- Results: P(|Δ| < 1 pp) ≈ 0.86, P(Δ < −1 pp) ≈ 0.14, P(Δ > +1 pp) ≈ 0.001.
- Suggested wording: "the fold data favour practical equivalence but do not establish it".

**5. Power of the equivalence test**
- If the true Δ is 0, TOST has 80 % power when δ ≥ (1.645 + 1.282) × SE ≈ 2.93 × SE.
- Paired hold-out contrasts (SE ≈ 0.27–0.28): about ±0.8 pp. The ±1 pp test was therefore adequately powered.
- Fold contrasts (SE 0.354): about ±1.04 pp in the normal approximation, more with df 9. A failure at ±1 pp was predictable from the design.

**6. Sentences the team could add**
- "Equivalence tests were not pre-registered and are exploratory. Using a ±1 pp MCC margin (≈ ±0.5 pp accuracy; half of the 1 %-accuracy region of practical equivalence of Benavoli et al. 2017), YUV histogram equalisation was statistically equivalent to no normalisation on the 40-patient hold-out (ΔMCC −0.26 pp; 90 % patient-cluster bootstrap CI −0.76 to +0.15; TOST p ≈ 0.007) and on the image-split hold-out (A3−A0: 0.00 pp; 90 % CI −0.44 to +0.45; TOST p < 0.001)."
- "On cross-validation folds the data are compatible with effects from −1.25 to +0.05 pp (90 % CI), so we cannot claim equivalence at ±1 pp. We can claim it within the pre-registered smallest effect of interest of ±1.51 pp (TOST p = 0.015)."
- "For H2 we pre-registered a superiority-by-margin rule: the gain had to exceed A1's fold SD. Varoquaux & Cheplygina (2022) recommend this kind of rule instead of testing against zero."

**7. Claims that would overreach**
- "YUV normalisation has no effect." Only bounds on the effect are supported, and the fold CI reaches −1.25 pp.
- "YUV is useless for malaria microscopy." The data come from one dataset and one site, and the result says nothing about cross-site shift.
- "A1 and A0 are equivalent." Not supported.
- "Patient splitting improves performance." This rests on the unpaired +1.62 pp, where the hold-outs differ and A1's 40 patients are easier; Holm p = 0.15.
- Choosing the margin after seeing the CIs without saying so.

### Gaps
- I could not read the full AMPPS tutorial (Lakens, Scheel & Isager 2018; HTTP 403). Its specific SESOI approaches, for example benchmarks and minimal clinically important difference, are therefore cited from Lakens 2017 and the 2018 abstract only.
- I found no published frequentist TOST worked example for comparing deep-learning classifiers. The closest ML examples are Benavoli's Bayesian rope and Bouthillier's P(A>B).
- I found no source that defines a clinically meaningful margin for cell-level MCC. Clinical decisions are made per patient by aggregating many cells, so a clinical margin for cell MCC remains unjustified.
- The 90 % CIs above use a per-side normal approximation to a percentile bootstrap. Exact values need the bootstrap replicates.
- The fold CI "about [−1.4, +0.2]" was rounded, which moves the threshold of 1.25 pp by a few hundredths.
- The Corani & Benavoli 2015 DOI comes from bibliographic knowledge. It is cited inside the Benavoli PDF, but I did not fetch it.

## Q2. Minimum detectable effect and power with patient-clustered data

### Takeaway
Computed MDEs at 80 % power, two-sided α = 0.05:

| Contrast | MDE (MCC pp) | ≈ accuracy pp |
|---|---|---|
| Paired hold-out ensemble contrasts | ≈ 0.75–0.77 | ≈ 0.38 |
| Paired fold contrasts | ≈ 1.0–1.1 | ≈ 0.5 |
| Unpaired H1 hold-out contrast | ≈ 2.2 | ≈ 1.1 |
| Unpaired fold contrast (naive) | ≈ 1.6 | |
| Unpaired fold contrast (NB-inflated) | ≈ 2.3 | |

With Holm-adjusted α these MDEs are about 16 % larger.

Detecting a 0.5 pp accuracy difference (≈ 1 pp MCC):
- Paired design: about 24 held-out patients. The existing 40 are enough.
- Unpaired design: about 200 held-out patients. A 200-patient dataset cannot supply that.

The fold-level "leakage effect, Holm p = 0.02" is fragile. Correcting for fold dependence makes it p ≈ 0.048 raw and Holm p ≈ 0.14.

### Cited Findings
**MDE and design effect**
- The MDE is a multiple of the standard error of the impact estimate. The multiplier is z₁₋α/₂ + z₁₋β ≈ 1.96 + 0.84 = 2.80 for two-sided α = 0.05 and 80 % power. [Bloom 1995, Evaluation Review 19(5):547–556](https://doi.org/10.1177/0193841X9501900504) (not fetched; the multiplier is checked by the arithmetic: 1.960 + 0.842 = 2.802)
- Kish design effect for clustered data: Deff = 1 + (m − 1) × ICC, where m is cluster size. The effective sample size is n / Deff. [Killip, Mahfoud & Pearce 2004, Ann Fam Med 2:204–208](https://doi.org/10.1370/afm.141) (not fetched)
- With unequal cluster sizes the design effect grows with the coefficient of variation of cluster size. [Eldridge, Ashby & Kerry 2006, Int J Epidemiol 35:1292–1300](https://doi.org/10.1093/ije/dyl129) (not fetched)
- In radiology, sensitivity and specificity computed from several lesions or images per patient need cluster-aware methods. [Genders et al. 2012, Radiology 265:910–916](https://doi.org/10.1148/radiol.12120509) (not fetched)

**Cross-validation folds are not independent**
- The plain t-test applied to CV results has Type I error "much larger than α", and "the correlation cannot be estimated from data". The NB heuristic sets ρ = n_te/n_tot. [Benavoli et al. 2017](https://jmlr.org/papers/v18/16-305.html); [Nadeau & Bengio 2003, Mach Learn 52:239–281](https://doi.org/10.1023/A:1024068626366); [Bengio & Grandvalet 2004, JMLR 5:1089–1105](https://www.jmlr.org/papers/v5/grandvalet04a.html) (NB and BG not fetched)

**Test-set size and data sampling**
- Varoquaux & Cheplygina call for "Enough data in the test set to bring statistical power, at least several hundreds samples, ideally thousands or more". They note that "testing predictive modeling requires many samples, more than conventional inferential studies". [Varoquaux & Cheplygina 2022](https://doi.org/10.1038/s41746-022-00592-y)
- Bouthillier et al.: "Bootstrapping data stands out as the most important source of variance". They found model initialisation "generally is less than 50% of the variance of bootstrap". They advise that "Resampling techniques such as out-of-bootstrap should be favored instead of fixed held-out test sets to improve capacity of detecting small improvements." [Bouthillier et al. 2021](https://arxiv.org/abs/2103.03098)

**Reporting power after the fact**
- Report sensitivity power analysis, meaning the effect a design could detect, rather than "observed power". [Lakens 2022, Collabra: Psychology 8:33267](https://doi.org/10.1525/collabra.33267); [Hoenig & Heisey 2001, Am Stat 55:19–24](https://doi.org/10.1198/000313001300339897) (both not fetched)

**Variability benchmarks from malaria studies**
- Patient-level 5-fold CV on NIH malaria: ResNet-50 MCC 0.917 ± 0.017. The fold SD of about 1.7 pp is similar to the team's A1 SD of 1.51 pp. [Rajaraman et al. 2018, PeerJ 6:e4568](https://doi.org/10.7717/peerj.4568)
- Slide-disjoint EfficientNet-B0 accuracy SD was ±0.60 pp (3 seeds). The authors note that MalariaNet's 1.45 pp leakage drop "is, itself, within the ±1.02 seed standard deviation." [Hou et al. 2026](https://doi.org/10.3390/bios16070358)

### Inferences
**1. Computed MDE table** (80 % power, two-sided α = 0.05; MDE = M × SE)

| Contrast | SE (MCC pp) | MDE, M = 2.80 | t-based MDE | ≈ accuracy pp |
|---|---|---|---|---|
| A2−A1 folds (paired, NB-t, df 9) | 0.354 | 0.99 | 1.11 (M = 3.15) | ≈0.5 |
| A2−A1 hold-out ensemble (paired) | 0.276 | 0.77 | — | ≈0.39 |
| A3−A0 hold-out ensemble (paired) | 0.268 | 0.75 | — | ≈0.38 |
| A1−A0 hold-out ensemble (unpaired, H1) | 0.793 | 2.22 | — | ≈1.1 |
| A1−A0 folds, Welch, naive | 0.514 | — | 1.57 (df 11.8) | ≈0.8 |
| A1−A0 folds, Welch × NB inflation | 0.747 | — | 2.28 | ≈1.1 |

- With Holm-adjusted α = 0.05/3, the multiplier rises to 2.394 + 0.842 = 3.24, about ×1.16. For example, 0.77 becomes 0.89 pp.
- **Statement to add:** "With 40 held-out patients (≈139 cells each), the paired patient-cluster bootstrap SE of an ensemble MCC difference was ≈0.27 pp, so the design could detect differences of ≈0.77 pp MCC (≈0.4 pp accuracy) with 80 % power at two-sided α = 0.05 (MDE = 2.8 × SE). The unpaired H1 hold-out comparison could only detect ≈2.2 pp; it could not have detected the ≈1.65 pp fold-level leakage effect, so H1's hold-out result is inconclusive rather than negative."

**2. The fold-level leakage test is fragile** (computed)
- Taking the reported 95.57 ± 0.60 and 93.92 ± 1.51 as SDs over 10 folds, Welch gives Δ = −1.65 pp, SE 0.514, df 11.8, p = 0.0076, Holm × 3 = 0.023. This reproduces the reported "Holm p = 0.02" exactly, which suggests Welch treated the folds as independent.
- Inflating each arm's variance by the NB factor (1/k + n_te/n_tr)/(1/k) = 2.11 gives SE 0.747, p = 0.048 and Holm ≈ 0.14 if it stays the smallest p. The 95 % CI becomes [−3.28, −0.02].
- So the "descriptive" label is right. Describe the effect as "a point estimate of ≈1.65 pp MCC (≈0.8 pp accuracy), statistically fragile".
- A further finding worth reporting: the fold SD was 2.5× larger (0.60 → 1.51). Random image splits understate how much performance varies from patient to patient, which matches Bouthillier's point that data sampling dominates variance.

**3. How to estimate the ICC and design effect from data they already have**
- Re-run the hold-out bootstrap resampling cells instead of patients.
- Compute Deff = Var(patient-cluster bootstrap) / Var(cell bootstrap).
- Compute ICC ≈ (Deff − 1)/(m̄ − 1), with m̄ = 5,550/40 = 138.75. Use the Eldridge coefficient-of-variation formula if cluster sizes vary a lot.
- Report n_eff = 5,550/Deff.
- For paired contrasts the relevant ICC is that of the per-cell difference in correctness, not of correctness itself.
- Illustrative values (computed):

| ICC | Deff, A1 hold-out (m̄ 138.75) | n_eff (of 5,550 cells) | Deff, A0 hold-out (m̄ 27.6) |
|---|---|---|---|
| 0.005 | 1.69 | 3,286 | 1.13 |
| 0.01 | 2.38 | 2,334 | 1.27 |
| 0.02 | 3.75 | 1,478 | 1.53 |
| 0.05 | 7.89 | 704 | 2.33 |

- Implication: once m̄ × ICC is well above 1, precision depends on the number of patients, not cells. Varoquaux's "several hundreds … ideally thousands" should be read as effective n, not 5,550 cells.

**4. How many held-out patients are needed for 0.5 pp accuracy (≈1 pp MCC)**
- Rule: k_needed = k_now × (2.8 × SE_now / δ)². This keeps cells per patient and the disagreement rate between models fixed.
- **Paired** comparison (two pipelines on the same test patients; SE 0.276 at k = 40):
  - About 24 patients for 0.5 pp accuracy; about 32 with Holm.
  - About 95 patients for 0.25 pp accuracy (0.5 pp MCC); about 127 with Holm.
- **Unpaired** comparison (different hold-outs, as in H1; SE 0.793): about 197 patients for 0.5 pp accuracy. That is infeasible because training needs patients too.
- Analytic cross-check: Kish formula, accuracy 98.45 %, 139 cells per patient, two independent hold-outs. Patients needed per arm are 117, 164 and 259 for ICC 0.005, 0.01 and 0.02. Same conclusion.

**5. Analyses that would give a sharper answer**
- **Paired leakage design.**
  - Fix a set of test patients and split each patient's cells into a test half T and a "leak" half L.
  - Train a clean model on the 160 training patients only.
  - Train a leaky model on the same data plus L. To keep the training size equal, swap in L for an equal number of training cells.
  - Evaluate both on T and compare with a paired patient bootstrap.
  - This removes the "easier 40 patients" confound and the unpaired variance.
  - This design is my suggestion. It is analogous to the record-wise vs subject-wise comparisons in [Saeb et al. 2017](https://doi.org/10.1093/gigascience/gix019).
- **Repeated grouped hold-outs.** Use 5–10 different random 40-patient hold-outs, or nested grouped CV, to average over hold-out difficulty, as [Bouthillier 2021](https://arxiv.org/abs/2103.03098) recommends.
- **Per-patient spread.** Report per-patient accuracy or MCC for the 40 hold-out patients, for example as a dot plot.

**6. Claims that would overreach**
- Reporting "observed power" from the observed effect.
- Saying "the study was underpowered, so leakage exists".
- Saying "5,550 test cells give ±0.3 % precision" using a binomial formula that ignores clustering.

### Gaps
- No per-patient error data were available to me. The ICC and Deff numbers are illustrative, not estimates.
- The patient-scaling rule assumes cells per patient and the disagreement rate between models stay constant.
- For the unpaired H1 contrast, I assumed most of the variance comes from the 40-patient hold-out.
- The NB correction was derived for repeated random splits. Applying it to a single 10-fold CV, as Benavoli does with ρ = 1/k, is a heuristic.
- Bloom, Killip, Eldridge, Genders, Nadeau–Bengio, Bengio–Grandvalet, Lakens 2022 and Hoenig–Heisey are cited from bibliographic knowledge with DOIs. I did not fetch them in this session.

## Q3. Reporting standards: TRIPOD+AI, CLAIM 2024, STARD-AI, DECIDE-AI, and the items that matter most here

### Takeaway
CLAIM 2024 is the best fit. Its Item 20 says image sets "generally should be disjoint at the patient level or higher". Add TRIPOD+AI and a REFORMS or model-info-sheet supplement for leakage.

The items that matter most here are:
- partitioning and the level at which partitions are disjoint (CLAIM 19, 20 and 2; TRIPOD+AI 12a and Box 1);
- uncertainty (CLAIM 29; TRIPOD+AI 23a);
- sample size justification (TRIPOD+AI 10), filled with the MDE;
- calibration (TRIPOD+AI 12e);
- heterogeneity across patients (TRIPOD+AI 12d and 23b);
- external validation (CLAIM 33): state "none";
- protocol and registration (CLAIM 42; TRIPOD+AI 18c and 18d).

DECIDE-AI does not apply. STARD-AI applies only in part.

### Cited Findings
**TRIPOD+AI** ([Collins et al. 2024, BMJ 385:e078378](https://doi.org/10.1136/bmj-2023-078378))
- 27 main items with 52 subitems.
- 5a: data sources, given separately for development and evaluation.
- 10: how the study size was reached, and that it was "sufficient to answer the research question".
- 12a: how data were used, "including whether the data were partitioned".
- 12c: "all model building steps, including any hyperparameter tuning, and method for internal validation".
- 12d: heterogeneity in performance across clusters.
- 12e: "all measures and plots used (and their rationale) to evaluate model performance", including discrimination, calibration and clinical utility.
- 14: fairness.
- 16: "Identify any differences between the development and evaluation data".
- 18c: protocol. 18d: registration. 18e: data. 18f: code.
- 23a: "Report model performance estimates with confidence intervals".
- 23b: heterogeneity across clusters.
- 26: limitations, including statistical uncertainty and generalisability.
- Box 1: evaluation data "should be distinct from the data used to train the model", with "no overlap in participants".

**CLAIM 2024** ([Tejani et al. 2024, Radiol Artif Intell 6:e240300](https://doi.org/10.1148/ryai.240300))
- 44 items.
- Item 2 (abstract): give "data partitions and level of data splitting (eg, patient- or image-level)".
- Item 19: "Specify how data were partitioned for training, model optimization … and testing".
- Item 20: "Describe the level at which the partitions are disjoint (eg, patient-, series-, image-level)". It adds that sets "generally should be disjoint at the patient level or higher" so that "images of the same patient do not appear in more than one partition".
- Item 29: uncertainty "with standard deviation and/or confidence intervals".
- Item 30: robustness or sensitivity analysis.
- Item 33: "Describe the external data used to evaluate the completed algorithm".
- Item 34: clinical trial registration.
- Item 39: "Failure analysis of incorrect results".
- Item 42: reference to the full study protocol.
- Item 43: availability of software, trained model and/or data. Code should go to a public repository.

**STARD-AI** ([Sounderajah et al. 2025, Nat Med 31:3283–3289](https://doi.org/10.1038/s41591-025-03953-8); [EQUATOR listing](https://www.equator-network.org/reporting-guidelines/the-stard-ai-reporting-guideline-for-diagnostic-accuracy-studies-using-artificial-intelligence/); [protocol, BMJ Open 2021](https://bmjopen.bmj.com/content/11/6/e047709))
- Built by consensus of more than 240 stakeholders.
- Adds 18 new or modified items to STARD 2015.
- Emphasises dataset practices, the AI index test and how it was evaluated, and algorithmic bias and fairness.

**DECIDE-AI** ([Vasey et al. 2022, BMJ 377:e070904](https://doi.org/10.1136/bmj-2022-070904))
- Covers "the early stage clinical evaluation of decision support systems driven by artificial intelligence", meaning live clinical use.

**Leakage-specific tools**
- REFORMS has 32 questions, each paired with a guideline, from a consensus of 19 researchers. It targets validity, reproducibility and generalisability in ML-based science. [Kapoor et al. 2024, Sci Adv 10:eadk3452](https://doi.org/10.1126/sciadv.adk3452)
- Kapoor & Narayanan's "model info sheets" are a template of "21 questions that elicit precise arguments needed to justify the absence of leakage". They "can be included as supplementary materials". [Kapoor & Narayanan 2023, Patterns](https://doi.org/10.1016/j.patter.2023.100804)

**Calibration**
- Calibration is a core part of model validity that is often ignored. [Van Calster et al. 2019, BMC Med 17:230](https://doi.org/10.1186/s12916-019-1466-7) (not fetched)

### Inferences
**Priority table for the report**

| Issue | Items | Concrete action |
|---|---|---|
| Patient-level split and leakage | CLAIM 2, 19, 20; TRIPOD+AI 12a, Box 1; Kapoor L3.2 | Say in the abstract and methods that A0 and A3 are disjoint only at image level, so they estimate performance on new cells of already-seen patients. Say A1 and A2 are patient-disjoint (160/40). Name the grouping key, and check it against NIH's patientid_cellmapping CSVs (see Q5). Attach a model info sheet. |
| Uncertainty | CLAIM 29; TRIPOD+AI 23a | Report the patient-cluster bootstrap 95 % CIs, the equivalence 90 % CIs from Q1, and fold SDs. |
| Sample size | TRIPOD+AI 10 | Add the MDE statement and the design-effect explanation from Q2. |
| Heterogeneity | TRIPOD+AI 12d, 23b; CLAIM 30 | Give the per-patient performance spread and the finding that the 40 hold-out patients were easier. Report seeds, or better, repeated grouped hold-outs. |
| Calibration | TRIPOD+AI 12e | Add a reliability diagram and ECE or calibration slope and intercept for the averaged ensemble probabilities on the hold-out. Calibration is often skipped in malaria cell papers. |
| External validation | CLAIM 33; TRIPOD+AI 5a, 16, 26 | Write "No external validation": all data come from one hospital (Chittagong) per [Rajaraman 2018](https://doi.org/10.7717/peerj.4568). **Do not call the 40-patient hold-out "external".** It is internal, patient-disjoint validation. |
| Failure analysis | CLAIM 39 | Show misclassified cells, and check for label noise, which another notes file covers. |
| Pre-registration | CLAIM 42; TRIPOD+AI 18c, 18d | Cite the GitHub commit hash and timestamp of the analysis plan. List every deviation, including the post hoc equivalence tests. A Git commit is timestamped but not a formal registry; say so. |
| Code, data and model | CLAIM 43; TRIPOD+AI 18e, 18f | Link the repository and the model release, and state the NIH data licence. |
| Clinical-stage guidelines | DECIDE-AI | State "not applicable: no clinical deployment". |
| Diagnostic accuracy | STARD-AI | Apply in part. This is a cell-level technical evaluation against cell labels, not a patient-level diagnostic accuracy study. |

### Gaps
- I did not retrieve STARD-AI's item-level wording; only the summary from EQUATOR and the search results.
- I did not confirm whether CLAIM 2024 has a calibration item.
- TRIPOD+AI is written for clinical prediction models. Applying it to a cell classifier is my interpretation.
- I did not fetch Van Calster 2019.

## Q4. The value of negative results, pre-registration and patient-level splits in ML and medical imaging: quotable statements

### Takeaway
The literature supports the team's framing on three points. Publication bias toward positive results and leakage both inflate results in ML for medical imaging. Pre-registration and registered reports are recommended remedies. Patient-level separation is the expected default. The quotes below are verified and ready to cite.

### Cited Findings
**Varoquaux & Cheplygina 2022** ([npj Digital Medicine](https://doi.org/10.1038/s41746-022-00592-y))
- "positive results, some due to experimental flukes, are more likely to be published than corresponding negative findings"
- "Methods publication are selected for their novelty."
- "It is then all too appealing to find after-the-fact theoretical justifications of positive yet fragile empirical findings."
- "Popularizing different types of publications may help, for example publishing negative results"
- "Preregistration or registered reports can bring more robustness and trust", because "the motivation and experimental setup of a paper are to be reviewed before empirical results are available"
- "the lack of statistically significant results does not demonstrate the absence of effect"
- "any trivial effect can be significant given enough data"
- On leakage: one example is that "repeated measures of an individual are split across train and test set". Their remedy: "Safeguarding from data leakage by separating out all test data from the start, before any data transformation."
- From their Kaggle analysis: "the gains made by the top 10% of methods are smaller than the expected noise when evaluating a method". In 5 of 8 challenges, "the evaluation noise is worse than the winner gap".

**Roberts et al. 2021** ([Nat Mach Intell 3:199–217](https://doi.org/10.1038/s42256-021-00307-0))
- They screened 2,212 studies; 415 passed initial screening and 62 were included after quality screening. The arXiv v4 says 61 ([arXiv:2008.06388](https://arxiv.org/abs/2008.06388)).
- Conclusion: "none of the models identified are of potential clinical use due to methodological flaws and/or underlying biases".

**Kapoor & Narayanan 2023** ([Patterns](https://doi.org/10.1016/j.patter.2023.100804))
- "we find 17 fields where leakage has been found, collectively affecting 294 papers". The 2022 arXiv preprint said 329 ([arXiv:2207.07048](https://arxiv.org/abs/2207.07048)); cite the journal figure.
- Taxonomy item [L3.2] "Nonindependence between training and test samples": "In the extreme (but unfortunately common) case, training and test samples come from the same people or units." They cite a histopathology example that "uses different observations of the same patient in the training and test sets".
- Caveat: non-independence is not leakage if the claim is about a population with the same dependence structure.
- "leakage usually leads to inflated estimates of model performance"
- "a cautionary note against taking results in ML-based science at face value"

**Saeb et al. 2017** ([GigaScience 6(5):1–9](https://doi.org/10.1093/gigascience/gix019))
- "record-wise CV often massively overestimates the prediction accuracy of the algorithms"
- Nearly half of the wearable and smartphone studies they reviewed used record-wise CV.
- A published commentary from reviewers and authors debates when each CV scheme is appropriate. [Little et al. 2017, GigaScience 6(5):1–6](https://doi.org/10.1093/gigascience/gix020)

**Size of leakage effects in medical imaging**
- Brain MRI: splitting at slice level instead of subject level inflated accuracy by 29–55 % across four datasets. With random labels, a slice-level split gave about 96 % accuracy versus 50 % for a subject-level split. [Yagis et al. 2021, Sci Rep 11:22544](https://doi.org/10.1038/s41598-021-01681-w)
- OCT: improper splitting inflated MCC by 0.07–0.43 and accuracy by 5–30 %. [Tampu, Eklund & Haj-Hosseini 2022, Sci Data 9:580](https://doi.org/10.1038/s41597-022-01618-6)

**Benchmark variance** ([Bouthillier et al. 2021](https://arxiv.org/abs/2103.03098))
- Variance in benchmarks "is on the order of magnitude of the individual increments" reported on paperswithcode.

**Venues for negative results and pre-registration**
- ICBINB workshop, NeurIPS 2020 ([site](https://i-cant-believe-its-not-better.github.io/neurips2020)):
  - "We aim to create an open-minded and diverse space for researchers to share unexpected or negative results"
  - "This workshop will stress the quality and thoroughness of the scientific procedure"
  - "We also welcome work that highlights pathologies or unexpected behaviors in well-established practices."
- Later ICBINB editions: [NeurIPS 2022](https://sites.google.com/view/icbinb-2022/), [NeurIPS 2023 "Failure Modes in the Age of Foundation Models"](https://sites.google.com/view/icbinb-2023/submit), and [ICLR 2025 "Challenges in Applied Deep Learning"](https://lists.cnsorg.org/hyperkitty/list/comp-neuro@lists.cnsorg.org/thread/VVETGKHYB5WTIZUST3INQZEG7ZLIVZ2A/). The ICLR 2025 call asked for negative results and failed experiments.
- ML Pre-registration Workshop, third edition at NeurIPS 2021, with full papers in PMLR ([site](https://preregister.science/)):
  - "Some results will be negative, and this is welcomed."
  - "Papers are evaluated on the basis of scientific interest, not whether they achieve the best results."
  - "reviewers can be tempted to prioritise incremental improvements in benchmarks"
  - "good ideas that do not work will get published, instead of filed away"

### Inferences
**Framing paragraph the team could adapt**
> "Because positive results are preferentially published (Varoquaux & Cheplygina 2022) and leakage through non-independent train/test samples is a documented cause of inflated performance across 17 fields (Kapoor & Narayanan 2023), we fixed our hypotheses, metrics and tests in a timestamped analysis plan before training. Two of three pre-registered hypotheses were not supported. We report them in full, as pre-registration proponents in ML recommend ('Some results will be negative, and this is welcomed'). We use equivalence tests and minimum detectable effects to say what the data rule out, not only what they fail to show."

**Using these sources honestly**
- Contrast the team's result with the MRI and OCT literature. Leakage there inflated accuracy by 5–55 %; here the effect is about 1 pp. That is consistent with Kapoor's point that how large leakage is depends on how much patient identity carries label information.
- The literature does **not** say that leakage is always large. Overstating that would contradict the team's own data.

### Gaps
- The descriptions of the 2022, 2023 and ICLR 2025 ICBINB calls come from search snippets. The phrase "slow science" against "leaderboard-ism" was not verified on a primary page.
- I did not verify the PMLR volume number for the pre-registration workshop.
- I did not find a medical-imaging journal that formally offers Registered Reports for ML papers.

## Q5. Prior work on leakage and patient-level splits in malaria cell datasets, and how the team's effect compares

### Takeaway
The team's fold-level leakage estimate is −1.65 pp MCC, about −0.8 pp accuracy. That is almost the same as the most comparable within-study estimate:
- Hou et al. (2026) found slide-disjoint accuracy drops of 0.25–1.45 pp, mean about 0.82 pp, across eight architectures.
- For EfficientNet-B0 the drop was 0.47 pp.

The team's estimate is about a third of the 2.7 pp accuracy gap in Rajaraman et al. (2018). Positioning: "small but non-zero leakage on NIH single-cell images, an order of magnitude below MRI and OCT".

One methodological check is critical. The NIH datasheet lists 193 patients and provides official patient-ID mapping CSVs. The grouping key the team used must match those CSVs.

### Cited Findings
**NIH dataset and the original patient-level papers**
- Rajaraman et al. 2018 ([PeerJ 6:e4568](https://doi.org/10.7717/peerj.4568)):
  - Data: 150 *P. falciparum*-infected and 50 healthy patients, photographed at Chittagong Medical College Hospital; 27,558 cells, 13,779 per class.
  - They state: "Cross-validation has been performed at the patient level" (5 folds).
  - ResNet-50 at patient level: accuracy 0.959 ± 0.008, MCC 0.917 ± 0.017.
  - Cell level (Table 6): accuracy 0.986, MCC 0.972.
  - They attribute the patient-level shortfall to "staining variations between patients".
- Rajaraman, Jaeger & Antani 2019 ([PeerJ 7:e6977](https://doi.org/10.7717/peerj.6977)):
  - "We performed cross-validation at the patient level and ensured preventing data leakage into the validation", "so that the test data represents truly unseen images".
  - Earlier studies "were evaluated at the cell level, with randomized splits and/or small-scale datasets".
  - Best patient-level ensemble (VGG-19 + SqueezeNet): accuracy 99.51 ± 0.1, MCC 99.0 ± 0.2.
  - The paper does not describe how patients were mapped to folds.

**Later papers on this dataset that did not split by patient**
- Fuhad et al. 2020 ([Diagnostics 10(5):329](https://doi.org/10.3390/diagnostics10050329)):
  - Split 80:10:10 with no mention of patients; reported 99.23 % accuracy.
  - Reported that "some of the data are genuinely mislabeled". They set aside 647 parasitized and 750 uninfected suspicious images, going from 27,558 to 26,161 images.
- Marques et al. 2022 ([Multimed Tools Appl](https://doi.org/10.1007/s11042-022-12624-6)): cell-level stratified 10-fold CV plus a 5,512-image validation set, with no patient-level split.

**2026 re-evaluations**
- Hou et al. 2026, "MalariaNet" ([Biosensors 16(7):358](https://doi.org/10.3390/bios16070358)):
  - Grouping: by the filename "C" number, called a clinic or case identifier. "Grouping by this C number yields 200 unique groups covering all 27,558 cells". The finer slide token parses only 86.5 % of file names.
  - Splits: random per-cell 70/15/15 versus GroupShuffleSplit at about 140/30/30 slides, with 3 seeds.
  - Accuracy drops, per-cell → slide-disjoint:

    | Model | Per-cell | Slide-disjoint | Drop |
    |---|---|---|---|
    | MalariaNet | 97.06 | 95.61 ± 1.02 | −1.45 |
    | ShuffleNetV2 | 97.58 | 96.56 | −1.02 |
    | MobileNetV3-S | — | — | −1.24 |
    | EfficientNet-B0 | 97.22 | 96.75 ± 0.60 | −0.47 |
    | MobileNetV2 | — | — | −0.39 |
    | ResNet-18 | — | — | −0.25 |
    | Tiny-MobileNetV2 | — | — | −0.86 |
    | SingleStream | — | — | −0.91 |

  - The mean drop is ≈0.82 pp; I computed this from their Table 2.
  - Their judgement: "This 1.45 pp fall is, itself, within the ±1.02 seed standard deviation". They also call "the 'compact model matches large models' narrative … a leakage artefact", because the top-ranked model changed.
  - "To the best of our knowledge, no prior work has quantified how much slide leakage inflates results on this widely used … benchmark."
- Al Kafi et al. 2026, EMFE (preprint, not peer-reviewed) ([arXiv:2608.24793](https://arxiv.org/abs/2608.24793)):
  - 200 patients: 150 infected, whose slides contain both classes, and 50 uninfected-only.
  - "Every image's filename-embedded patient token was independently cross-checked against the official mapping and agreed in all 27,558 cases".
  - Patient-grouped random forest: accuracy 0.9463 in 20-fold out-of-fold estimates; 0.9429 on the hold-out.
- Dehbi et al. 2026 ([Front Med 13, 10.3389/fmed.2026.1911275](https://doi.org/10.3389/fmed.2026.1911275)) say the opposite: "The public release does not provide patient identifiers", and "a reliable grouping identifier is unavailable". They used an image-level split and do not claim patient independence.
- The NIH/LHNCBC datasheet lists "CSV files for Patient-ID to cell mappings": `patientid_cellmapping_parasitized.csv` and `patientid_cellmapping_uninfected.csv`. It also states "193 patients (148 infected + 45 uninfected patients)". [LHNCBC malaria datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)

**Patient-level field evaluation (a different setting)**
- Yu et al. 2023 ([Malaria J 22:33](https://doi.org/10.1186/s12936-023-04446-0)) evaluated a smartphone app on 190 patients in Sudan.
  - Malaria Screener reached 71.8 % accuracy against PCR, or 91.8 % with a different post-study patient-level calculation.
  - PlasmodiumVF-Net reached 83.1 % against expert microscopy.
  - Benchmark cell accuracy does not translate directly into patient-level diagnostic accuracy.

### Inferences
**Comparison table** (MCC ≈ 2 × accuracy differences; conversions are approximate)

| Study | Split comparison | Accuracy drop (pp) | MCC drop (pp) |
|---|---|---|---|
| **This team (A0 vs A1 folds)** | 10-fold random-image vs 10-fold patient-grouped, EfficientNet-B0 | ≈0.8 | **1.65** (fragile: NB-adjusted p ≈ 0.05) |
| This team (hold-outs, H1) | Different hold-outs, unpaired | −0.8 (patient split higher) | −1.62, confounded, MDE 2.2 |
| Hou et al. 2026 | Per-cell vs slide-disjoint, 8 architectures | 0.25–1.45 (mean 0.82); EfficientNet-B0 0.47 | ≈0.5–2.9 (EfficientNet-B0 ≈0.9) |
| Rajaraman et al. 2018 | Cell-level vs patient-level CV | 2.7 (98.6 → 95.9) | 5.5 (97.2 → 91.7) |
| Rajaraman et al. 2019 | Patient-level only | — (patient-level ensemble 99.5 %) | — |
| Yagis 2021 (MRI); Tampu 2022 (OCT) | Slice- or image-level vs subject-level | 29–55; 5–30 | OCT 7–43 |

- **Positioning sentence:**
  > "Our fold-level estimate of the patient-leakage effect (≈1.65 pp MCC, ≈0.8 pp accuracy) matches the slide-disjoint re-evaluation of Hou et al. (2026; 0.25–1.45 pp accuracy across eight architectures, 0.47 pp for EfficientNet-B0). It is about a third of the cell- vs patient-level gap reported by Rajaraman et al. (2018), and one to two orders of magnitude smaller than leakage effects in slice-level MRI or OCT. On NIH single-cell images the label is visible in the cell itself, so patient identity adds little exploitable signal. Leakage mainly makes random-split estimates look more certain than they are: our fold SD rose 2.5× under patient grouping."
- **What the team adds.** It is a pre-registered, MCC-based, patient-cluster-bootstrapped estimate with explicit equivalence bounds and MDEs. It also tests stain normalisation under a patient split, which matters because Rajaraman 2018 blamed the patient-level drop on staining variation. Hou et al. state that no prior work had quantified slide leakage on this benchmark, so an independent estimate from a different pipeline has replication value.
- **Why Rajaraman 2018's gap may be larger.** It compares different evaluation protocols with 5 folds of about 40 patients each, using older feature-extraction pipelines. The 2019 patient-level results (99.5 %) from the same group show that training choices can outweigh the effect of the split.
- **Critical check before submission: the grouping key.**
  - If the team grouped by the filename C-number (200 groups) but the official CSVs map cells to 193 patients, a few patients may have several C-numbers. Those patients could then appear in both training and hold-out, leaving residual leakage in A1 and A2.
  - Verify against `patientid_cellmapping_*.csv` and report the result under CLAIM Item 20.
  - EMFE reports perfect agreement between filename tokens and the official mapping. That is a preprint and needs independent confirmation.
- **Overreach to avoid:**
  - "No leakage exists in NIH malaria data."
  - "Prior cell-level results are invalid." The effect is about 1 pp, comparable to seed noise.
  - Citing EMFE's "Yu et al." figure (see Gaps).

### Gaps
- **Unverifiable claim; do not cite.** EMFE (arXiv:2608.24793) says "Yu et al. reported a larger drop, from 96.90% accuracy under cell-level evaluation to 78.00%". It cites "H. Yu et al. 2020, IEEE Access 8, pp. 12345–12356". A targeted search found no such paper. The page range looks like a placeholder, so the reference may be fabricated. The closest real Yu et al. paper (Malaria J 2023) is a field study with different numbers.
- **Patient count conflict.** The PeerJ papers, Hou et al. and EMFE say 200 patients (150 + 50). The LHNCBC datasheet says 193 (148 + 45). I could not resolve this without the CSVs.
- **Conflict on patient IDs.** Dehbi et al. 2026 say no patient IDs exist, which conflicts with the CSV listing on the NIH page.
- **Missing details in older papers.** Rajaraman 2019 does not describe how patients were assigned to folds. Fuhad et al. do not state whether results used corrected labels, and their label audit has not been independently confirmed.
- **No paired estimate yet.** I found no peer-reviewed study that estimates the leakage effect on this dataset with a paired, same-test-set design. The team's paired-design suggestion (Q2) would be new.
- **Possibly incomplete search.** I may have missed other 2021–2026 re-evaluations in IEEE or PLOS ONE. Several hits were preprints or non-peer-reviewed repositories.
