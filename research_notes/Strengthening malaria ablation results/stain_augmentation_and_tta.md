# Stain colour augmentation vs stain normalisation, and test-time augmentation (TTA), for a single-site malaria thin-smear cell classifier

Notes compiled 2 Nov 2026. Each source is tagged with its year, so older evidence (anything before about 2023) is easy to spot. Numbers marked **(computed)** are my own arithmetic (Python/scipy) on the team's reported A1/A2 statistics. They do not come from a source. Team baseline used throughout: A1 ensemble accuracy 98.45 %, MCC 96.90, 5,550 held-out cells from 40 patients, which is about 86 misclassified cells **(computed)**. For balanced classes with sensitivity ≈ specificity, MCC ≈ 2·acc − 1, and the team's numbers fit exactly (2 × 0.9845 − 1 = 0.969). So 1 pp MCC ≈ 0.5 pp accuracy ≈ 28 cells **(computed)**.

## 1. What does the evidence say about stain normalisation versus stain/colour augmentation for generalisation? When does normalisation help, and by how much?

### Takeaway
In the largest controlled comparisons, colour augmentation (HSV or HED jitter) is what produces cross-lab generalisation. These comparisons are Tellez 2019 (760 CNNs, 9 labs), Boschman 2022 (8 normalisers) and the MIDOG22 domain-generalisation benchmark. Once colour augmentation is in place, normalisation adds little or nothing. When training and test data come from one centre, normalisation gives no consistent benefit. It helps mainly on external multi-centre test sets, and most when the baseline has no colour augmentation; there, gains of +0.21 to +0.25 AUC are reported. Classical and GAN normalisers can also hurt, by as much as −10 to −19 points.

### Cited Findings
**Tellez et al. 2019, Medical Image Analysis 58:101544 (reference comparison; older)**
- Design. Four H&E patch tasks: mitosis, lymph-node metastasis, prostate epithelium, and 9-class colorectal tissue, on 128×128 patches. Every model was trained on a single centre (Radboudumc) and tested only on unseen external labs, 9 centres in all. There were 152 configurations × 5 repeats = 760 CNNs, scored by AUC per external set and combined into an average rank. — [Tellez 2019, arXiv:1902.06543](https://arxiv.org/abs/1902.06543) (DOI [10.1016/j.media.2019.101544](https://doi.org/10.1016/j.media.2019.101544))
- The best configuration overall was **no normalisation + HED-light colour augmentation** (mean rank 1.2 of 38). Every one of the top 10 used HSV or HED colour augmentation. The worst three were no normalisation + Basic (rank 37.6), + Morphology (37.2) and + brightness/contrast (BC) (36.2). — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- Effect size of adding colour augmentation (no normalisation, Basic → HED-light): lymph-umcu AUC 0.406 → 0.968; crc-labpon 0.556 → 0.973; prostate-cedar 0.624 → 0.879; mitosis-tupac 0.965 → 0.996. — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- Normalisation rescues models only when colour augmentation is absent. For example, lymph-umcu AUC with Basic augmentation was 0.406 without normalisation and 0.959 with their network normaliser. Normalisation on top of colour augmentation did not beat colour augmentation alone: Network + HED-light ranked 4.1, against 1.2 for Identity + HED-light. The authors write that "overall top performance was achieved without the use of color normalization" and that normalisation "is not a necessary condition". — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- Classical normalisers (LUT-based, and Macenko "deconvolution") "did not surpass the performance of Grayscale". The authors suggest they "hide certain useful features", adding input noise. Every normaliser did poorly without colour augmentation, scoring below Grayscale + BC (rank 12.2). — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- HSV vs HED showed "no substantial performance difference". Strong vs light was "similar … with a slight advantage towards light". Heavy augmentation cost "less than 1% average performance reduction on the internal test set" (same-centre test). — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- A nuance that matters for a pipeline without normalisation (like the team's): Identity + HSV-light ranked only 17.4 (lymph-cwh AUC 0.888), whereas Identity + HSV-strong ranked 4.7 and Identity + HED-strong 8.1. Normalised models were more robust to the choice of colour-augmentation strength. — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- Published ranges:
  - brightness ratio [0.65, 1.35], contrast [0.5, 1.5];
  - **HSV-light: hue and saturation ratios [−0.1, 0.1]; HSV-strong [−1, 1];**
  - **HED-light: [−0.05, 0.05]; HED-strong [−0.2, 0.2], for all HED channels;**
  - Gaussian noise σ [0, 0.1], blur σ [0, 0.1], scale [0.8, 1.2], elastic α [80, 120], σ [9, 11];
  - all ranges were tuned "manually via visual examination".

  HED augmentation separates stains by colour deconvolution with a fixed matrix, perturbs H and E independently, then converts back to RGB. — [Tellez 2019](https://arxiv.org/abs/1902.06543)

**RandStainNA, Shen et al., MICCAI 2022 (older)**
- Setup. Trained on NCT-CRC-HE-100K-NONORM (80/20 train/val) and tested externally on CRC-VAL-HE-7K (8 classes). Six backbones, 3 runs averaged. Every arm, including the baseline, used flips only as morphology augmentation. — [RandStainNA, arXiv:2206.12694](https://arxiv.org/abs/2206.12694) (DOI [10.1007/978-3-031-16434-7_21](http://dx.doi.org/10.1007/978-3-031-16434-7_21))
- EfficientNet-B0 test accuracy:
  - baseline 79.62 %;
  - HED-light stain augmentation 92.57; HSV-light 91.10; HSV-strong 91.76; LAB-light 93.66;
  - Reinhard-type normalisation in HSV 93.90, LAB 91.92, HED 91.34;
  - RandStainNA-HSV 94.81, RandStainNA-full 94.62.

  ResNet-18 went from 84.20 (baseline) to 93.85 (best normalisation) to 94.66 (RandStainNA-full). Transformers gained more: Swin-T rose from 88.80 (best normalisation) to 92.75 (RandStainNA-HSV). — [RandStainNA](https://arxiv.org/abs/2206.12694)
- Normalisation can hurt. On BACH with ResNet-18, accuracy fell from 72.68 % (baseline) to 62.50 % with normalisation in HED space (−10.2 pp), while RandStainNA reached 79.11 %. MobileNetV3 fell from 74.22 to 68.72 with HED normalisation. — [RandStainNA supplementary Tables 6–7](https://arxiv.org/abs/2206.12694)
- Baseline augmentation definitions (following Tellez): HED is "p′ = p·ε1 + ε2", i.e. per-channel scale plus shift; HSV is "p′ = p + p·ε", a multiplicative ratio; ε is uniform, with light and strong ranges. — [RandStainNA](https://arxiv.org/abs/2206.12694)
- Only means of 3 runs are reported, with no confidence intervals or significance tests. — [RandStainNA](https://arxiv.org/abs/2206.12694)

**Jahanifar et al., DG survey and benchmark (arXiv 2023)**
- Benchmarked 28 DomainBed algorithms plus "StainAug" with ResNet-50 on MIDOG22 mitosis-vs-mimicker patches from 5 domains, leave-one-domain-out, 1,260 runs. StainAug had the best F1, 76.0 ± 0.4 vs ERM 74.7 ± 0.2, i.e. +1.3 pp (accuracy 79.9 vs 79.1). Most sophisticated DG algorithms did not beat ERM. The authors find "no one-size-fits-all solution" and say "CPath-specific Stain Augmentation technique can be very effective". — [Jahanifar 2023, arXiv:2310.19656](https://arxiv.org/abs/2310.19656)

**Boschman et al., J Pathol (2021/2022)**
- Compared 8 normalisation algorithms. "Color normalization does not consistently improve classification performance when both training and testing data are from a single center." On four multi-centre datasets it improved external accuracy: ovarian **+0.25 AUC** (p = 1.6e-05) and pleural **+0.21 AUC** (p = 1.4e-10). Mixing images normalised by three algorithms, used as augmentation, "consistently improves" diagnosis on external centres. — [Boschman et al.](https://consensus.app/papers/details/6637be469eaf5ba1b9f5a133fcf4b29e/)

**Other comparisons**
- Franchet 2024, Comput Biol Med (single-centre training, multi-centre test, breast grading):
  - an H&E-specific stain augmentation (AugmentHE) gave at least 0.14 AUC more than RGB shift;
  - their augmentation + normalisation pipeline raised AUC on biased data by up to 21.7 % over usual augmentations;
  - "conventional normalization methods coupled with AugmentHE yielded similar results while being much slower".

  — [Franchet 2024](https://consensus.app/papers/details/a8857235903758fbafbe46723fff8294/)
- Otálora 2019: no single best technique. Colour augmentation and DANN "obtain most often the best results". — [Otálora 2019](https://consensus.app/papers/details/2678acc6a3e0503e8e9fba02e5cc3963/)
- Cong 2022 (CAGAN, a GAN normaliser): improved benchmark algorithms by 5–10 % over baselines *not using normalisation*. It was not compared against colour augmentation. — [Cong 2022](https://consensus.app/papers/details/5b4001439a2f5493ad701df596c72991/)
- Lin 2025, Sci Rep: a model trained on one batch of slides failed on recuts of the same blocks from the same lab (AUC 0.52–0.53 across batches vs 0.74–0.81 within a batch). Neither colour tuning nor CycleGAN normalisation fixed this. — [Lin 2025](https://consensus.app/papers/details/e0bd59e277cc55e0b82b37bdc254374f/)
- Xu et al. 2025 (BeerLaNet, arXiv preprint): StainGAN raised whole-blood-cell detection mAP50 from 65.2 to 89.6 but lowered malaria parasite detection from 91.03 to 81.67. Macenko lowered malaria detection to 72.03. The authors' reading is that generic normalisers "may perform well on small domain shift data … but fail to generalize to the large color shifts observed in the malaria dataset". — [Xu 2025, arXiv:2510.06592](https://arxiv.org/abs/2510.06592)
- Marini 2023 (DDCA) discards augmented samples whose colours fall outside a database of more than 2 million real H&E colour variations. It "can substantially improve classification performance on unseen data". — [Marini 2023](https://consensus.app/papers/details/86224557ca125befb4ddcbc289368e52/)

### Inferences
- The setting where normalisation pays off has two features: test images from other labs or scanners, and usually no colour augmentation. The team's A1/A2 design has neither: one hospital, one staining protocol, and test patients held out from the same lab. The literature therefore predicts a null for A2. Boschman's single-centre result is the closest published analogue.
- The large effect sizes for colour augmentation (+0.3 to +0.6 AUC, +12–15 pp accuracy) come from big inter-lab shifts with a baseline lacking colour augmentation. Under in-domain testing, the same papers report about zero or slight losses (Tellez: <1 % on the internal test). These magnitudes cannot be carried over to a same-site baseline at 98.45 %.
- From 2021 to 2025 the field has increasingly turned normalisation into augmentation (Boschman's mixing, RandStainNA, DDCA). The benefit comes from colour diversity during training, not from standardising colour. That points the team towards augmentation (Q4), not another normaliser.
- GAN/learned normalisers have mixed results, can hurt Giemsa data (BeerLaNet table) and cost far more than the remaining budget justifies. I would not recommend one here.

### Gaps
- I did not retrieve StainNet results, so there is no StainNet evidence in these notes.
- I found no study with the team's design (single site, patient-level hold-out) comparing normalisation with augmentation. All large comparisons use H&E histology, not Giemsa.
- Boschman, Franchet, Otálora, Cong, Lin and Marini were read from abstracts only (via Consensus), not full text. The Jahanifar benchmark is cited from its arXiv v1; I did not check whether it has a journal version.

## 2. Which malaria blood-smear studies (NIH dataset or others) test colour normalisation or augmentation, and what did they find?

### Takeaway
The evidence is thin:
- **On NIH data:** the one direct controlled test (Rahman et al., 2019 preprint) found stain normalisation *lowered* accuracy for all three models it tested, by 0.3 to 2.4 pp. Two small conference papers report gains from gray-world normalisation or LAB colour space, but from low baselines.
- **Across sites:** studies show strong site effects (an NIH-trained detector loses half its RBC-level sensitivity at another hospital), fixed by adding target-site data. None tested colour augmentation.
- **Across platforms:** a 2025 multi-platform Giemsa study found classical and GAN normalisers inconsistent and sometimes harmful.

I found no malaria study that ablates HSV or HED colour jitter.

### Cited Findings
- **Rahman et al. 2019 (arXiv preprint; NIH cells; 5-fold random image-level split, not patient-grouped).** Stain normalisation (Khan et al. method) vs none:
  - Custom CNN 94.99 % vs 96.29 %;
  - TL-VGG16 96.94 % vs 97.27 %;
  - CNN features + SVM 92.41 % vs 94.77 %.

  In the authors' words, "Stain normalization does not provide any improvement for any of the models". Standardisation and mean normalisation also gave no gain. — [Rahman 2019, arXiv:1907.10418](https://arxiv.org/abs/1907.10418)
- Rahman's explanation is that the normaliser "was originally developed for H&E stains; the samples from the NIH malaria dataset … does not have enough Hematoxylin". They add that its background-pixel filtering changes the images, and that "since the dataset have enough instances of each of the stains, the models worked better on dataset without stain augmentation". — [Rahman 2019](https://arxiv.org/abs/1907.10418)
- Rahman's training augmentation included an "HSV to RGB" colour-space change, contrast normalisation (0.5–1.5), rotation ±25°, shear, translation, cropping and Gaussian noise. "General data augmentation techniques performed significantly better." — [Rahman 2019](https://arxiv.org/abs/1907.10418)
- **Label noise.** A pathologist reviewed TL-VGG16's false positives and judged **38 % mislabelled**: clear parasites labelled uninfected. The full dataset was not reviewed. — [Rahman 2019](https://arxiv.org/abs/1907.10418)
- Rahman's patient-level aggregation (any positive cell makes a positive patient) gave TL-VGG16 93 % accuracy and AUC 86.5 %. The authors attribute the drop to staining variation between patients; that attribution is their interpretation, not a tested result. — [Rahman 2019](https://arxiv.org/abs/1907.10418)
- Swastika 2021 (J Phys Conf Ser): among the preprocessing options tested, gray-world normalisation gave the largest per-epoch accuracy gain and the best final accuracy (90.1 % ResNet-50, 93.1 % custom CNN). These are low baselines in a conference paper. — [Swastika 2021](https://consensus.app/papers/details/3123bd9094f656759b54c708b0bd4de9/)
- Syamsuddin 2025 (conference; MP-IDB thin smears; detection): LAB colour-space input raised YOLOv8 mAP50 from 0.612 to 0.687 and Faster R-CNN from 0.482 to 0.546. — [Syamsuddin 2025](https://consensus.app/papers/details/e462e0a9f23e586e9a68b8f0f5b1e976/)
- **Xu et al. 2025 (BeerLaNet, arXiv preprint, Johns Hopkins).**
  - *Classification:* Giemsa thin-smear *P. falciparum* life-stage classification, trained on one imaging platform and tested on two others (4 platforms in total; 2,486 training cells; test sets of 343 and 261). ResNet-18 6-class accuracy: baseline 21.32 %, Reinhard 29.34, Macenko 29.59, Vahadane 38.81, StainGAN 31.46, LStainNorm 21.17, BeerLaNet 48.66.
  - *Detection:* trained on 24,720 MGG-stained images and tested on 264 Zeiss Axioscan images (YOLOv8 mAP50): baseline 91.03, Reinhard 90.17, **Macenko 72.03**, Vahadane 92.10, **StainGAN 81.67**, BeerLaNet 95.07.
  - There was no colour-augmentation arm.

  — [Xu 2025](https://arxiv.org/abs/2510.06592)
- **Guillon et al. 2024 (arXiv; NIH plus 3 hospitals; smartphone ×1000; patient-grouped 5-fold CV).**
  - A ResNet-50 told NIH images from Hospital A images with 95 % accuracy (null 42 %).
  - An NIH-trained YOLOv5 fell from 89.2 % image-level accuracy on the NIH test set to 66.17 % at Hospital A. RBC-level sensitivity fell from 79.58 % to 38.81 %.
  - Joint training with Hospital A data restored image-level accuracy to 91.96 %. About 20 extra site images already helped, and about 200 reached a near-plateau.
  - "Specific augmentations and data preprocessing" were left for future work.

  — [Guillon 2024, arXiv:2408.08792](https://arxiv.org/abs/2408.08792)
- Guillon also reports earlier cross-setting drops: mAP fell from 62.8 to 36.7 between ×1000 and ×400 magnification ([Sultani et al., CVPR 2022](https://doi.org/10.1109/CVPR52688.2022.02003)). Thick-smear patient-level accuracy fell from 96.7 % to 83.1 % in a prospective smartphone-app evaluation ([Yu et al., Malaria J 2023](https://doi.org/10.1186/s12936-023-04446-0)). — [Guillon 2024](https://arxiv.org/abs/2408.08792)
- In the NIH field-image release used by Guillon, the patient count is 133 + 60 = 193, with 965 images (5 per patient). The NIH description says 150 infected and 50 healthy patients. — [Guillon 2024, Table 1](https://arxiv.org/abs/2408.08792); [Rahman 2019 dataset description](https://arxiv.org/abs/1907.10418)

### Inferences
- Rahman (random split, H&E normaliser) and the team's A2 (patient split, YUV equalisation) agree: normalisation as preprocessing does not help on the NIH cell set. A2 is consistent with the only prior malaria evidence.
- In the malaria literature, the real generalisation problem is between sites (Guillon, Sultani, Yu). A patient hold-out from the same hospital does not test it, so any benefit of normalisation or colour augmentation is largely invisible on the team's test set.
- If Rahman's label-noise rate carries over (roughly a third of false positives being label errors), part of the team's ~86 residual errors cannot be fixed by any image transform. This caps the achievable gain.

### Gaps
- I found no controlled HSV/HED colour-augmentation ablation in any malaria study.
- Mehanian et al. 2017 (multi-site thick smears, global white balance plus a "novel augmentation scheme") could not be retrieved. Only Rahman's secondary description was seen, so there are no numbers.
- Rahman's 38 % figure covers one model, a random split, one pathologist and false positives only. The paper is an arXiv preprint whose peer-review status I did not verify.
- I did not re-verify Umer et al. 2020's YUV results.

## 3. Why might YUV luma equalisation add nothing here?

### Takeaway
Three reasons compound:
1. **Little shift to remove.** There is one hospital and one protocol, and the literature finds that normalisation within a single centre does not consistently help.
2. **The transform does not normalise stain colour.** It equalises luma only, and luminance remapping is already randomised in training by CLAHE, brightness and contrast. The literature says that once augmentation is present, normalisation is largely redundant.
3. **Little headroom and low power.** There are ~86 errors, part of them probably label noise. The ensemble-level minimum detectable effect is ~0.8 pp MCC, so A2's −0.26 pp (CI −0.85 to +0.23) is what "no effect" looks like.

### Cited Findings
- With training and test from a single centre, normalisation "does not consistently improve classification performance"; gains appear on external centres. — [Boschman et al.](https://consensus.app/papers/details/6637be469eaf5ba1b9f5a133fcf4b29e/)
- Normalisation is "not a necessary condition" for top performance once colour augmentation is used. Classical normalisers do no better than grayscale and may "hide certain useful features". — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- On the NIH cell set, stain normalisation lowered accuracy for all models. The authors attribute this to an H&E-designed method on Giemsa images and to sufficient stain diversity already in the training data. — [Rahman 2019](https://arxiv.org/abs/1907.10418)
- Site signatures between hospitals are strong: a classifier separates NIH from another hospital with 95 % accuracy. All NIH images come from one site. — [Guillon 2024](https://arxiv.org/abs/2408.08792)
- When the shift is not about colour (different slide batches from the same lab), colour correction, including CycleGAN, did not restore performance. — [Lin 2025](https://consensus.app/papers/details/e0bd59e277cc55e0b82b37bdc254374f/)
- albumentations 0.5.2 facts relevant to the existing pipeline:
  - CLAHE is a uint8 transform whose `clip_limit` is a range (docstring default (1, 4); signature `CLAHE(clip_limit=4.0, tile_grid_size=(8, 8), p=0.5)`).
  - `RandomContrast(limit=0.2)` and `RandomBrightness(limit=0.2)` are deprecated subclasses of `RandomBrightnessContrast`.

  — [albumentations 0.5.2 transforms.py](https://github.com/albumentations-team/albumentations/blob/0.5.2/albumentations/augmentations/transforms.py)
- About 38 % of one NIH model's false positives were judged mislabelled by a pathologist. — [Rahman 2019](https://arxiv.org/abs/1907.10418)

### Inferences
- **Not a stain normaliser.** Equalising luma (Y) only, as the team's A2 is defined, leaves the U/V chroma channels unchanged. Stain hue and saturation therefore stay where they were, and those are the axes along which labs differ and which Reinhard, Macenko and RandStainNA act on. A2 is a contrast/brightness normalisation and does not test stain-colour normalisation.
- **Redundant with training augmentation.** CLAHE (itself a local histogram equalisation), RandomContrast and RandomBrightness sit in a OneOf with p = 0.3. If the five members have equal weight, each is applied to about 6 % of training images, and about 18 % get some luminance remap. The models are already trained to tolerate such remaps, so a deterministic equalisation adds no new information. On top of that, 10-model averaging smooths residual sensitivity. In this pipeline, CLAHE "clip 2" means a clip limit sampled from roughly [1, 2], given 0.5.2's range semantics.
- **Little colour shift to correct.** A1 already reaches 98.45 % on unseen patients from the same lab. That suggests colour differences between patients are not a major error source within this dataset, unlike the between-hospital shift Guillon measured.
- **Statistical power (computed from the team's A2 numbers).**
  - Ensemble level: the A2 CI [−0.85, +0.23] implies a patient-cluster bootstrap SE ≈ 0.276 pp MCC. The minimum detectable effect at 80 % power is **0.77 pp MCC** at α = 0.05, or 0.85 pp at α = 0.025. That is about 21–24 cells, roughly a quarter of all errors.
  - Fold level: A2's −0.60 pp with p = 0.13 (9 df) implies a corrected SE ≈ 0.36 pp. The minimum detectable effect is **1.13 pp MCC** (α = 0.05) or 1.30 pp (α = 0.025).
  - A2's ensemble estimate is about 0.94 SE below zero, which is entirely compatible with a true effect of 0.
- **Paired vs unpaired variance.** Back-calculating, the SD of paired fold differences is about 0.78 pp (assuming the 10-fold Nadeau–Bengio factor 1/10 + 1/9). That is about half of A1's raw fold-to-fold SD of 1.51 pp. Using the unpaired 1.51 pp would put the fold-level minimum detectable effect near 2.2 pp. Pairing is essential.
- **Possible harm mechanism (hypothesis, unverified).** If the crops have large uniform black backgrounds, a global (non-local) histogram equalisation's mapping is dominated by background pixels. It can then stretch the cell interior's intensities unpredictably from crop to crop. The team should visually inspect 20–30 A2 images.

### Gaps
- No paper directly tests whether luma-only equalisation becomes redundant once CLAHE/brightness/contrast augmentation is present. The redundancy argument rests on analogy (Tellez, Boschman) plus the mechanism above.
- I did not verify the background composition of the NIH crops or the inner weights of the team's OneOf. Both should be checked in the code.

## 4. If the team ran ONE more pre-registered arm, which colour augmentation is best supported, with which parameters, what effect size is plausible, could it be detected, and at what cost?

### Takeaway
- **Best supported:** Tellez's **HED-light** jitter (per-channel scale U(0.95, 1.05), shift U(−0.05, 0.05) in colour-deconvolution space). It ranked first of 38 configurations among models without normalisation, which is the team's setting. It needs a ~15-line `A.Lambda` around scikit-image's `rgb2hed`/`hed2rgb`.
- **Zero-code fallback:** HSV jitter via `A.HueSaturationValue` or `A.ColorJitter`, both present in albumentations 0.5.2. Tellez found HSV ≈ HED overall.
- **Honest expectation:** no measurable gain on held-out patients from the same hospital. The true effect is plausibly −0.5 to +0.3 pp MCC, while the design detects only ≥ ~0.8 pp (ensemble) or ≥ ~1.1 pp (fold mean), with power of only ~10–20 % for +0.3 pp.
- **Recommendation:** run it only as a newly pre-registered H3 with an equivalence margin, so that a null result is informative. Cost is about $2–3 and 15 minutes.

### Cited Findings
- Tellez ranges, defined on the [0, 1] scale of their colour spaces and tuned visually:
  - HSV-light: hue and saturation ratios [−0.1, 0.1];
  - HSV-strong: [−1, 1];
  - HED-light: [−0.05, 0.05];
  - HED-strong: [−0.2, 0.2].

  Without normalisation, the ranks were HED-light 1.2, HSV-strong 4.7, HED-strong 8.1 and HSV-light 17.4. HSV ≈ HED overall, light was slightly better, and the internal-test cost was <1 %. — [Tellez 2019](https://arxiv.org/abs/1902.06543)
- Common formulas: HED is p′ = α·p + β (RandStainNA's "p′ = p·ε1 + ε2"), and HSV is a ratio, p′ = p(1 + ε). With EfficientNet-B0 on an external H&E set, light HED and HSV augmentation scored 92.57 % and 91.10 %, against a baseline of 79.62 %. — [RandStainNA](https://arxiv.org/abs/2206.12694)
- An H&E-aware stain augmentation beat plain RGB shift by at least 0.14 AUC in a single-centre-train, multi-centre-test design. — [Franchet 2024](https://consensus.app/papers/details/a8857235903758fbafbe46723fff8294/)
- Stain augmentation was the best of 29 methods on MIDOG22 leave-one-domain-out: +1.3 pp F1 over ERM. — [Jahanifar 2023](https://arxiv.org/abs/2310.19656)
- **Colour transforms in albumentations 0.5.2:**
  - `HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.5)`;
  - `RGBShift(r_shift_limit=20, g_shift_limit=20, b_shift_limit=20, p=0.5)`;
  - `ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.2, p=0.5)`, where a hue tuple must lie in [−0.5, 0.5];
  - `FancyPCA(alpha=0.1)` (3-channel uint8);
  - `RandomGamma(gamma_limit=(80, 120))`, `ToGray`, `ChannelShuffle`, `ToSepia`;
  - `Lambda(image=None, …, name=None, p=1.0)`, which needs `name` for serialisation.

  No stain-specific (HED/H&E) transform appeared in the parts of the file I read. — [albumentations 0.5.2 transforms.py](https://github.com/albumentations-team/albumentations/blob/0.5.2/albumentations/augmentations/transforms.py)
- **Units in albumentations 0.5.2.**
  - `HueSaturationValue` on uint8: hue is shifted through a lookup table, `np.mod(lut + hue_shift, 180)`, so 1 unit = 2°. Saturation and value shifts are additive on a 0–255 scale and clipped.
  - On float images, hue is in degrees mod 360 and S/V are in 0–1.
  - `ColorJitter`'s hue factor is a fraction of a full turn (it adds 180·factor modulo 180 for uint8). Its saturation is a multiplicative blend with grayscale.

  — [albumentations 0.5.2 functional.py](https://github.com/albumentations-team/albumentations/blob/0.5.2/albumentations/augmentations/functional.py)
- **scikit-image.** `rgb2hed`/`hed2rgb` use the Ruifrok & Johnston (2001) colour deconvolution, with channels haematoxylin, eosin and DAB. `separate_stains`/`combine_stains` accept other built-in matrices, including **`bex_from_rgb`, documented as "Giemsa stain: Methyl Blue + Eosin"**. No azure-based matrix exists. — [scikit-image skimage.color API](https://scikit-image.org/docs/stable/api/skimage.color.html)
- An H&E normaliser was judged unsuitable for NIH Giemsa crops because they lack haematoxylin. — [Rahman 2019](https://arxiv.org/abs/1907.10418)

### Inferences
**Recommended H3, pre-registered as new; it is not a re-run of H2.** H3 states: "Adding Tellez HED-light colour augmentation to the A1 pipeline changes held-out-patient MCC."
- Arm A4 is the A1 pipeline exactly: same folds, seeds, 40 hold-out patients, 33 epochs, batch 16 and label smoothing 0.1. One transform is appended after the existing OneOf blocks, with p = 0.5. The value of p is my choice; Tellez sampled random magnitudes per image and does not state a probability.
- Sketch for TF 2.15 / albumentations 0.5.2 (verify the background threshold and the output scale):

  ```python
  import numpy as np, albumentations as A
  from skimage.color import rgb2hed, hed2rgb
  def hed_light(image, sigma=0.05, **kw):              # Tellez HED-light
      rgb = image.astype(np.float32) / 255.0
      hed = rgb2hed(rgb)
      hed = hed * np.random.uniform(1 - sigma, 1 + sigma, 3) + np.random.uniform(-sigma, sigma, 3)
      out = (np.clip(hed2rgb(hed), 0, 1) * 255).round().astype(np.uint8)
      cell = image.max(axis=-1, keepdims=True) > 10    # keep a black background black (check threshold)
      return np.where(cell, out, image)
  colour = A.Lambda(name="hed_light", image=hed_light, p=0.5)
  ```

- **Why HED and not BEX.** Pre-register the plain `rgb2hed` H&E matrix, so the arm is literally Tellez's published method and the citation is exact. Giemsa and H&E share eosin, and the blue-purple chromatin roughly takes the haematoxylin role, so HED is a usable, if non-physical, decomposition. Name skimage's Giemsa `bex` matrix as a deviation only if you choose it before seeing any results.
- **Scale check.** The numerical scale of `rgb2hed` output depends on the skimage implementation. Before registering, inspect about 50 augmented training cells, never test cells. Confirm that parasites (dark purple chromatin) stay visible and colours stay plausible. If they do not, shrink σ, and record the final σ in the pre-registration.
- **Zero-code fallback, equally defensible given HSV ≈ HED in Tellez.** Either of these, with brightness and contrast left to the existing pipeline:
  - `A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=0, p=0.5)`. That is ±20° hue and ±15/255 saturation, additive.
  - `A.ColorJitter(brightness=0, contrast=0, saturation=0.1, hue=0.05, p=0.5)`. That is ±18° hue, with multiplicative saturation, which is closer to Tellez's "ratio" definition.

  These are my mappings, not literature values. For Giemsa's pink-purple hues (about 0.8–0.95 of the hue circle), Tellez's multiplicative ±0.1 ratio corresponds to roughly ±30°, so ±20° is the conservative end of "light".
- **Avoid as the H3 arm:** `RGBShift`, which is weaker in the H&E literature; GAN normalisers; and any extra normaliser.

**Plausible effect and detectability (computed):**
- **Prior:** effect centred near 0, plausibly −0.5 to +0.3 pp MCC (−14 to +8 cells). Reasons: Tellez's in-domain cost of heavy colour augmentation was <1 %; Boschman found no consistent single-centre effect; A2 came in at −0.26 pp; and the +1.3 pp F1 from MIDOG22 was cross-domain, so it is an unlikely upper bound here.
- **Power at ensemble level** (patient-cluster bootstrap, SE ≈ 0.276 pp): 6.5 % for +0.1 pp, 11 % for +0.2, 19 % for +0.3, 44 % for +0.5. The 80 %-power minimum detectable effect is 0.77 pp (α = 0.05), or 0.85 pp with a Holm-style α = 0.025.
- **Power at fold level** (Nadeau–Bengio corrected t, SE ≈ 0.36 pp, 9 df): 12 % for +0.3 pp, 24 % for +0.5 pp. The minimum detectable effect is 1.13 pp (α = 0.05) or 1.30 pp (α = 0.025).
- **Answer to "could 40 patients or 10 folds detect it?":** no, not at plausible sizes. Detection needs at least ~21–24 fewer errors out of ~86.

**Decision rules to pre-register:**
- *Success:* ensemble ΔMCC > 0 with a 95 % patient-cluster bootstrap CI excluding 0, **and** a Holm-adjusted fold-level Nadeau–Bengio p below α.
- *Informative null (equivalence):* pre-register a smallest effect of interest, for example ±1.0 pp MCC (≈28 cells, about a third of the errors). Declare "no meaningful effect" if the 90 % CI lies inside ±1.0 pp, i.e. two one-sided tests. With SE ≈ 0.276, the 90 % half-width is about 0.45 pp, so equivalence is achievable if |Δ| ≲ 0.55 pp.
- *Harm:* CI entirely below 0.
- *Otherwise:* inconclusive.
- Report the result whatever the outcome.

**Ways to raise power (pre-register in advance):**
- If A1's 10 CV folds were patient-grouped, the out-of-fold predictions cover the remaining 160 patients. A secondary analysis pooling them evaluates 4× as many patients. That shrinks the cluster-bootstrap SE by about √(40/160) = ½, bringing the ensemble minimum detectable effect to about 0.4 pp. Still large, but more informative.

**Cost:**
- Training the arm costs about $2–3 and 15 minutes on 10 × RTX 4090 (the team's figure).
- HSV transforms are OpenCV lookup tables with negligible overhead.
- The skimage HED path is CPU NumPy work done per image. Benchmark one epoch first, apply it at the native crop size (~110–150 px) before resizing to 224 if possible, or reimplement as log → 3×3 matmul → exp in TensorFlow on the GPU.
- Implementation and visual checks take about 2–4 person-hours (estimate).

**The experiment that could actually show a benefit.** Colour augmentation's documented value is robustness *across sites*. Evaluating the A1 and A4 models, unchanged, on an external Giemsa thin-smear set would test that mechanism directly. One option is P. falciparum cells cropped from MP-IDB, which exists as a public thin-smear set ([Syamsuddin 2025](https://consensus.app/papers/details/e462e0a9f23e586e9a68b8f0f5b1e976/)). This needs cell cropping and should be labelled exploratory. On the same-hospital split, a null is the expected and largely uninformative result.

### Gaps
- No Giemsa-specific colour-augmentation ranges exist in the literature I found. All published ranges come from H&E.
- Whether skimage's `bex` "Giemsa" matrix fits Romanowsky-stained thin smears better than HED is untested.
- I found no malaria study that ablates colour augmentation, so the effect-size prior is reasoned by analogy, not measured.
- Whether A1's CV folds were patient-grouped, which determines whether the out-of-fold power boost is valid, is unknown to me.

## 5. How much does TTA gain in medical image classification? D4 TTA when training already covers all 8 orientations, effect on calibration, malaria-specific results, realistic gain, and whether it is worth reporting

### Takeaway
TTA gains are typically small:
- about +0.2 to +2.8 pp top-1 at 70–92 % baselines on natural-image benchmarks;
- +0.25 to +0.48 pp for *single* models on the NIH malaria data (random split; the only malaria-specific result I found);
- shrinking to about 0 for 10-member deep ensembles on small images;
- negative when TTA views fall outside the training distribution (a 2026 preprint reports −10 to −32 pp on 28×28 MedMNIST with augmentations the models were not trained on).

For this team, D4 views are already in training and the predictor is a 10-model ensemble at 98.45 %, so the realistic gain is about 0–0.1 pp accuracy, i.e. 0–6 cells. It is free, so run it, but report it as an exploratory robustness and calibration check (E1), not as an improvement.

### Cited Findings
- **Shanmugam et al., ICCV 2021 (older).** Standard TTA (flips × 5 crops × 3 scales = 30 views, mean-aggregated) vs the original prediction:
  - ImageNet: ResNet-50 75.78 → 76.91 (+1.13), ResNet-18 69.37 → 71.02, MobileNetV2 71.38 → 72.69, InceptionV3 69.66 → 72.45;
  - Flowers-102: ResNet-50 91.72 → 91.96 (+0.24), MobileNetV2 90.28 → 90.47 (+0.19);
  - CIFAR-100 CNN: 74.15 → 75.48; STL-10: 77.92 → 78.58.

  — [Shanmugam 2021, arXiv:2011.11156](https://arxiv.org/abs/2011.11156)
- From the same paper:
  - For ResNet-18 on ImageNet, "a little over one third of the labels changed by the standard TTA policy are incorrect".
  - "The benefit of simple averaging (Mean) diminishes with larger networks."
  - The size of the TTA gain correlated with examples per class (r = 0.95).
  - An expanded policy with intensity transforms *reduced* CIFAR-100 accuracy (74.37 → 73.41).
  - Learned weights for contrast, brightness, cut-out and shear augmentations went to 0.

  — [Shanmugam 2021](https://arxiv.org/abs/2011.11156)
- **Ashukha et al., ICLR 2020 (older).** Their TTA draws one random augmentation per ensemble member, keeping compute equal.
  - ImageNet ResNet-50: a single model improves from 23.86 % error to 21.06 % with 50 TTA samples. A 10-member deep ensemble improves from 20.90 to 20.16, and a 5-member one is unchanged (21.19 vs 21.20).
  - **CIFAR-10, 10-member deep ensembles:** VGG16 4.57 → 4.73 (worse), ResNet-110 3.63 → 3.58, ResNet-164 3.50 → 3.46, WideResNet 3.01 → 3.02 (≈0).
  - Their explanation: "the performance gain for powerful ensembles … on CIFAR datasets is not as dramatic … likely due to the fact that CIFAR images are small".

  — [Ashukha 2020, arXiv:2002.06470](https://arxiv.org/abs/2002.06470)
- **Ashukha on calibration.** On ImageNet, TTA "improves accuracy but decreases the uncalibrated log-likelihood of deep ensembles"; it "breaks the nearly optimal temperature". The authors attribute this decalibration to extreme random crops. With milder augmentation, TTA "often improves the calibration of an ensemble". Temperature scaling "is a must" for fair comparison. — [Ashukha 2020](https://arxiv.org/abs/2002.06470)
- **Veeling et al., MICCAI 2018 (older, PCam).**
  - "CNNs trained on histopathology data exhibit erratic fluctuations in predictions under input rotation and reflection."
  - A P4M rotation-reflection-equivariant DenseNet reached NLL 0.260, accuracy 89.8 and AUC 96.3. A DenseNet trained *with* 90° rotation and reflection augmentation reached 0.306, 88.1 and 95.1. Without augmentation it reached 0.315, 87.6 and 95.5. So augmentation alone did not deliver invariance.
  - TTA averaging over 90°-rotated and mirrored versions "comes at 8 times the computational cost and does not provide guarantees on equivariance".
  - The paper reports no TTA numbers.

  — [Veeling 2018, arXiv:1806.03962](https://arxiv.org/abs/1806.03962)
- **Malaria-specific TTA, Rahman et al. 2019** (NIH, random image-level split, single models). TTA used augmentations similar to training (rotations, shifts, shear, crop, contrast, colour space, noise), averaged with equal weights. TL-VGG16 went from 97.64 % to **97.89 % (+0.25 pp)** and the custom CNN from 95.97 % to **96.45 % (+0.48 pp)**. The 3-model ensemble without TTA scored 97.78 %. — [Rahman 2019](https://arxiv.org/abs/1907.10418)
- **Medeiros 2026 (arXiv preprint, single author).**
  - Setup: MedMNIST v2 at 28×28; four architectures trained from scratch, with BatchNorm statistics "accumulated … on unaugmented images". Mixed TTA (flips, ±15° rotation, resized crop 0.8–1.0, brightness/contrast ±0.3, blur) with 50 views.
  - Results: ResNet-18 PathMNIST 0.870 → 0.554 (**−31.6 pp**), BloodMNIST 0.957 → 0.857 (−10.0 pp), DermaMNIST 0.742 → 0.758 (+1.6 pp). TTA hurt in 11 of 12 combinations.
  - Intensity-only TTA was less harmful (BloodMNIST ResNet-18: 0.901, vs 0.881 geometric and 0.854 mixed).
  - Adding the original image to the views cut the drop at N = 1 (BloodMNIST ResNet-18: from −21.1 % to −2.6 %).
  - Calibration went both ways: ECE 0.196 → 0.039 (DermaMNIST ResNet-18) but 0.011 → 0.136 (BloodMNIST SmallCNN).
  - The authors' own limitations: low resolution and training from scratch. Its code repository is named "AI-Scientist-v3".

  — [Medeiros 2026, arXiv:2604.09697](https://arxiv.org/abs/2604.09697)
- **Calibration methods built on TTA.**
  - Adaptive-TTA "improves uncertainty calibration without affecting the model's accuracy" (Brier score). It beat temperature scaling on CIFAR-10/100 and AID. — [Conde 2022](https://consensus.app/papers/details/45ac602f419d597b9ed3cccaaf70e794/)
  - A TTA extension of post-hoc calibration gave "substantially better calibration", shown on skin-cancer classification under real-world shift. — [Hekler 2023](https://consensus.app/papers/details/4de8ee8607755240a963802d235867e4/)
  - In MRI segmentation, TTA-based uncertainty "helps to reduce overconfident incorrect predictions". — [Wang 2019](https://consensus.app/papers/details/d11ce8157137538192afa6fd15be7922/)

### Inferences
- **Why D4 TTA is safe here, unlike in Medeiros.** The team trained with RandomRotate90, Flip and Transpose, so all 8 D4 views are in-distribution and BatchNorm statistics were collected on them. Averaging over the full D4 group also makes each model's output *exactly* invariant to the 8 orientations, by construction. That removes the residual orientation "fluctuations" Veeling describes. Do **not** add colour or intensity TTA: the models never saw colour jitter, and Shanmugam and Medeiros show untrained test-time transforms can hurt.
- **Realistic gain (estimate).**
  - Per model: roughly +0.1 to +0.5 pp accuracy, consistent with Rahman's single-model +0.25 to +0.48 pp.
  - Ensemble of 10: about 0 to +0.1 pp accuracy (0–6 cells, ≤ 0.2 pp MCC). Ensembling already removes most of the variance TTA would remove (Ashukha, CIFAR), and the images are small (~110–150 px crops upsampled to 224).
  - Expect a handful of cells to flip in *both* directions (Shanmugam).
- **Detectability nuance.** TTA compares the *same* models on the *same* cells, so only flipped cells contribute to the paired variance. Its bootstrap SE will be far smaller than the 0.276 pp of a retrained arm. A 3-cell net gain could therefore come out "significant" and still be trivial. Pre-specify a minimal important difference, e.g. 0.5 pp MCC, and report effect sizes and CIs rather than p-values.
- **E1 protocol (exploratory; costs essentially nothing).**
  - For each of the 10 models in A1, and separately in A2 and A3, predict the 5,550 held-out cells under the 8 D4 transforms: `tf.image.rot90(x, k)` for k = 0–3, each with and without `tf.image.flip_left_right`. The identity is one of the 8.
  - Average softmax over the 8 views per model, then over the 10 models (an 80-prediction mean), and keep the 0.5 threshold.
  - Load: 444,000 forward passes per arm, a few minutes on one GPU (estimate). Saved per-cell predictions cannot be reused; new forward passes are needed.
  - Report:
    - ensemble ΔMCC and Δaccuracy with the same patient-cluster bootstrap;
    - per-model Δ;
    - the counts of cells flipped correct → wrong and wrong → correct;
    - ECE (15 bins), Brier and NLL, both raw and after temperature scaling fitted on *validation folds* (never the test set).
  - Also check whether the H2 conclusion, A2 vs A1, is unchanged under TTA.
- **Calibration expectation (hypothesis).** Label smoothing 0.1 already caps confidence, and averaging 80 predictions softens it further. ECE may therefore rise through *under*-confidence even if accuracy is flat, which is why the temperature-scaled numbers matter.
- **Is it worth reporting?** Yes, as a short exploratory robustness/calibration table: "D4 TTA did not measurably change ensemble MCC (Δ = x pp, 95 % CI …)". That shows the H1/H2 conclusions are not artefacts of orientation sensitivity. It should not be presented as a performance improvement or folded into H2/H3.

### Gaps
- I found no peer-reviewed study that quantifies D4 TTA on top of D4-trained *ensembles* for cell or patch crops. Veeling gives the motivation but no TTA numbers.
- Rahman 2019 is the only malaria-specific TTA result I found: a preprint with a random split and single models, not ensembles. A targeted search for "test-time augmentation" with malaria cell classification (Nov 2026) returned only papers that use augmentation at training time.
- I did not retrieve evidence on how label smoothing interacts with TTA calibration.
- Medeiros 2026 is an unreviewed preprint, apparently generated with an AI-scientist pipeline, on 28×28 images and models trained without augmentation. Treat it as a caution about off-distribution TTA, not as evidence about this setup.
