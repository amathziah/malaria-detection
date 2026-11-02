# Label noise in the NIH Malaria Cell Images dataset, and cheap, responsible error analysis

Evidence tags used below: **[PR]** peer-reviewed; **[PP]** preprint, not peer-reviewed; **[INF]** informal (dataset pages, library documentation, search-engine summaries, dead links). Team numbers used throughout: patient-grouped hold-out of 40 patients, 5,550 cells, 86 errors (55 false negatives (FN), 31 false positives (FP)), accuracy 98.45 %. Researched 2 November 2026. Percentages marked "computed here" are my own arithmetic on published counts.

## 1. What has been documented about label errors in this dataset, is there a corrected list, and what noise rate and ceiling does that imply?

### Takeaway
Fuhad et al. (2020) set aside **1,397 of 27,558 images (5.07 %)**: 647 labelled parasitized and 750 labelled uninfected, described as "falsely labelled **and suspicious**". They did this after consulting one unnamed expert, reported **no accuracy on the original labels**, and their Google Drive link to the "corrected" data now returns **HTTP 404**. The only other relabelling (Michael Delves, IEEE DataPort, 2020, updated 2025) publishes no counts. The only expert check of a model's errors (Rahman et al., a preprint) judged **38 % of 29 false positives** to be mislabeled. The team's own 98.45 % caps the random label noise that the model can detect at 1.55 % of hold-out cells, so the "5 %" figure cannot mean a 95 % ceiling. On the weak evidence available, perhaps **a quarter to a half** of the 86 errors are label disagreements, and the model is probably **within about 1 point** of the attainable ceiling.

### Cited Findings

**Peer-reviewed**
- [PR] Fuhad et al. found the problem while running experiments: "While doing experiments on the malaria dataset, we found that certain samples were mislabeled." — [Fuhad et al. 2020, Diagnostics 10(5):329, PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/) (DOI [10.3390/diagnostics10050329](https://doi.org/10.3390/diagnostics10050329))
- [PR] Their process: "To confirm this rising issue we consulted with an expert", and "The expert confirmed that some of the data are genuinely mislabeled". The data were "later manually annotated as per the presence and absence of malarial parasites". The paper does not name the expert, says nothing about their qualifications, and does not say whether this was the original Mahidol-Oxford slide reader. It describes no model-based screening, so the method appears to be visual inspection by the authors followed by expert confirmation. — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/)
- [PR] Their exact counts:
  - "After removing 647 falsely labeled and suspicious parasitized data" (called "false parasitized").
  - "For uninfected malaria data, 750 suspicious images was found, which was named as false uninfected."
  - "While annotating, suspicious, and falsely labelled data was put aside."
  - The remaining set is 13,132 parasitized + 13,029 uninfected = 26,161.
  - In total, 1,397 images = 5.07 % of 27,558: 4.70 % of the parasitized class and 5.44 % of the uninfected class (computed here). — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/)
- [PR] Errors run in both directions: "Some of the data seems like uninfected but labelled as parasitized" and "some parasitized images are labelled as uninfected". Figure 1 panels (c) and (d) show "Falsely labelled uninfected images" and "Falsely labelled parasitized images". — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/)
- [PR] The paper contradicts itself on what was done. The Introduction says the mislabeled samples "were corrected and the corrections can be found in [41]", but Section 3.1 says they were "put aside", meaning removed. No separate count of relabelled, as opposed to removed, images is given. — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/)
- [PR] There is **no before/after comparison**: all reported accuracies are on the cleaned 26,161 images. The headline is 99.23 % (Table 5 lists 0.9923 for 32×32 inputs with the autoencoder). The 80:10:10 split is never described as patient-level, and the test size is inconsistent: 10 % of 26,161 is about 2,616, yet the text mentions "3000 test images". — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/)
- [PR] Reference 41 is "Corrected Malaria Data—Google Drive", `https://drive.google.com/drive/folders/10TXXa6B_D4AKuBV085tX7UudH1hINBRJ?usp=sharing`, accessed by the authors on 29 Dec 2019. — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/). [INF] When I fetched it on 2 Nov 2026 it returned **HTTP 404**. — [Drive link](https://drive.google.com/drive/folders/10TXXa6B_D4AKuBV085tX7UudH1hINBRJ?usp=sharing)
- [PR] The "≈5 %" figure has spread to other papers. A later ensemble paper reportedly says about 5 % of the dataset is mislabeled and that this could affect performance. I could not read its full text (HTTP 403), so this comes from a search summary and the paper's own source is unconfirmed; it is most likely Fuhad. — [A new ensemble learning approach to detect malaria from microscopic red blood cell images (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S2666351122000547)
- [PR] Recent peer-reviewed papers cite Fuhad's accuracy without discussing label quality. MalariaNet cites his "99.23%-accuracy" system without mentioning label quality. — [Hou et al. 2026, Biosensors 16(7):358, PMC13406217](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/). Parveen et al. mention corrected labels only as Fuhad's work. — [Parveen et al. 2025, Sci Rep 15:45037](https://www.nature.com/articles/s41598-025-28387-7)
- [PR] I found no peer-reviewed paper applying confident learning or cleanlab to this dataset. A 2025 retinal-imaging study notes that cleanlab reports in medical imaging are few (per a search summary). — [Lin et al. 2025, npj Digit Med 8:10](https://www.nature.com/articles/s41746-024-01424-x)

**Preprints and informal sources (weaker evidence)**
- [PP] Rahman et al. tested on a random split of 2,756 cells. Their TL-VGG16 model made 63 errors (34 FN, 29 FP) for 97.77 % accuracy. They report: "the false positives from TL-VGG16 have been evaluated by a pathologist. Following evaluation, it has been concluded that 38% of the blood cells from the false positives are in fact mislabeled, showing clear formation of malaria parasites while labelled as uninfected." — [Rahman et al. 2019, arXiv:1907.10418](https://arxiv.org/abs/1907.10418)
  - Of k/29, only 11/29 rounds to 38 % (Wilson 95 % CI 23–56 %; computed here). The paper does not give the count.
- [PP] Rahman et al. then assert, without checking, that "a similar error rate can be found for the false negatives". They add: "Due to budget constraints and large number of blood cell images, we were unable to perform a thorough data validation scheme conducted by a pathologist over the entire NIH Malaria dataset." Figure 12 is titled "Example of mislabeled parasite infected blood cells confirmed by pathologist." — [Rahman et al. 2019](https://arxiv.org/abs/1907.10418)
- [PP] The same preprint describes the negative class: it "contained no plasmodium but could contain other types of objects including staining artifacts/impurities". Artefact-bearing "uninfected" cells are therefore correctly labelled by design, and false alarms on them are model errors. — [Rahman et al. 2019](https://arxiv.org/abs/1907.10418)
- [INF] The IEEE DataPort deposit "Malaria dataset (thin blood smear, updated)" is by Kaustubh Chakradeo (Radboud), Michael Delves (London School of Hygiene & Tropical Medicine) and Sofya Titarenko (Huddersfield). It was created 15 Jul 2020 and last updated 4 Aug 2025.
  - It states that "a relatively large proportion of images was mislabeled" and "the dataset has been double-checked and relabeled by Michael Delves".
  - Images are "reorganised into five folders: parasitised, uninfected, weird, bad segmentation, unsure".
  - The page gives **no counts**, reviewer numbers, licence or associated paper. Files need a free IEEE login.
  - DOI [10.21227/mrgx-rh96](https://doi.org/10.21227/mrgx-rh96). — [IEEE DataPort page](https://ieee-dataport.org/open-access/malaria-dataset-thin-blood-smear-updated)
- [INF] A search summary of the same listing mentions an approximately 336 MB archive and "5 groups of parasitized and uninfected images for cross-validation (after cleaning)". I did not confirm either on the page itself. — [IEEE DataPort page](https://ieee-dataport.org/open-access/malaria-dataset-thin-blood-smear-updated)
- [PP] A 2025 preprint introducing an instance-level P. falciparum dataset in COCO format reportedly notes that the original NIH annotation was done by a single expert, which "can introduce a considerable labeling bias". This comes from a search summary; I did not open the paper. — [arXiv:2507.18483](https://arxiv.org/abs/2507.18483)
- [PP] Kabore & Guel mention "annotation variability" only in general terms, with no NIH-specific numbers. — [arXiv:2501.00464](https://arxiv.org/abs/2501.00464)

### Inferences
- **Checking the deck sentence.** "About 5 %" is correct (1,397 / 27,558 = 5.07 %). "Questioned" is the right verb, but the sentence should make three things clear:
  - the 1,397 images mix expert-confirmed errors with merely "suspicious" images;
  - they were removed, not shown one by one to be wrong;
  - no list can be reused today, because the link is dead.

  Suggested wording: *"Fuhad et al. (2020) set aside 1,397 of 27,558 cells (5.1 %) as mislabeled or suspicious after consulting one expert; they report no accuracy on the original labels, and their list is no longer online. We keep the original labels, as Marques et al. did."*
- **The team's own result bounds the noise.** Suppose a fraction ε of hold-out labels were random flips that a good model cannot reproduce. Then accuracy against those labels could not exceed 1 − ε.
  - The observed 98.45 % therefore means random, model-detectable label noise in the hold-out is at most **1.55 %**, the share of all 86 errors.
  - So Fuhad's 5 % must be mostly ambiguous cells on which the model reproduces the original reader's convention, or cells that were never wrong. It is **not** evidence of a 95 % ceiling.
- **How much of the 86 errors could be label noise.** Borrowing Rahman's 38 % (CI 23–56 %) gives roughly 20–48 errors, with a central estimate of about 33. This estimate is weak: one pathologist, 29 false positives, a random cell-level split and a different model.
  - If exactly those cells were relabelled and no new errors appeared, accuracy against corrected labels would be 98.80–99.32 % (central 99.04 %; computed here).
  - That is an upper bound. Correcting labels would also expose mislabeled cells the model happened to agree with.
- **Ceiling against the original labels.** A perfect classifier would also "miss" every true label error, so the ceiling is at most 100 % minus 0.35–0.87 %, that is **≈99.1–99.6 %**.
  - 98.45 % is plausibly **0.7–1.2 points** below that.
  - "Most of the remaining error is label noise" is **not** supported. "Perhaps a quarter to a half" is the defensible range.
- **Which direction the errors run.** The pathologist-confirmed label errors were all false positives: cells labelled uninfected that showed parasites. The team has more false negatives (55; 1.95 % of parasitized cells) than false positives (31; 1.13 % of uninfected cells). Fuhad documents label errors in both directions, and the literature in Q5 suggests many false negatives are faint or early-stage cells that are genuinely hard.
- **Errors cluster by patient.** Half the errors come from 7 of 40 patients, and 14 patients have none. Under an equal per-cell rate, a crude Poisson calculation predicts about 4.7 zero-error patients, not 14 (computed here; it ignores differing cell counts and class mixes).
  - This points to slide- or patient-level causes such as stain, focus, parasitemia or annotation session.
  - Clustering alone cannot separate label noise from model error, because both can cluster by slide.

### Gaps
- The Delves relabelling: counts per folder, whether original file names are kept, the number of reviewers and the licence are not on the public page (login required). Nothing I found reports training or testing on it.
- Fuhad's list: the link is dead, and I did not check the Wayback Machine or contact the authors.
- I found no published inter-reader agreement for this dataset, which had a single reader at the Mahidol-Oxford Tropical Medicine Research Unit (MORU). The true ceiling is therefore unmeasured.
- I could not confirm whether the group's later peer-reviewed paper ([Tissue & Cell 69, 2021](https://katalog.lib.cas.cz/KNAV/EdsRecord/edsair,edsair.doi.dedup.....5c71e578e588288ca7848f9043a38c1d)) repeats the 38 % finding. It appears to be about a different, higher-variation dataset.
- I did not verify whether Marques et al. 2022 used the original labels; the deck asserts this.
- Neither of two searches found any GitHub repo or Kaggle notebook auditing these labels with cleanlab.

## 2. How can likely label errors be found with existing out-of-fold predictions, and how should a team without a microscopist report them?

### Takeaway
Use confident learning through cleanlab's `find_label_issues`. It needs only the labels and out-of-sample probabilities, which the team already has for all 27,558 cells (out-of-fold for the 160 training patients, ensemble predictions for the 40 hold-out patients). In a two-class problem, ranking by loss, self-confidence or margin gives the same order. AUM is not possible without re-training. Treat every flag as a candidate:
- In the NeurIPS 2021 audit, human reviewers confirmed only **51 %** of confident-learning flags on average.
- Automated relabelling in a 2025 medical study wrongly changed **0.7–10.7 %** of correct labels.

So show galleries, give a range, and keep the original-label accuracy as the headline.

### Cited Findings

**Peer-reviewed**
- [PR] Confident learning (Northcutt, Jiang & Chuang, JAIR 2021):
  - It estimates the joint distribution of given and true labels "building on the assumption of a class-conditional noise process", using "pruning noisy data, counting with probabilistic thresholds, and ranking examples".
  - It is described as "provably consistent".
  - It found errors in MNIST and ImageNet (e.g. 645 "missile" images labelled "projectile").
  - Cleaning before training "moderately increases accuracy" for models such as ResNet.

  — [arXiv:1911.00068](https://arxiv.org/abs/1911.00068); JAIR DOI [10.1613/jair.1.12125](https://doi.org/10.1613/jair.1.12125). The per-class threshold, the mean self-confidence of examples carrying each label, is defined in the paper body; I re-checked only the abstract.
- [PR] Pervasive label errors (Northcutt, Athalye & Mueller, NeurIPS 2021 Datasets & Benchmarks):
  - At least 3.3 % label errors on average across 10 test sets, and at least 6 % of the ImageNet validation set.
  - On average **51 %** of algorithmically flagged candidates were confirmed as mislabeled by human reviewers.
  - On corrected labels, ResNet-18 overtakes ResNet-50 if the prevalence of originally mislabeled test examples rises by 6 %, and VGG-11 overtakes VGG-19 on CIFAR-10 at 5 %.

  — [arXiv:2103.14749](https://arxiv.org/abs/2103.14749)
- [PR] AUM (Pleiss, Zhang, Elenberg & Weinberger, NeurIPS 2020) relies on the "training dynamics" of clean versus mislabeled samples. An extra class "populated with purposefully mislabeled threshold samples" learns an upper bound on AUM.
  - WebVision50: removing 17 % of training data improved test error by 1.6 points.
  - CIFAR-100: removing 13 % improved it by 1.2 points.

  — [arXiv:2001.10528](https://arxiv.org/abs/2001.10528)
- [PR] Lin et al. 2025 ran cleanlab on retinal images with out-of-sample probabilities from 5-fold cross-validation (Swin Transformer), replacing labels automatically each round.
  - "The majority (86.6 to 97.5%) of label errors were accurately modified."
  - The false-labelling rate (correct labels wrongly changed) was 0.7–5.6 % on colour fundus photographs (CFP) and 0.7–10.7 % on optical coherence tomography (OCT).
  - On noise-free data, "label accuracy may decrease from 100% to approximately 99.3 or 99.4% after six iterations".
  - Warnings: "achieving a completely clean dataset is not feasible with this approach", and "One notable risk involves misidentifying actual labels as label issues and subsequently mis-modifying them".
  - Ambiguous cases "with overlapping category representations" drove the false labelling.
  - The authors suggest "manual confirmation based on the ranked label scores of each image".

  — [Lin et al. 2025, npj Digit Med 8:10](https://www.nature.com/articles/s41746-024-01424-x)
- [PR] Xia et al. (ICLR 2025) show that label smoothing degrades selective classification, that is, separating correct from wrong predictions by confidence. The effect worsens with stronger smoothing, and post-hoc logit normalisation recovers much of the loss. — [arXiv:2403.14715](https://arxiv.org/abs/2403.14715); [ICLR 2025 record](https://mlanthology.org/iclr/2025/xia2025iclr-understanding)

**Preprints and informal sources (weaker evidence)**
- [INF] The cleanlab documentation for `find_label_issues(labels, pred_probs, *, ...)` says: "Returned label issues are most accurate when they are computed based on out-of-sample pred_probs from your model", and recommends cross-validation.
  - `filter_by` options: `prune_by_noise_rate` (default), `prune_by_class`, `both`, `confident_learning`, `predicted_neq_given`, `low_normalized_margin`, `low_self_confidence`.
  - `return_indices_ranked_by` options: `self_confidence`, `normalized_margin`, `confidence_weighted_entropy`.
  - `frac_noise=1.0` is recommended.
  - The stable docs list releases up to v2.7.1.

  — [cleanlab filter docs](https://docs.cleanlab.ai/stable/cleanlab/filter.html)
- [PP] Rahman et al.'s pathologist review of false positives is the only expert-validation precedent on this dataset (see Q1). — [arXiv:1907.10418](https://arxiv.org/abs/1907.10418)
- [PP] Patient structure: NIH provides patient-to-image mapping files. The 150 infected patients' slides contribute cells to both classes, while the 50 control patients contribute only uninfected cells. — [EMFE, Al Kafi et al. 2026, arXiv:2608.24793](https://arxiv.org/abs/2608.24793)

### Inferences

**Choosing a method for this team**
- **The ranking choice does not matter for two classes.** Self-confidence p(given label), normalised margin (2p − 1) and per-cell cross-entropy (−log p) all rise or fall together. "Loss ranking", "self-confidence" and "margin" therefore produce the same ordering.
- **What does matter:**
  - how many cells to flag: confident learning's per-class thresholds versus simple argmax disagreement;
  - how the 10 models are combined: mean probability versus the number of models that disagree with the label, if per-model probabilities were saved.
- **Label smoothing.** The per-class thresholds adapt to the uniform under-confidence that label smoothing causes (ECE about 0.06), and rankings are unaffected by any monotone miscalibration. However, Xia et al. show label smoothing also *reorders* confidence, so the precision of the flags may be below the 51 % seen on ImageNet-type data.
- **Run the two prediction sets separately.** Out-of-fold probabilities come from one model per cell, while hold-out probabilities come from a 10-model ensemble, so their calibration differs.
  - If the out-of-fold folds were not patient-grouped, those probabilities are out-of-sample per cell but not per patient. They may be over-confident on same-slide cells; disclose this.
- **AUM is not feasible now.** It needs margins logged during training and a re-train with threshold samples. Mention it as future work only.
- **Evidence that needs no microscopist:**
  - **Patient status.**
    - A false positive in an *uninfected-only control* patient is almost certainly a model error or artefact. For it to be a missed parasite, the patient's diagnosis would also have to be wrong.
    - False positives in *infected* patients are the pool where Rahman-type label errors live.
    - Every false negative comes from an infected patient, by construction.
  - **The Delves relabelling.** If the files keep their original names, cross-tabulating the 86 errors against the Delves folders (other class, weird, bad segmentation, unsure) gives an *independent* re-read. It is still a single reader. This is the best evidence currently available.
  - **Agreement across the 10 models.** Errors where 10 of 10 models disagree with the label are the strongest candidates.

**A plan for under two hours on a laptop, using the existing predictions**

| Time | Step | Output |
|---|---|---|
| 0:00–0:15 | One table per cell: file name, patient ID, patient status (infected or control, from the NIH mapping), label, ensemble p(parasitized), per-model probabilities if saved, split (out-of-fold or hold-out). | Tidy CSV |
| 0:15–0:35 | Per-patient errors and error rates. Permutation test: shuffle error flags across cells *within class*, keeping each patient's cell counts, 10,000 times. Test statistics: share of errors in the top 7 patients, and number of zero-error patients. Patient-cluster bootstrap (resample the 40 patients, about 2,000 times) for 95 % CIs on accuracy and MCC. | p-value for clustering; cluster CIs |
| 0:35–0:55 | cleanlab on out-of-fold and hold-out separately: `count.num_label_issues`, `filter.find_label_issues(..., return_indices_ranked_by='self_confidence')`, `rank.get_label_quality_scores`. Count how many of the 86 errors are flagged, split by FN/FP and by infected/control patient. | Candidate list; estimated issue counts |
| 0:55–1:25 | Galleries at native resolution with file name, patient and p: all 55 FN and all 31 FP, sorted by p; the top cleanlab candidates from the out-of-fold set; and a *control gallery* of correctly classified cells with similar p. Two team members independently triage a shuffled mix of errors and controls, **blind to label and prediction**, using the rubric in Q5. Compute Cohen's κ. | Category counts with κ |
| 1:25–1:45 | Histograms of p(parasitized) by true class, errors highlighted, log y-axis. Reliability diagram and ECE with equal-mass bins. Optional risk–coverage curve. | Calibration figure |
| 1:45–2:00 | Sensitivity table: accuracy if 0 / 25 / 38 / 50 % of errors were label noise (98.45 / 98.84 / 99.04 / 99.23 %; computed here). Draft the limitations text. | Slide plus caveats |
| Optional (+30 min) | Download the Delves set (free IEEE login), match file names, and cross-tabulate against the errors. | Independent re-read rate |

Minimal code, with column order [uninfected, parasitized]:
`P = np.c_[1-p, p]; issues = cleanlab.filter.find_label_issues(y, P, return_indices_ranked_by="self_confidence"); n = cleanlab.count.num_label_issues(y, P)`

**What the team must NOT claim**
- That any specific cell "is mislabeled". The correct terms are "candidate label error" or "confident model–label disagreement". Even with expert-style review, only about 51 % of flags were confirmed in the NeurIPS audit.
- A relabelled or "cleaned" hold-out accuracy as the headline. The pre-registered metric uses the original labels, and any corrected figure is post hoc and exploratory. Relabelling only the cells the model got wrong is one-sided: it can only raise accuracy, while label errors the model agreed with stay hidden.
- That the ceiling is 95 % because of Fuhad's 5 %. Their own result contradicts this.
- That the remaining errors "are" label noise. At most they are "consistent with" ambiguity, with an estimated share of about a quarter to a half resting on one small preprint.
- Equivalence with Fuhad's 99.23 %. That figure comes from a cleaned, likely cell-level test set with no before/after comparison.
- That the blinded triage categories are diagnoses. They are non-expert visual categories with a stated κ.

### Gaps
- No precision figure exists for confident-learning flags on this dataset or on any malaria cell data.
- I found no study of how label smoothing combined with ensembling affects the precision of confident-learning flags. The Xia et al. finding is indirect.
- I could not confirm whether the NIH patient-to-image mapping gives a control or infected status for every hold-out patient. EMFE says it does for all 200.

## 3. What does a good error-analysis section look like in medical image classification papers, ideally malaria ones?

### Takeaway
The CLAIM reporting checklist asks for an analysis of incorrect results (item 37 in 2020, reworded as item 39 in 2024), yet compliance is poor; one review found 0 of 9 studies met it. Two malaria preprints are the closest templates:
- **Rahman et al.:** a confusion matrix, galleries of false positives and false negatives, a pathologist check of the false positives, and an honest statement of limitations.
- **EMFE (2026):** a 40-patient hold-out almost the same size as the team's; a gallery of all four outcome types; statistical tests comparing false negatives with true positives and false positives with true negatives; patient-cluster bootstrap CIs; a patient-level analysis stratified by parasitemia; and explicit limitations.

### Cited Findings

**Peer-reviewed**
- [PR] CLAIM 2020 includes "failure analysis of incorrectly classified cases" as item 37, under model performance in Results. — [CLAIM 2020 (Mongan et al., Radiology: AI, DOI 10.1148/ryai.2020200029)](https://pubs.rsna.org/doi/pdf/10.1148/ryai.2020200029); item number per [a reproduced checklist](https://www.springermedizin.de/resource/supplementary/12885_2024_11838_MOESM1_ESM.pdf/26622134)
- [PR] The 2024 CLAIM update rewords the item to cover incorrect results generally and renumbers it 39 (per a search summary; I did not read the full wording). — [CLAIM 2024 checklist](https://pubs.rsna.org/doi/suppl/10.1148/ryai.240300/suppl_file/ryai240300_CLAIMchecklist.docx)
- [PR] Adherence is poor: in one systematic review, 0 of 9 included studies met the failure-analysis item. — [PMC10249293, Table 5](https://pmc.ncbi.nlm.nih.gov/articles/PMC10249293/table/Tab5)
- [PR] MalariaNet (Biosensors 2026) uses slide-disjoint splits over three seeds. A slide-level block bootstrap widens the 95 % interval to about ±1.2 to ±3.3 points, and the authors call per-cell figures "optimistic upper bounds". It has no error gallery and no calibration analysis. — [Hou et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/)
- [PR] Parveen et al. (Sci Rep 2025) use Grad-CAM, LIME and SHAP on false positives.
  - They conclude "false positives often arose from cytoplasmic staining artifacts or boundary irregularities". Figure 19's caption reads "color and boundary artifacts can lead to false-positive malaria detections".
  - However, they use a random image-level split (18,963 / 4,063 / 4,064) with no calibration analysis.
  - They also report "approximately 2015 images were misclassified by both hybrid models" alongside about 98 % accuracy, an inconsistency.

  An example of a qualitative, explanation-led error analysis that should not be imitated uncritically. — [Parveen et al. 2025](https://www.nature.com/articles/s41598-025-28387-7)
- [PR] Pervasive label errors presents galleries of validated label errors (Fig. 1). — [arXiv:2103.14749](https://arxiv.org/abs/2103.14749) (figure content per a search summary)
- [PR] Aggregate metrics can hide clinically meaningful failing subgroups, which is the hidden-stratification argument (Oakden-Rayner et al., ACM CHIL 2020). — [arXiv:1909.12475](https://arxiv.org/abs/1909.12475) (from prior knowledge; not re-opened this session)
- [PR] Reliability diagrams and ECE come from Guo et al., ICML 2017. — [arXiv:1706.04599](https://arxiv.org/abs/1706.04599). Combining ensembles with label smoothing or mixup-style training can make models under-confident (Wen et al., ICLR 2021). — [arXiv:2010.09875](https://arxiv.org/abs/2010.09875). Both are from prior knowledge and were not re-opened this session.

**Preprints (weaker evidence)**
- [PP] Rahman et al.'s "False Case Analysis":
  - a confusion matrix (63 errors out of 2,756);
  - Fig. 12, mislabeled infected cells "confirmed by pathologist";
  - Fig. 13, galleries of false positives and false negatives;
  - a limitations paragraph.

  Their patient-level rule ("any parasitized cell means an infected patient") reached 93 % accuracy and AUC 86.5 %, which they attribute to "staining variations between patients". — [arXiv:1907.10418](https://arxiv.org/abs/1907.10418)
- [PP] EMFE (Al Kafi et al., Aug 2026) is a handcrafted-feature model evaluated with patient-grouped nested cross-validation (20 outer folds, 3 inner folds) plus an untouched 40-patient hold-out (160 / 40 patients; 21,915 / 5,643 cells). Hold-out accuracy is 94.29 % [92.63, 95.82] by patient-cluster bootstrap. Its error analysis:
  - Fig. 7 gallery with counts: 2,657 TP, 239 FN, 2,664 TN, 83 FP.
  - Table 12 Mann–Whitney U tests of each feature for FN vs TP and FP vs TN: false negatives are "marginal, low-signal cells", and false positives are "consistent with staining artifacts or debris".
  - Patient-level aggregation with Wilson CIs: an "any positive cell" rule gives 14 % specificity; τ = 10 recovers perfect specificity on this cohort, with the sensitivity cost "concentrated in low-parasitemia patients".
  - A limitations paragraph noting the crops exclude "debris, stain precipitation, platelets, white blood cells".

  — [arXiv:2608.24793](https://arxiv.org/abs/2608.24793)
- [PP] EMFE also cites accuracy drops from cell-level to patient-level evaluation: 98.61 % → 95.90 % (Rajaraman et al. 2018) and 96.90 % → 78.00 % (Yu et al.). — [EMFE](https://arxiv.org/abs/2608.24793), citing [Rajaraman et al. 2018, PeerJ 6:e4568](https://doi.org/10.7717/peerj.4568). I did not check the primary sources. EMFE lists the Yu et al. paper as "IEEE Access 8:12345–12356, 2020", a page range that looks implausible, so treat the 78.00 % figure as **unverified** until it is traced to the original.

### Inferences

**A template for the team's error-analysis section (or 3–4 slides)**
1. **Headline with honest uncertainty.** Original-label accuracy and MCC, a patient-cluster bootstrap CI, and the confusion matrix split by infected versus control patients.
2. **Where the errors are.** A bar chart of errors per patient, sorted, with cell counts, plus the permutation-test p-value for clustering. Name the 7 high-error patients and describe their slides (stain, focus, parasitemia).
3. **What the errors look like.** FN and FP galleries sorted by confidence, next to a matched gallery of correct cells. Report blinded, two-rater category counts with κ.
4. **How confident the model was.** Histograms and a reliability diagram. State that label smoothing makes the model under-confident (ECE about 0.06) and that this also weakens confidence as an error signal (Xia et al.).
5. **How much could be label noise.** An evidence table (Fuhad 5.1 % set aside; Rahman 38 % of 29 FP; Delves "relatively large proportion", counts unknown), the cleanlab flag counts, and the scenario table. Conclude with a range, not a number.
6. **Limitations.** No microscopist; one original reader; candidate errors are not confirmed; any corrected-label figure is post hoc.

Following this template would put the team ahead of most published malaria papers on CLAIM's failure-analysis item. EMFE (same 40-patient hold-out design) and MalariaNet are the closest peers to cite.

### Gaps
- I found no malaria paper that used blinded non-expert triage with κ, or that formally tested per-patient error clustering on the NIH data.
- I did not read the exact 2024 wording of CLAIM item 39.

## 4. Would cleaned labels or noise-robust losses plausibly change the team's conclusions, and what effect sizes are reported?

### Takeaway
Probably not:
- **Hold-out.** The team's own result limits the gain from relabelling the hold-out to at most 1.55 points, and more plausibly about 0.35–0.9 points.
- **Published training-side gains.** Cleaning or noise-robust training typically gains about 1–2 points, and only at far higher noise levels (AUM: 1.2–1.6 points after removing 13–17 % of web-scale data).
- **Already covered.** The label smoothing already in use is competitive with loss-correction methods under label noise.
- **Ablation arms.** All arms share the same test labels, so label noise mostly moves them together. It can flip a ranking only when differences between arms are as small as the noise.

### Cited Findings

**Peer-reviewed**
- [PR] Label smoothing performs competitively with loss correction under label noise (Lukasik et al., ICML 2020, PMLR 119:6448–6458). — [PMLR](https://proceedings.mlr.press/v119/lukasik20a.html)
- [PR] AUM: removing 17 % of WebVision50 training data gave −1.6 points of error; removing 13 % of CIFAR-100 gave −1.2 points. — [arXiv:2001.10528](https://arxiv.org/abs/2001.10528)
- [PR] Confident learning: cleaning ImageNet before training "moderately increases accuracy". — [arXiv:1911.00068](https://arxiv.org/abs/1911.00068)
- [PR] Lin et al. 2025 on retinal images:
  - Accuracy improved "0.3–52.9%" after cleaning; the range spans injected-noise levels up to extreme ones.
  - 10 % injected noise cut accuracy by 4.0 % (CFP) and 4.4 % (OCT) in the Results, but 3.6 % and 4.5 % in the Discussion, an internal inconsistency.
  - On external data, EyePACS AUC went from 0.972 to 0.979, with no significant accuracy change (p = 0.105). APTOS-2019 AUC went from 0.785 to 0.810 (p = 0.036; accuracy p = 0.006).

  — [Lin et al. 2025](https://www.nature.com/articles/s41746-024-01424-x)
- [PR] Test-label errors flip model rankings only when the prevalence of mislabeled test examples changes by about 5–6 % relative to small accuracy gaps. — [arXiv:2103.14749](https://arxiv.org/abs/2103.14749)
- [PR] Fuhad et al. report no before/after accuracy, so their 99.23 % cannot be credited to cleaning. — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/)
- [PR] Patient-level uncertainty is larger than any plausible label correction:
  - With slide-disjoint splits, EfficientNet-B0 fell from 97.22 % to 96.75 % (MalariaNet: 97.06 ± 0.45 → 95.61 ± 1.02).
  - Slide-level bootstrap intervals were about ±1.2 to ±3.3 points.

  — [Hou et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/)
- [PR] A review of noisy-label methods in medical imaging is available for further reading (Karimi et al., Medical Image Analysis 2020). — [DOI 10.1016/j.media.2020.101759](https://doi.org/10.1016/j.media.2020.101759) (pointer only; not re-opened this session)

**Preprints (weaker evidence)**
- [PP] Rahman et al. claim that "the mislabeled data also has a negative impact in the overall performance" but give no figure. — [arXiv:1907.10418](https://arxiv.org/abs/1907.10418)

### Inferences
- **Size of a plausible correction.** Relabelling the hold-out under the Rahman-based range would move accuracy by about 0.35–0.9 points. That is within or near a patient-cluster CI for 40 patients (MalariaNet's slide-level intervals are ±1.2–3.3 points). It would not change the claim "within about 1 point of published results".
- **A cheap robustness check for the ablation conclusions.** If per-arm hold-out predictions were saved, recompute each A1–A3 comparison twice: on all cells and with the cleanlab-flagged cells excluded. If the direction and size of each difference hold, write "conclusions are robust to excluding N candidate label errors". This is a sensitivity analysis, never the main result.
- **Training-side noise-robust losses** (e.g. generalised cross-entropy, co-teaching) would mostly duplicate what label smoothing already provides at an estimated noise level near 1 %. Expect changes well under 1 point, which a 40-patient hold-out cannot resolve. This is an inference from the effect sizes above, not a measured result.
- **Recommended sentence.** "Published audits and our own error bound suggest that roughly a quarter to a half of our 86 errors may be label disagreements rather than model errors. Correcting them would change accuracy by under 1 point and would not alter any ablation conclusion."

### Gaps
- No study of this dataset compares training on original versus cleaned labels under patient-level evaluation. Fuhad gives no "before"; the Delves set appears unused in published work.
- I found no effect sizes for noise-robust losses on malaria cell images specifically.

## 5. What failure categories do malaria classifiers typically show on this dataset, and which papers show galleries of misclassified NIH cells?

### Takeaway
Documented categories on NIH-cell classifiers are:
- **missed early or low-signal ring stages** (false negatives);
- **staining artefacts, debris and boundary or edge irregularities that mimic chromatin** (false positives);
- **genuine label errors in both directions**;
- **segmentation or "weird" crops**;
- **stain differences between patients**.

Platelets are documented as a false-positive source in a different dataset and pipeline, and white blood cells in African thick-smear images. I found no NIH-specific evidence on Howell–Jolly bodies. Galleries of misclassified or mislabeled NIH cells appear in Rahman et al. (Figs 12–13), Fuhad et al. (Fig. 1c–d), EMFE (Fig. 7) and Parveen et al. (Figs 19–20).

### Cited Findings

**Peer-reviewed**
- [PR] Staining and boundary artefacts behind false positives (NIH/Kaggle cells, random split):
  - "model errors often stem from cytoplasmic staining artifacts, illumination noise, or boundary irregularities";
  - "faint cytoplasmic stains, peripheral shadows, or edge artifacts" that "resemble the chromatin or ring patterns typical of infected cells";
  - Figs 19–20 show false positives with Grad-CAM, LIME and SHAP.

  — [Parveen et al. 2025, Sci Rep](https://www.nature.com/articles/s41598-025-28387-7)
- [PR] Label errors in both directions, with example panels in Fig. 1c–d. — [Fuhad et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7277980/)
- [PR] Platelets in a *different* dataset with its own segmentation pipeline: "as platelets have the same color as the parasites, all the patches that were undesirably cropped platelets only were classified as false positives". This quote comes from a search summary. — [Delgado-Ortet et al. 2020, Entropy, PMC7517192](https://pmc.ncbi.nlm.nih.gov/articles/PMC7517192/)

**Preprints and informal sources (weaker evidence)**
- [PP] Early-stage cells: "the model miss-classifies the red blood cells which are in an early stage of malaria - consisting of only a few parasites". Mislabeled infected cells are shown in Fig. 12 and FP/FN galleries in Fig. 13. Patient-level misses are attributed to "staining variations between patients". — [Rahman et al. 2019](https://arxiv.org/abs/1907.10418)
- [PP] False negatives "show systematically weaker spot signal … marginal, low-signal cells". False positives show "elevated spot count, area, and especially saturation, consistent with staining artifacts or debris". Patient-level sensitivity loss is concentrated in low-parasitemia patients. The NIH crops exclude "debris, stain precipitation, platelets, white blood cells, and other artifact categories present in the fuller NIH thin-smear taxonomy". — [EMFE 2026](https://arxiv.org/abs/2608.24793)
- [INF] An expert re-reader needed "weird", "bad segmentation" and "unsure" categories beyond the two classes, implying a non-trivial number of crops that are malformed or undecidable. — [IEEE DataPort, Delves relabelling](https://ieee-dataport.org/open-access/malaria-dataset-thin-blood-smear-updated)
- [PP] White blood cells are investigated as a false-positive source in African blood-smear images, a different dataset and task. I saw the title only. — [arXiv:2609.29663](https://arxiv.org/abs/2609.29663)

### Inferences
- **Suggested blinded triage rubric**, built from the categories above plus the Delves folders:

  | # | Category | Expected mostly in |
  |---|---|---|
  | C1 | Clear parasite visible (ring, chromatin dot or trophozoite) | FP in infected patients: candidate label error |
  | C2 | Faint or tiny dot, often at the cell edge (possible early ring or artefact) | FN; some FP |
  | C3 | Stain precipitate, debris or colour blotch on the cell | FP |
  | C4 | Overlapping small purple body (platelet-like) or other inclusion (Howell–Jolly-like) | FP; undocumented on NIH |
  | C5 | Segmentation or crop problem (cut or partial cell, two cells, mostly background) | Either |
  | C6 | Blur, illumination or colour cast | Either; patient-clustered |
  | C7 | Nothing visible | FN in infected patients: candidate label error, or a parasite out of the focal plane |
  | C8 | Cannot tell | Either |

- **How to read the triage.** False positives scored C3–C5 in control patients are almost certainly model errors. False positives scored C1, or false negatives scored C7, are the "candidate label errors". Report the counts with κ and the number of "cannot tell" cells, and call the categories "visual categories assigned by non-experts".
- **Overlap with patient clustering.** If most errors in the 7 high-error patients fall in C2 or C6, the residual error is driven by early stages or slide quality rather than labels. That is a useful, honest finding either way.

### Gaps
- I found no NIH-specific report on Howell–Jolly bodies, Pappenheimer bodies or stain precipitate frequency, and no published per-category error rates.
- The Delves folder counts are unknown, so how common "weird", "bad segmentation" and "unsure" crops are cannot yet be quantified.
- Platelet and white-blood-cell evidence comes from other datasets. Whether platelets overlapping red cells occur in NIH crops at a meaningful rate is undocumented.
