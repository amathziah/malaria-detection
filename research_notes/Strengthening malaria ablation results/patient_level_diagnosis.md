# Patient-level (slide-level) diagnosis from cell-level malaria classifiers on the NIH "Malaria Cell Images" dataset

Notes compiled 2 Nov 2026. Figures marked **computed here** were calculated by the researcher from NIH's own `patientid_cellmapping_parasitized.csv` / `patientid_cellmapping_uninfected.csv`. NLM distributes these files with the dataset ([NLM malaria datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)); a local copy is in `/Users/madhav/malaria-detection/outputs/data/nih_patient_mapping/`. Patients are grouped by the `C<n>` prefix. The confidence intervals computed here use the standard Clopper–Pearson and Wilson formulas.

---

## Q1. How do malaria ML papers turn cell/object predictions into a patient (slide) diagnosis, and what patient-level performance did they report?

### Takeaway
On the 27,558-cell NIH dataset I found exactly one published per-patient diagnosis analysis. EMFE (arXiv, Aug 2026) swept a "≥ τ predicted-positive cells" rule **post hoc** over all 200 patients. "Any positive cell" gave 14 % specificity; τ = 10 gave 100 % specificity at 87.3 % sensitivity. Every older "patient-level" number on these data (Rajaraman 2018/2019; the thin-smear row of Malaria Screener 2020) is a **cell-classification metric under patient-grouped cross-validation**, not a per-patient diagnosis. On NLM's thick-smear patient sets and in field systems, the rules are:
- count rules (parasites per image or slide, majority of images);
- FP-floor-corrected parasitaemia estimates;
- mean-score thresholds.

Patient-level **specificity** is the recurring failure point. Mean-score and early rules reached only about 50–80 %. Count and FP-floor rules tuned for it reach about 90 %.

### Cited Findings

**A. Work on the NIH 27,558-cell dataset (same 150 + 50 Chittagong patients)**
- **Rajaraman et al. 2018 (dataset paper):**
  - Used 5-fold cross-validation "at the patient level". Under it, ResNet-50 features scored accuracy 0.959, AUC 0.991, sensitivity 0.947, specificity 0.972, F1 0.959, MCC 0.917 (Table 4).
  - Table 6 labels these values "patient level". The cell-level (random-split) row is 0.986 accuracy, 0.981 sensitivity, 0.992 specificity, 0.999 AUC.
  - The authors attribute the gap to "staining variations between patients".
  - The paper does not aggregate cells into a per-patient diagnosis.
  - [Rajaraman et al. 2018, PeerJ 6:e4568](https://doi.org/10.7717/peerj.4568) (full text via [Europe PMC PMC5907772](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5907772/fullTextXML))
- **Malaria Screener (Yu et al. 2020), thin-smear Table 2:** a "Patient" row of accuracy 95.9 %, AUC 99.1 %, sensitivity 94.7 %, specificity 97.2 %, F1 95.9 %, and a "Patch" row of 98.6 / 99.9 / 98.1 / 99.2 / 98.7 %.
  - Both rows cite ref. [14], which is Rajaraman et al. 2018, and both are "mean performance on five folds".
  - The paper says "we could find no comparable literature that performed cross-validation studies on patient-level".
  - The app itself counts infected and total RBCs per image, keeping a running total until a user-set RBC maximum. No thin-smear patient decision rule is published.
  - [Yu et al. 2020, BMC Infect Dis](https://doi.org/10.1186/s12879-020-05453-1) ([PMC7656677](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7656677/fullTextXML))
- **Rajaraman, Jaeger & Antani 2019 (ensembles):**
  - Report "cross-validation studies … at the patient level to ensure preventing data leakage". Ensemble-D (VGG-19 + SqueezeNet) scored accuracy 99.51 ± 0.1 % and AUC 99.92 %.
  - The comparison table lists Rajaraman 2018 "patient level" as accuracy 95.9 / AUC 99.1 / MCC 91.7.
  - No per-patient aggregation.
  - [Rajaraman et al. 2019, PeerJ 7:e6977](https://doi.org/10.7717/peerj.6977) ([PMC6544011](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6544011/fullTextXML))
- **EMFE (Al Kafi et al., arXiv Aug 2026), the closest precedent to the team's plan:**
  - Design: a classical-feature classifier with patient-grouped nested CV (K_outer = 20). Pooled accuracy was 94.6 %, and an untouched 40-patient hold-out (160 / 40 patients, 21,915 / 5,643 cells) scored 94.3 % with patient-cluster-bootstrap CIs.
  - Aggregation: post hoc on the out-of-fold predictions of **all 200 patients**. Rule: "call a patient infected if at least τ of their cells are predicted Parasitized", τ ∈ {1, 2, 3, 5, 10, 20}, with Wilson CIs.
  - Results (Table 14):

    | τ | Sensitivity | Specificity |
    |---|---|---|
    | 1 | 150/150 (1.000) | 7/50 (0.140) |
    | 2 | 149/150 | 0.380 |
    | 3 | 148/150 (0.987) | 32/50 (0.640) |
    | 5 | 144/150 (0.960) | 43/50 (0.860) |
    | 10 | 131/150 (0.873) | 50/50 (1.000, Wilson 0.929–1.000) |
    | 20 | 95/150 (0.633) | 1.000 |

  - Per-cell specificity was 0.959, and controls average 68.3 cells. Independence ("compounding") predicts 94 % of controls with ≥ 1 FP cell; 86 % (43/50) was observed.
  - At τ = 3, sensitivity in the lowest "true parasitemia" quartile (mean 8.6 % of the patient's cells parasitized) was 94.7 %, against 100 % in the higher quartiles.
  - The authors call it "a retrospective, post hoc characterization … not a validated clinical decision rule".
  - [Al Kafi et al. 2026, arXiv:2608.24793](https://arxiv.org/abs/2608.24793)
- **MalariaNet (Biosensors 2026):**
  - Slide-disjoint 70/15/15 split by C-number (200 groups).
  - All eight architectures lost accuracy against per-cell random splits, by 0.25–1.45 pp.
  - Reports cell-level metrics only, e.g. sensitivity 93.94 % / specificity 97.41 % for MalariaNet under the slide-disjoint split.
  - [Hou et al. 2026, Biosensors 16:358](https://doi.org/10.3390/bios16070358) ([PMC13406217](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13406217/fullTextXML))

**B. NLM thick-smear patient-level work (same hospital, Chittagong Medical College Hospital)**
- **Yang et al. 2019 (MLMI), thick smears, 150 infected + 50 normal patients, 5-fold CV:**
  - Patch level: accuracy 96.89 %, AUC 98.48 %, sensitivity 90.82 %, specificity 97.43 %.
  - **Patient level: accuracy 78.00 %, AUC 84.90 %, sensitivity 79.33 %, specificity 74.00 %, precision 90.42 %.**
  - Reproduced as Malaria Screener Table 1 (2,967 images: 1,819 infected + 1,148 normal). [Yu et al. 2020](https://doi.org/10.1186/s12879-020-05453-1); [Yang et al. 2019 record](https://repository.li.mahidol.ac.th/handle/123456789/50691)
  - EMFE describes this drop (96.9 → 78.0 %) as "cell-level evaluation to … patient-grouped evaluation" ([arXiv:2608.24793](https://arxiv.org/abs/2608.24793)). In fact it is thick-smear **patch-level classification vs patient-level diagnosis**, both under 5-fold CV ([Yu et al. 2020](https://doi.org/10.1186/s12879-020-05453-1)).
- **Yang et al. 2020 (IEEE JBHI):**
  - Pipeline: IGMS candidate screening plus a CNN on 1,819 thick-smear images from 150 *P. falciparum* patients.
  - Under "patient-level five-fold cross-evaluation", accuracy was 93.46 %. The correlation between detected and true parasite counts was > 0.98 at image and patient level (abstract, via search).
  - The NLM datasheet lists this set as 150 infected / 0 uninfected, so no patient-level specificity was possible.
  - [Yang et al. 2020, doi:10.1109/JBHI.2019.2939121](https://doi.org/10.1109/JBHI.2019.2939121); [PMC12077747](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12077747/); [NLM datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)
- **Kassim et al. 2021 (PlasmodiumVF-Net), 350 patients (150 Pf, 150 Pv, 50 uninfected; 5,972 images):**
  - Rule: an image is "uninfected" if fewer than **2** parasites survive filtering. A patient is uninfected if **more than half** of their images are uninfected; otherwise species is decided by the higher average per-image score.
  - The threshold was chosen from histograms of detections in normal patients; zero parasites was "too stringent".
  - Final three-class patient-level accuracy was 92.3 %, image-level 83.9 %, under 5-fold CV on patient level.
  - [Kassim et al. 2021, Diagnostics 11:1994](https://doi.org/10.3390/diagnostics11111994) ([PMC8621537](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8621537/fullTextXML))
- **Yu et al. 2023, Sudan field study (190 patients, thick smears, expert microscopy and PCR references):**
  - Malaria Screener's primary rule: image score = mean of candidate probabilities, and patient score = mean of image scores, positive above a threshold tuned on one site's slides. Against microscopy (n = 85) it gave **sensitivity 100 % (91.2–100), specificity 51.1 % (35.8–66.3)**, accuracy 74.1 %.
  - A **post-study** count rule ("if the number of parasite candidates … exceeded the threshold, the patient was considered positive") gave sensitivity 92.5 % (79.6–98.4), specificity 91.1 % (78.8–97.5), accuracy 91.8 %.
  - PVF-Net: sensitivity 86.9 %, specificity 78.9 %, accuracy 83.1 % (n = 189).
  - The authors mapped 74.1 / 91.8 / 83.1 % accuracy to WHO Levels 3 / 1 / 2.
  - Mean scoring "ignored the number of parasite candidates", and artifacts "caused false detections that led to negative patients being diagnosed as positive".
  - [Yu et al. 2023, Malar J 22:33](https://doi.org/10.1186/s12936-023-04446-0) ([PMC9883923](https://pmc.ncbi.nlm.nih.gov/articles/PMC9883923/))

**C. Other slide-level systems whose aggregation rules are worth copying**
- **Delahunt et al. (thin films; 798 image sets, 765 patients, > 12 countries):** patient parasitaemia is estimated with a false-positive floor and a sensitivity correction:
  - P̂ = (n_R · 5×10⁶/n_RBC − f̂p) / ŝ, with t, ŝ and f̂p "determined on a validation set (f̂p uses negative samples only)".
  - The scanner collects fields until **20k single RBCs** are tallied ("a human microscopist examines 5k RBCs").
  - The diagnosis operating point (mean FP rate of 1.6k per µL) "gives 90 % sample-level specificity on holdout sets … a requirement based on the 'WHO 56' evaluation method". Rough µ(fp) proxies for prior methods ranged 5k–70k per µL.
  - "Object-level specificity and … AUC depend on the raw number of distractors … can be boosted arbitrarily by surplus easy distractors."
  - "Standard ML metrics such as ROC curves are insufficient to assess patient-level accuracy."
  - Objects from a blood sample must be in train or validation, "never in both".
  - [Delahunt et al., arXiv:1908.01901 (v2 2022)](https://arxiv.org/abs/1908.01901)
- **Autoscope (Peru, thick films, 700 participants, PCR reference):**
  - "Diagnosis thresholds … are pre-specified, using results on a set of validation samples, with the goal of achieving > 90 % specificity".
  - Slide-level sensitivity / specificity: 72 % / 85 % at one site and 52 % / 70 % at the other, with exact binomial CIs (epiR).
  - [Torres et al. 2018, Malar J](https://doi.org/10.1186/s12936-018-2493-0) ([PMC6157053](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6157053/fullTextXML))
- **EasyScan GO on a WHO 55-slide set:**
  - Detection 33/35 (94.3 %), specificity 20/20, sensitivity 13/15. Both false negatives were Pf slides at 112 and 175 p/µL.
  - This equals WHO Level 1 for detection. The slide-level disposition rule is not given numerically.
  - [Horning et al. 2021, Malar J](https://doi.org/10.1186/s12936-021-03631-3) ([PMC7905596](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7905596/fullTextXML))
- **Weakly supervised / MIL-style:**
  - DeepMCNN was trained on routine clinical-microscopy (slide-level) labels for thick films in Ibadan, Nigeria. Prospective validation gave **sensitivity / specificity 0.92 / 0.90** and PPV / NPV 0.92 / 0.90 ([Manescu et al. 2020, Am J Hematol](https://doi.org/10.1002/ajh.25827)).
  - MOFF (MICCAI 2020) fuses features from about 100 thick-film fields using sample-level labels, with max or average fusion and majority voting ([Manescu et al. 2020, LNCS 12265](https://doi.org/10.1007/978-3-030-59722-1_22); [code](https://github.com/UCL/FASt-MAL-MOFF)). Its reported 0.93 / 0.93 sensitivity / specificity comes only from a secondary review ([liner.com summary](https://liner.com/review/weakly-supervised-deep-learning-approach-for-detecting-malaria-and-sickle)) and is unverified.
  - MILCA (MIDL 2026) adds MIL with class-activation-map pseudo-labels ([PMLR v315](https://proceedings.mlr.press/v315/manescu26a.html)).

**D. Generic pooling theory**
- Standard MIL assumption: a bag (slide) is positive if at least one instance is positive ([Dietterich et al. 1997, Artif Intell 89:31–71](https://doi.org/10.1016/S0004-3702(96)00034-3)).
- Max-pooling MIL with slide-level labels on whole-slide images: [Campanella et al. 2019, Nat Med](https://doi.org/10.1038/s41591-019-0508-1).
- Learned attention pooling: [Ilse, Tomczak & Welling 2018, arXiv:1802.04712](https://arxiv.org/abs/1802.04712).
- The noisy-OR / independence prediction P(≥ 1 FP) = 1 − (1 − r)ⁿ overestimated control FP flags (94 % predicted vs 86 % observed) on NIH data. Errors are not independent across a patient's cells ([EMFE](https://arxiv.org/abs/2608.24793)).

### Inferences
- **Terminology trap.** In this literature "patient-level" usually means *patient-grouped evaluation of a cell classifier*, not *diagnosis of a patient*. The team's limitations slide should use distinct terms: "patient-disjoint cell-level evaluation" and "patient-level diagnosis (aggregation)".
- Comparing the team's 98.45 % hold-out cell accuracy with Malaria Screener's "patient-level 95.9 %" is apples to apples: both are cell metrics. Comparing it with the thick-smear "patient-level 78 %" is not, because that is a diagnosis on different slides.
- **Mapping the families onto this dataset:**
  - *Count* (R1 below) and *fraction* rules are nearly equivalent here, because every patient has about 68 uninfected crops plus k parasitized crops (see Q3).
  - *Mean probability* (Yu 2023 primary) is diluted. An infected patient with 3 parasitized crops has a mean p of about 3/71 ≈ 0.04, so the rule degenerates into a count rule with an awkward threshold.
  - *Noisy-OR* and *max* ("any positive cell") saturate on healthy patients (EMFE: 14 % specificity).
  - *Delahunt-style FP-floor subtraction* is the most principled rule that needs no training.
  - *Attention-MIL* would need new training and is out of scope.
- **Expected behaviour of the team's own rule (computed here, independence assumption):**
  - At t = 0.5, the per-crop FP rate is 31/2,735 = 1.13 %. A healthy patient with 68 crops then has 0.77 expected FP crops and a 54 % chance of ≥ 1. "Any positive cell" would give roughly 46 % specificity.
  - At t = 0.19 (FP 6.07 %), there are 4.1 expected FP crops per healthy patient and a 98.6 % chance of ≥ 1.
  - So t and τ must be chosen jointly. τ ≥ about 3 is likely needed at t = 0.5, and τ ≥ about 8–10 at t = 0.19.
  - Errors cluster by patient (half the team's errors come from 7 of 40 patients, as did EMFE's 94 % vs 86 % gap), so one artifact-rich healthy smear can defeat any small τ.
- A leak-free, pre-specified rule with an untouched hold-out would go beyond anything published on this dataset. EMFE selected τ on the same 200 patients it reports, and Yu 2023's best rule was post-study.

### Gaps
- No full text of the MLMI 2019 paper was retrieved, so its thick-smear patient decision rule is unconfirmed. Malaria Screener 2020 does not describe it either.
- The MOFF sample-level numbers are unverified (secondary source only).
- I found no malaria paper using a formal Bayesian (likelihood-ratio) patient rule or noisy-OR as the deployed rule. The Bayes-decision paper Delahunt cites (Anggraini 2011) was not retrieved.

---

## Q2. What patient-level performance is clinically needed? (WHO competence levels, detection limits, RBCs examined, typical parasitaemia, RDT benchmarks)

### Takeaway
The defensible benchmarks are:
- **Slide-level detection ≥ 90 %** (WHO Level 1 microscopist; the scored slide sets include negatives and low-density Pf).
- **Specificity ≥ 90 %** (Delahunt's WHO-56-derived requirement; WHO's RDT false-positive limit < 10 %).
- Detection at clinically relevant densities of about **100–200 parasites/µL** (WHO RDT panels at 200 p/µL).

A thin film examined at about 1,000–2,000 RBCs cannot reach those densities on Poisson grounds alone. The NIH crops carry no density labels, so the team **cannot claim** a limit of detection or a WHO competence level. They can only quote these benchmarks as context.

### Cited Findings
- **WHO competence levels** (Horning Table 1, from the WHO QA manual):
  - Detection and species ID: Level 1 ≥ 90 %, Level 2 80–< 90 %, Level 3 70–< 80 %, Level 4 < 70 %.
  - Quantitation (within 25 % of the reference count): ≥ 50 / 40–< 50 / 30–< 40 / < 30 %.
  - The final level is set by the lowest component.
  - The detection set ideally has "20 negative samples and 20 positive samples". In the set evaluated there, positives included 7 Pf slides below 200 p/µL.
  - [Horning et al. 2021](https://doi.org/10.1186/s12936-021-03631-3); [WHO Malaria microscopy quality assurance manual v2 (page dated 2015)](https://www.who.int/publications/i/item/9789241549394)
- A harmonisation proposal for clinical research adds a **false-positive limit of ≤ 2.5 % at Level 1** (≤ 5 % at L2, ≤ 10 % at L3). It is "adapted from the ReMMS manual", not WHO's own table ([Dhorda et al. 2020, Malar J](https://doi.org/10.1186/s12936-020-03352-z), [PMC7471592](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7471592/fullTextXML)).
- Delahunt et al. treat **90 % sample-level specificity** as "a requirement based on the 'WHO 56' evaluation method" ([arXiv:1908.01901](https://arxiv.org/abs/1908.01901)).
- **WHO RDT selection criteria** (when no prequalified test exists):
  - "at least a 75 % 'panel detection score' for low parasite density samples (200 p/µL)";
  - "a false positive rate of less than 10 %";
  - "fewer than 5 % invalid tests".
  - The panel detection score "is not the same as 'sensitivity'", which is measured on a real mix of densities.
  - [WHO GMP, RDT selection and procurement](https://www.who.int/teams/global-malaria-programme/case-management/diagnosis/rapid-diagnostic-tests/selection-and-procurement)
- **Clinically sufficient analytical sensitivity:** "100–200 parasites/µL appears sufficient in most cases of clinical *P. falciparum* infection" (citing WHO 2010). Screening tests target a minimum of < 20 p/µL and an optimum of ≤ 2 p/µL, and MalERA recommended ≤ 5 p/µL ([Bell et al. 2016, Malar J](https://doi.org/10.1186/s12936-016-1454-8), [PMC4981959](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4981959/fullTextXML)).
- **Detection limits and negative calls:**
  - Thick-film theoretical LoD is "3–4 parasites per µL", rarely achieved in practice.
  - "A minimum of 200 HPFs must be examined or 2500 WBCs counted on the thick film before declaring a slide negative."
  - Thin films are unsuitable for medium or low densities; matching thick-film LoD would need "hundreds of additional fields".
  - [Dhorda et al. 2020](https://doi.org/10.1186/s12936-020-03352-z)
- **Poisson requirement:** an LoD of 50 p/µL requires examining about 0.1 µL of blood. That is about 800 WBCs on a thick film, "or 5e5 Red Blood Cells (RBCs) on thin film, which is unworkable". Hence "thick film is used for diagnosis" ([Delahunt et al.](https://arxiv.org/abs/1908.01901)).
- **Field limits of detection:** about 100 p/µL for both microscopy and Autoscope at one Peruvian site; about 50 (microscopy) vs about 200 (Autoscope) at the other ([Torres et al. 2018](https://doi.org/10.1186/s12936-018-2493-0)).
- **RBCs examined on thin films:**
  - Parasites are counted against "2000 RBCs in the thin film" ([Dhorda et al. 2020](https://doi.org/10.1186/s12936-020-03352-z)).
  - "On thin film, microscopists typically count 1000 RBCs", while scanners count 10k–20k. The same paper elsewhere says "a human microscopist examines 5k RBCs", an internal inconsistency ([Delahunt et al.](https://arxiv.org/abs/1908.01901)).
  - An automated thin-film scan covered 150–192 fields and about 10,000–50,000 RBCs ([Horning et al. 2021](https://doi.org/10.1186/s12936-021-03631-3)).
- **When thin films are used for quantitation (sources disagree):**
  - above about 20 parasites/HPF or 0.3 % parasitaemia ([Dhorda](https://doi.org/10.1186/s12936-020-03352-z));
  - at about 8k–16k p/µL ([Delahunt](https://arxiv.org/abs/1908.01901));
  - at about 80,000 p/µL ([Horning](https://doi.org/10.1186/s12936-021-03631-3)).
- **Typical densities:**
  - In field thin films, parasites appear about "1 per 100 RBCs in high parasitemia cases, and more commonly fewer than 1 per 1000 RBCs" ([Delahunt](https://arxiv.org/abs/1908.01901)).
  - In Sudanese clinical patients (microscopy-positive Pf, Malaria Screener subset), 1/40 had < 1,000 p/µL, 16/40 had 1,000–10,000 and 23/40 had > 10,000 p/µL. In the PVF-Net subset, 8/99, 40/99 and 51/99 respectively. PVF-Net sensitivity was 50 % below 1,000 p/µL ([Yu et al. 2023](https://doi.org/10.1186/s12936-023-04446-0)).
  - Conversion: 5×10⁶ RBC/µL ([Delahunt Eq. 1](https://arxiv.org/abs/1908.01901)).
- **Hyperparasitaemia (severe malaria):** WHO now uses ≥ 10 % in all settings ([J Travel Med 2025, via search](https://academic.oup.com/jtm/article/8153893)). This is contradicted by a reproduction of the WHO 2021 table giving > 5 % for non-endemic countries ([ebm.one](https://ebm.one/en/node/2133)). Unresolved; I did not access the primary WHO text.
- **Real-world reference performance:**
  - Field microscopy vs PCR: sensitivity 68 % and 42 %, specificity 100 % and 97 % at the two Peruvian sites ([Torres et al. 2018](https://doi.org/10.1186/s12936-018-2493-0)).
  - Sudan microscopists vs PCR: 94.2 % accuracy. The first two microscopists agreed on species and parasitaemia in only 27 of 100 positive reads ([Yu et al. 2023](https://doi.org/10.1186/s12936-023-04446-0)).

### Inferences
- **Poisson ceiling for the NIH patients (computed here).** The imaged fields contain roughly 1,180 segmented objects per patient (median; see Q3). Even a *perfect* cell classifier would therefore see ≥ 1 infected RBC with probability:

  | Density | Expected infected RBCs | P(≥ 1 infected RBC) |
  |---|---|---|
  | 200 p/µL (WHO RDT panel) | 0.047 | 4.6 % |
  | 1,000 p/µL | 0.24 | 21 % |
  | 5,000 p/µL | 1.18 | 69 % |
  | 10,000 p/µL | 2.36 | 91 % |

  With a 5-field thin film, patient-level detection is only meaningful for moderately high densities. The dataset's infected patients were evidently such cases (Q3).
- **FP noise floor (computed here; rough).** Applied to every RBC on a slide, a per-crop FP rate of 1.13 % implies an apparent background of about 56,500 "parasites"/µL (0.0113 × 5×10⁶). At t = 0.19 it is about 303,000/µL.
  - Delahunt's diagnostic operating point is about 1,600 FP/µL (≈ 0.032 % of RBCs), roughly 35× lower than the team's t = 0.5 rate.
  - This holds only if NIH's uninfected crops are representative of all RBCs. They include "staining artifacts/impurities" (Q3), so the true per-RBC rate may differ.
- **What to quote as context.** Use "WHO Level 1 detection ≥ 90 %", "specificity ≥ 90 % (WHO-56-derived; RDT FPR < 10 %)" and "clinically relevant density ≈ 100–200 p/µL", and state explicitly that the NIH evaluation cannot test any of them. It has no densities, no low-density slides and no full-slide reads.
- Do **not** label the result "WHO Level 1". Yu 2023 did so from accuracy alone, after a post-study rule change.

### Gaps
- The WHO SOP for parasite counting (MM-SOP-09) and Wongsrichanalai et al. 2007 ([doi:10.4269/ajtmh.2007.77.119](https://doi.org/10.4269/ajtmh.2007.77.119)) could not be retrieved (403 / CAPTCHA). The exact WHO RBC count for thin films (1,000 vs 2,000 vs 5,000) is unconfirmed.
- I found no current WHO/FIND target product profile for *automated microscopy* with numeric sensitivity and specificity targets. MalERA-derived profiles in Bell 2016 give LoD targets only.
- The admission parasitaemias of the 150 Chittagong patients are not published with the dataset.

---

## Q3. Dataset caveats: how the NIH cell dataset was built, how many cells each patient contributes, and what must be disclosed

### Takeaway
The cell set is a **curated, enriched sample**, not a slide. All annotated parasitized cells appear to be kept, but only about **6 % of segmented cells** are retained as "uninfected" crops, giving about **68 per patient whatever the patient's status**. Patient-level detection on these crops is therefore much easier than on a real slide:
- a median infected patient contributes **33** parasitized crops (range 1–633);
- the healthy-patient FP exposure is only about 68 crops, against roughly 1,180 segmented cells per patient in the imaged fields.

These facts, plus the case–control design, single site, label provenance and C47 duplication, must be disclosed with any patient-level number.

### Cited Findings
- **Collection and labels:**
  - Giemsa thin smears from 150 Pf-infected and 50 healthy patients, photographed at Chittagong Medical College Hospital with a smartphone on a light microscope.
  - "manually annotated by an expert slide reader" at MORU, Bangkok.
  - Segmentation: a multi-scale Laplacian-of-Gaussian centroid detector, then a **level-set active contour** (Ersoy et al. 2012), then morphological opening. WBCs were removed using ground-truth annotations. Segmentation PPV was 0.944, sensitivity 0.962, F1 0.952.
  - Negatives "contain no Plasmodium but other types of objects including staining artifacts/impurities".
  - 13,779 crops per class. **How the uninfected class was balanced is not described.**
  - [Rajaraman et al. 2018](https://doi.org/10.7717/peerj.4568)
  - (The Malaria Screener app itself uses watershed segmentation: [Yu et al. 2020](https://doi.org/10.1186/s12879-020-05453-1).)
- **Rajaraman 2018 fold counts** (parasitized / uninfected): 2,756/2,757; 2,758/2,758; 2,776/2,762; 2,832/2,760; 2,657/2,742. The near-constant uninfected count (about 2,760 per 40-patient fold) is consistent with about 69 uninfected crops per patient ([Rajaraman et al. 2018](https://doi.org/10.7717/peerj.4568)).
- **NLM datasheet:**
  - Patient-to-cell mapping comes as two CSVs.
  - The *full-image* thin-smear Pf set lists **193 patients (148 infected, 45 uninfected)**, with annotations of uninfected and infected RBCs, gametocytes, WBCs, debris, stain precipitate, platelets and more.
  - Thick-smear sets: 150 Pf, 150 Pv, 50 uninfected.
  - [NLM datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)
- **Identifier parsing:** the leading `C<n>` number parses for 100 % of files and yields 200 groups. The `C<digits>P<digits>` token parses for only 86.5 % ([MalariaNet 2026](https://doi.org/10.3390/bios16070358)).
- **Per-patient counts** (computed here from the [NIH CSVs](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)):
  - **Totals:** 27,558 unique files (13,779 + 13,779); 201 CSV keys; **200 C-numbers** (150 infected, 50 healthy).
  - **C47 duplication:** C47 appears under two keys, `C47P8thinOriginalOlympusCX21` (65 uninfected crops) and `C47P8thin_Original_Motic` (69), i.e. two microscopes for one patient. It has 10 parasitized and 134 uninfected crops.
  - **Healthy-patient keys** lack the `P<m>` token (e.g. `C1_thinF`, `C2NThinF`, `C201ThinF`–`C241ThinF`).
  - **Parasitized crops per infected patient:** min 1, P10 6, Q1 13, **median 33**, mean 91.9, Q3 96, P90 282, max 633. 14/150 patients have ≤ 5, 33/150 have ≤ 10, 60/150 have ≤ 20, and 23 have ≥ 200.
  - **Uninfected crops per patient:**
    - infected patients: median 68, range 63–77 (excluding C47);
    - healthy patients: median 68, range 65–71, mean 68.3;
    - 10,364/13,779 (**75.2 %**) come from infected patients.
  - **Crop "parasite fraction" per infected patient:** min 0.014, **median 0.328**, max 0.902.
  - **Field images per patient:** infected median 7 (5–21); healthy median 5 (4–7); 1,408 images in total.
- **Index forensics** (computed here; filenames end `_cell_<index>.png`):
  - In **936/936** images that contain both classes, every parasitized crop's index exceeds every uninfected crop's index.
  - In **1,041/1,041** images with parasitized crops, those indices form one contiguous run.
  - Uninfected crops kept are a median **6.2 %** (IQR 5.5–7.0 %) of the indices preceding the first parasitized one, and 6.0 % in uninfected-only images.
  - A rough proxy for parasitized cells as a share of segmented cells per infected patient: **median 2.8 %** (IQR 1.0–8.3 %, P10 0.45 %, min 0.09 %, max 48 %).
  - Segmented objects per patient (sum of the max index per image): median about 1,180 (629–2,474).
- **Distractor caveat:** "object-level specificity and AUC … can be boosted arbitrarily by surplus easy distractors" ([Delahunt et al.](https://arxiv.org/abs/1908.01901)).
- The cell-level class balance makes accuracy and F1 nearly identical. Results were not translated to field prevalence ([MalariaNet 2026](https://doi.org/10.3390/bios16070358)).

### Inferences
- **Likely construction** (inference from the index pattern; not documented by NIH):
  - the automatic segmentation enumerated RBCs 1…k per image;
  - expert-annotated infected cells were appended as k+1…k+m;
  - a random-looking ~6 % subsample of the segmented cells was kept as "uninfected", balancing the classes at 13,779 each.
- **Consequences:**
  1. Infected patients are represented by (apparently) **all** their annotated parasitized cells, but healthy patients by about **6 % of their cells**. Patient-level sensitivity is inflated and the FP exposure behind patient-level specificity is deflated, by roughly 16×. If all ~1,180 segmented cells of a healthy patient were scored at a 1.13 % FP rate, about 13 FP cells would be expected, against 0.77 on 68 crops.
  2. The crop "parasite fraction" (median 33 %) is roughly 10× the proxy parasitaemia (median ~2.8 %). EMFE's "true parasitemia quartiles" are crop fractions, not clinical parasitaemia.
  3. **Label leakage through counts.** Total crops per patient (68 + k) and images per patient (7 vs 5) differ by status, so neither may be a feature or a denominator choice that adds information. Rules must use only per-crop predictions. The fraction K/n is acceptable but redundant.
  4. **Grouping must use the C-number.** Grouping by full CSV key would split C47 into two "patients". Check that C47's two keys fall in the same fold.
  5. **Case–control spectrum.** Hospital-diagnosed patients and healthy controls, 75 % prevalence, single site, one staining protocol, smartphone optics, *P. falciparum* only. PPV/NPV and accuracy do not transfer.
  6. **Reference standard.** The patient label is cohort membership (expert microscopy at MORU), with no PCR. Yu 2023 shows experts disagree and microscopy misses PCR-positive infections.
- **Disclosure checklist for any patient-level number:**
  - crops, not slides;
  - ~68 uninfected crops per patient regardless of status;
  - parasitized crops per infected patient: median 33, range 1–633;
  - unknown and undocumented crop selection (state the index-pattern inference);
  - no parasite density data;
  - 5–7 fields (about 1,000 cells) per patient;
  - case–control 150:50 cohort; single site; *P. falciparum* only;
  - uninfected class contains artifacts;
  - C47 two-microscope duplication;
  - the 200- vs 193-patient discrepancy with NLM's full-image set;
  - "not a diagnostic accuracy study of a device".
- **Realistic follow-up without retraining.** NLM's full-image thin-smear set, with RBC-level annotations, would allow scoring *all* segmented RBCs per patient at natural parasitaemia. It would need segmentation and inference only.

### Gaps
- NIH does not document how the uninfected crops were sampled, or whether *all* annotated parasitized cells were kept. The index-pattern interpretation is unconfirmed.
- The 7-patient discrepancy (200 patients in the cell set vs 193 in the full-image thin set) is unexplained.
- Whether `_cell_<index>` counts only RBCs or all segmented objects is unknown, so the 2.8 % parasitaemia proxy is approximate.

---

## Q4. A leak-free protocol: decision-rule search space, selection, statistics for ~40 patients, handling a false-positive healthy patient, and the reporting table

### Takeaway
1. Fix a small, pre-registered rule family. The primary is "positive if ≥ τ crops have p ≥ t".
2. Select (t, τ) only on the 160 CV patients' out-of-fold predictions, with a written criterion, and quantify selection optimism with a nested leave-one-fold-out.
3. Apply the rule **once** to the 40 hold-out patients.
4. Report exact (Clopper–Pearson) and Wilson CIs. With about 10 healthy hold-out patients, one false positive moves specificity to 90 % (CP 55.5–99.7 %), so the CV-nested estimate and a per-patient listing are essential companions.

### Cited Findings
- **Good practice to copy:**
  - thresholds "pre-specified, using results on a set of validation samples, with the goal of achieving > 90 % specificity", with exact binomial CIs ([Torres et al. 2018](https://doi.org/10.1186/s12936-018-2493-0));
  - hyperparameters and the FP floor "determined on a validation set", FP floor from negatives only ([Delahunt et al.](https://arxiv.org/abs/1908.01901)).
- **Practice to avoid or label:**
  - Yu 2023's count rule was a "post-study recalculation" that moved specificity from 51.1 % to 91.1 %. The paper does not say whether it was derived on independent data ([Yu et al. 2023](https://doi.org/10.1186/s12936-023-04446-0)).
  - EMFE swept τ on the same 200 patients it reports and labels this post hoc ([EMFE](https://arxiv.org/abs/2608.24793)).
- **Clustering:** an independence-assuming Wilson interval (±0.6 pp) is anti-conservative. A slide-level block bootstrap widens it to ±1.2–3.3 pp, a design effect of 4–27 ([MalariaNet 2026](https://doi.org/10.3390/bios16070358)). Resample patients, not cells ([Rutter 2000, Acad Radiol 7:413](https://doi.org/10.1016/S1076-6332(00)80381-5)). EMFE uses patient-cluster bootstrap CIs on its 40-patient hold-out ([EMFE](https://arxiv.org/abs/2608.24793)).
- **Interval methods:**
  - Clopper–Pearson exact interval ([Clopper & Pearson 1934](https://doi.org/10.1093/biomet/26.4.404)).
  - Wilson score interval ([Wilson 1927](https://doi.org/10.1080/01621459.1927.10502953)).
  - Brown, Cai & DasGupta recommend Wilson or Jeffreys for small n and show Clopper–Pearson is conservative ([Stat Sci 2001](https://doi.org/10.1214/ss/1009213286)).
  - Newcombe compares seven methods and favours score-based intervals ([Stat Med 1998](https://doi.org/10.1002/(SICI)1097-0258(19980430)17:8<857::AID-SIM777>3.0.CO;2-E)).
  - With 0 events in n, the 95 % upper bound is about 3/n, the "rule of three" ([Hanley & Lippman-Hand 1983, JAMA](https://doi.org/10.1001/jama.1983.03330370053031)).
- **Reporting guidelines:** STARD 2015 (flow of participants, 2×2 cross-tabulation, CIs, intended use; [BMJ 2015;351:h5527](https://doi.org/10.1136/bmj.h5527)); TRIPOD+AI ([BMJ 2024;385:e078378](https://doi.org/10.1136/bmj-2023-078378)).
- **CI reference values** (computed here):

  | Result | Clopper–Pearson 95 % | Wilson 95 % |
  |---|---|---|
  | 30/30 | 88.4–100 | 88.6–100 |
  | 29/30 | 82.8–99.9 | 83.3–99.4 |
  | 28/30 | 77.9–99.2 | 78.7–98.2 |
  | 10/10 | 69.2–100 | 72.2–100 |
  | **9/10** | **55.5–99.7** | **59.6–98.2** |
  | 8/10 | 44.4–97.5 | 49.0–94.3 |
  | 40/40 | 91.2–100 | 91.2–100 |
  | 39/40 | 86.8–99.9 | 87.1–99.6 |
  | 50/50 | 92.9–100 | 92.9–100 |
  | 49/50 | 89.4–99.9 | 89.5–99.6 |

  One-sided 95 % upper bounds on the FP rate with zero FPs: 25.9 % for n = 10 (rule of three: 30 %); 7.2 % for n = 40; 5.8 % for n = 50.

### Inferences

**Proposed protocol (pre-register before unblinding the hold-out patient table)**
0. **Freeze and document.** Hold-out membership by C-number, with counts of infected and healthy patients (unknown to me; if stratified, 30 + 10). Confirm C47's two keys share a fold. Fix the probability source: the CV set uses out-of-fold single-model p; the hold-out uses the 10-model ensemble mean p as primary.
1. **Primary rule family R1** (count rule): positive if K_j(t) = #{crops with p ≥ t} ≥ τ.
   - t ∈ {0.19 (the existing CV-chosen cell threshold), 0.50, 0.80, 0.95, 0.99};
   - τ ∈ {1, 2, 3, 4, 5, 6, 8, 10, 12, 15};
   - 50 candidates.
2. **Secondary families** (exploratory comparators; selected by the same criterion on CV only):
   - R2, fraction: K_j/n_j ≥ φ, φ ∈ {1, 2, 3, 5, 10, 20 %}. Near-duplicate of R1 here.
   - R3, Delahunt-style FP-corrected burden: B_j = (K_j/n_j − r̂(t)) / ŝ(t) > c.
     - r̂ is the pooled per-crop FP rate on **CV healthy patients' crops only**;
     - ŝ is the mean per-patient crop recall on CV infected patients;
     - c is on a grid.
   - R4, top-m mean: mean of the m largest p ≥ s, with m ∈ {1, 3, 5}.
   - R5, mean probability ≥ s (Yu 2023's primary rule).
   - R6, noisy-OR 1 − Π(1 − p) ≥ s, reported as an expected-to-fail baseline.
   - Attention-MIL requires training and stays out of scope.
3. **Selection criterion** (write it down first). Default:
   - maximise Youden's J on the 160 CV patients **subject to CV specificity ≥ 95 %** (≤ 2 false-positive healthy patients if about 40 healthy);
   - tie-break 1: the largest minimum margin, i.e. the distance in crops between τ and the nearest CV patient's K_j;
   - tie-break 2: the smaller τ.
   - Rationale: 95 % sits between WHO's < 10 % RDT FPR / Delahunt's 90 % and Dhorda's 2.5 % Level-1 FP limit.
   - Alternatives such as "specificity = 100 % on CV" are acceptable only if pre-specified.
4. **Nested estimate of the selection procedure.** For each of the 10 CV folds, select the rule on the other 9 folds' OOF patients and apply it to the left-out fold. Pool the 160 decisions into a nested-CV sensitivity and specificity. This measures optimism and gives a larger specificity denominator (about 40 healthy).
5. **One-shot hold-out.** Apply the selected rule to the ensemble probabilities of the 40 patients. Then, as a robustness check, apply the same rule to each of the 10 fold models' hold-out predictions and report the range.
   - Why: the OOF (single-model) and ensemble probability distributions differ. The team's own t = 0.19 moved hold-out cell specificity from 98.87 % to 93.93 %.
6. **Stress tests** (no training; label as such):
   - (a) *Dilution*: keep k ∈ {1, 2, 3, 5} random parasitized crops per infected hold-out patient (e.g. 100 repeats) and re-apply the rule. This gives sensitivity against k, a crop-count "detection curve".
   - (b) *FP-burden extrapolation*: expected FP crops per healthy patient if all ~1,180 segmented cells were scored (n_seg × r̂), compared with τ.
   - (c) The Poisson ceiling table from Q2.

**Proposed reporting tables**
- **Table P1, rule selection on CV** (OOF, 160 patients; state n infected / n healthy). Columns: family, t, τ (or φ, c, s), CV sensitivity (x/N), CV specificity (x/N), J, nested-CV sensitivity, nested-CV specificity, selected (✓). Show all 50 R1 rows (appendix) and the best row per secondary family.
- **Table P2, primary hold-out result** (pre-registered rule, 40 patients):
  - a 2×2 table (TP, FP, FN, TN);
  - sensitivity and specificity, each with a CP and a Wilson 95 % CI;
  - balanced accuracy;
  - patient-level AUC of K_j(t), with a bootstrap CI over patients;
  - PPV/NPV only at the dataset's 75 % prevalence, flagged as non-transferable.
- **Table P3, per-patient listing** (all 40). Columns: C-ID, reference status, n crops, n parasitized crops (label), K_j(t), max p, decision, correct, margin (K_j − τ), note.
- **Table P4, sensitivity by parasitized-crop stratum** (1–5, 6–10, 11–20, 21–100, > 100), x/N with CP CI, for nested CV and hold-out. Footnote: crop counts ≠ parasitaemia.
- **Table P5, cell-level context** with patient-cluster bootstrap CIs, split three ways: parasitized crops, uninfected crops from healthy patients (the only crops that drive patient-level specificity), and uninfected crops from infected patients. Also give the number of patients with ≥ 1 FP crop.
- **Table P6, stress tests** (dilution curve, FP-burden extrapolation, Poisson ceiling).

**Handling a single false-positive healthy patient**
- Report it unchanged. Example: specificity 9/10 = 90.0 % (CP 55.5–99.7 %; Wilson 59.6–98.2 %). Note that n = 10 cannot distinguish 90 % from 99 %, and point to the nested-CV specificity, which has the larger n.
- Never re-tune τ or t after seeing it. Any alternative rule is labelled "post hoc, exploratory", as Yu 2023's recalculation should have been.
- Characterise the case:
  - K_j and the margin to τ;
  - a montage of the flagged crops with their p;
  - whether they look like stain precipitate, platelets or debris (the uninfected class contains artifacts);
  - whether every fold model also flags them;
  - the smallest τ at which the patient flips (sensitivity analysis only).
- State that the label cannot be re-adjudicated (no PCR), and that the healthy reference may itself be imperfect.
- Optionally give a clearly labelled pooled estimate over all 50 healthy patients (40 nested-CV + 10 hold-out, each leak-free at the cell level).

**Examiner checklist (caveats to pre-empt)**
1. Crops, not slides. Enrichment and ~6 % uninfected subsampling (Q3) mean patient-level performance is optimistic.
2. Rule selection optimism: give the nested-CV estimate, list every candidate rule, and apply the rule once.
3. Small n: CIs spanning 55–100 % for specificity.
4. Case–control design, single site, 75 % prevalence (STARD).
5. Ensemble vs single-model probability shift between selection and test.
6. Clustered errors: patient-bootstrap all cell-level CIs.
7. No density data, so no LoD or WHO-level claims.
8. C47 duplication and C-number grouping.
9. Uninfected crops from infected patients (75 %) dominate cell-level specificity but are irrelevant to patient-level specificity.
10. Total crop and image counts per patient leak the label, so they are not used.
11. "Patient-level" in prior work means grouped CV, not diagnosis (Q1).
12. Thin films are not the WHO diagnostic film. Thick film is used for diagnosis because it examines more blood.

### Gaps
- The number of healthy patients in the team's 40-patient hold-out was not given. All specificity precision statements above are conditional (shown for 10).
- I found no published guidance specific to *selecting* a count threshold for MIL-style malaria rules. The protocol above is a synthesis of Torres / Delahunt / STARD practice, not an established standard.

---

## Q5. Is there a published analysis of the NIH dataset's per-patient cell counts or of the patientid_cellmapping files?

### Takeaway
Only fragments exist:
- MalariaNet reports C-number parsing coverage and the largest group's share (2.5 %);
- EMFE reports the control-patient mean (68.3 cells) and crop-fraction quartiles;
- Rajaraman 2018 reports per-fold counts.

I found **no published full per-patient distribution** and no description of how crops were selected. The distribution and index forensics computed in Q3 appear to be new. They are consistent with every fragment above (EMFE's 0.328 median and 0.902 maximum crop fraction; MalariaNet's 2.5 % largest group = 702/27,558).

### Cited Findings
- **MalariaNet:** the C-number is parsable for 100 % of images and yields 200 groups covering all 27,558 cells. `C<digits>P<digits>` parses only 86.5 %. The largest group holds 2.5 % of cells. Splits are 70/15/15 by slide group, with 3,320–4,719 test cells per seed ([Hou et al. 2026](https://doi.org/10.3390/bios16070358)).
- **EMFE:**
  - 200 patients (150 infected, 50 uninfected-only controls);
  - controls average 68.3 cells;
  - crop-fraction ("true parasitemia") quartile boundaries 0–0.158, 0.158–0.328, 0.328–0.583, 0.583–0.902;
  - a 40-patient hold-out of 5,643 cells (similar in size to the team's 5,550).
  - [Al Kafi et al. 2026](https://arxiv.org/abs/2608.24793)
- **Rajaraman 2018:** per-fold parasitized / uninfected counts for its 5 patient-level folds ([PeerJ 2018](https://doi.org/10.7717/peerj.4568)).
- **NLM** distributes the two mapping CSVs but publishes no statistics on them ([NLM datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)).
- **Patient-grouped splits are also used by:** a public ViT repository with a 70/15/15 patient split ([GitHub malaria-vit](https://github.com/Emrebener/malaria-vit)) and a transfer-learning study grouping by patient ID ([PMC12731172](https://pmc.ncbi.nlm.nih.gov/articles/PMC12731172/)). Both were seen via search only; I did not verify their contents.

### Inferences
- The team can cite its own computed distribution (Q3) as a contribution, provided the script and CSV versions are archived.
- The near-constant ~68 uninfected crops per patient explains why grouped and ungrouped splits differ only modestly at cell level (0.25–1.45 pp in MalariaNet; 2.7 pp in Rajaraman 2018). The same constant makes patient-level aggregation look easy.

### Gaps
- I did not verify the contents of the malaria-vit repository or PMC12731172 (search snippets only).
- No source documents the crop-sampling procedure. Contacting NLM (the datasheet lists Stefan Jaeger as contact) is the only way to confirm it.
