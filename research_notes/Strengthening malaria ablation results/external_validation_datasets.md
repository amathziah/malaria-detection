# External validation datasets and cross-dataset generalisation for NIH-trained malaria single-cell classifiers

Scope: public thin-smear datasets that could serve as an external test set for models trained on the NIH/NLM "Malaria Cell Images" crops, and what published NIH-to-external experiments found. Links, file sizes and licences were checked on 2026-11-02 with curl, the GitHub API and the Harvard Dataverse API, unless a finding says otherwise. "Capstone" below means an unpublished MSc project (Noah Tjon Sien Kie, repository created 2026-09-29), which is not peer reviewed and reports one training seed per model. It is used because it ran exactly the experiment this team is considering.

## 1. Which public datasets could serve as an external test set, and what are their properties?

### Takeaway
Four public Giemsa thin-smear datasets from other sites label individual cells in a way that can be turned into single-RBC crops: MP-IDB (P. falciparum plus three other species, Switzerland), BBBC041 (P. vivax, Brazil and Thailand), IML-Malaria and M5 (both P. vivax, Pakistan). The Lacuna thin sets (Uganda and Ghana) box parasites but have no uninfected-RBC class. The NLM's own thin-smear image release (NIH-NLM-ThinBloodSmearsPf) and its 2025 MIRA re-annotation come from the same Chittagong patients and photographs as the 27,558 training crops, so they are not external and using them would leak. The NLM Sudan release is the closest match in acquisition (the same NLM smartphone app, P. falciparum, a new country), but it has only per-image counts and is a 49 GB download.

### Cited Findings

**Overview.** Details and sources are in the bullets that follow the table.

| Dataset | Species | Smear, stain | Site | Scale | Cell-level labels | Licence | Download (checked 2026-11-02) |
|---|---|---|---|---|---|---|---|
| NIH-NLM-ThinBloodSmearsPf (Kassim 2021) | P. falciparum | thin, Giemsa | Chittagong, Bangladesh (same as training) | 193 patients, 965 images | every RBC/WBC as a polygon (165 images) or a point (800 images) | NLM notice: any use, with attribution | 690 MB zip, HTTP 200. **Not external** |
| MIRA boxes (Wilm 2025) | P. falciparum | thin, Giemsa | same images as above | 800 images | a box on every cell | article CC BY 4.0 | Zenodo DOI returned 403 to a script. **Not external** |
| NLM thin P. vivax | P. vivax | thin | not stated | 171 patients | parasites | n/a | link "TBD", never released |
| NLM Malaria Screener Sudan (Yu 2023) | P. falciparum + P. vivax | thin + thick, Giemsa | 2 hospitals, Sudan | 190 patients; 875 thin images | none (counts per image only) | NLM notice: any use | 49.2 GB zip listed |
| MP-IDB (Loddo 2019) | Pf, Pv, Pm, Po | thin, Giemsa | Switzerland | 210 images in the repo (paper: 229) | parasite masks and stage letters; no uninfected labels | MIT | ~3.1 GB repo, HTTP 200 |
| BBBC041 (Hung 2018) | P. vivax | thin, Giemsa | Brazil (Manaus, Acre), Thailand | 1,364 images, ~80,000 cells | a box on every cell; 6 classes + "difficult" | CC BY-NC-SA 3.0 | 2.26 GB zip, HTTP 200 |
| IML-Malaria (Arshad) | P. vivax | thin, Giemsa | Lahore, Pakistan | 345 images, 38,449 boxes | a box on every cell; stages | none stated | ~46 MB repo, HTTP 200 |
| M5 (Sultani, CVPR 2022) | P. vivax | thin | Pakistan | 7,542 images (1,257 regions × 3 magnifications × 2 microscopes) | boxes on malarial cells; stages | none stated | 23 GB on Google Drive, HTTP 200; project page unreachable |
| Lacuna thin, Uganda (Nakasi 2025) | not stated | thin | Kiruddu and Mulago hospitals, Uganda | 1,000 images | parasite/WBC boxes; no uninfected class | CC BY 4.0 (Dataverse) | 0.73 GB RAR |
| Lacuna thin, Ghana | not stated | thin | Princess Marie Louise Children's Hospital, Accra | 1,000 images | stage/WBC boxes; no uninfected class | CC BY 4.0 (Dataverse) | 1.51 GB RAR |
| Tanzania NM-AIST (Lufyagila 2024) | not stated | thin + thick, Giemsa | Tanga region, 5 facilities | 75 samples; 1,334 thin images | image-level labels only | CC0 1.0 | 2.98 GB total |
| PlasmoCount (Davidson 2021) | P. falciparum (in-vitro culture) | thin, Giemsa | laboratory cultures | ~38,000 RBCs | per-RBC labels, stages | CC BY 4.0 | Mendeley, HTTP 200 |
| PlasmoID (Nugroho 2022) | Pf, Pv, Po, Pm | thin | Indonesia | 559 images, 691 parasites | parasite detection/segmentation | not found | no download link found |
| Chula RBC-12 | none (RBC morphology only) | thin | Chulalongkorn Univ., Thailand | 706–738 images, >20,000 cells | points with 12 morphology classes | none stated | ~0.2 GB repo, HTTP 200 |

**Training set (reference point)**
- The NIH crops come from Giemsa thin smears of 150 P. falciparum-infected and 50 healthy patients. They were photographed with "a standard Android smartphone attached to a conventional light microscope" at Chittagong Medical College Hospital and annotated by an expert slide reader at the Mahidol-Oxford Tropical Medicine Research Unit, Bangkok. RBCs were segmented with a level-set algorithm — [Rajaraman et al. 2018, PeerJ 6:e4568](https://doi.org/10.7717/peerj.4568)
- cell_images.zip is 353,452,851 bytes (last modified 2024-08-28). Patient-to-cell mapping CSVs are published next to it — [NLM data index](https://data.lhncbc.nlm.nih.gov/public/Malaria/index.html); [NLM malaria datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)
- The crop filenames carry a "C-number" case ID, which gives 200 patient groups — [Hou et al. 2026, MalariaNet, Biosensors 16(7):358](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/)

**NIH-NLM-ThinBloodSmearsPf and MIRA boxes: same source, not external**
- 193 patients (148 infected, 45 uninfected), 5 images each, 5312 × 2988 px with a circular eyepiece field, photographed by smartphone at Chittagong Medical College Hospital. In the "polygon set" every RBC and WBC is outlined; in the "point set" each cell is marked with a point — [ReadMe.pdf](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/ReadMe.pdf)
- Polygon set: 33 patients, 165 images, 34,213 RBCs (1,142 infected, 33,071 uninfected), 51 WBCs. Point set: 160 patients, 800 images, 162,450 RBCs (6,810 infected, 155,640 uninfected), 220 WBCs — [Dataset_statistics.xlsx](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/Dataset_statistics.xlsx)
- The zip is 690,355,704 bytes. The licence permits "any commercial or non-commercial purpose" as long as the notice is kept, the credit "Courtesy of the U.S. National Library of Medicine" is given, and Kassim et al. is cited — [folder index](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/index.html); [Data License Agreement](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/Data%20License%20Agreement.docx); [Kassim et al. 2021, IEEE JBHI 25(5):1735](https://ieeexplore.ieee.org/document/9244549)
- The NLM datasheet lists the 27,558-cell zip and the patient-to-cell CSVs in the same "thin smears, falciparum" row as this image set. Its label list also includes Gametocyte, Dead_Parasite, Parasite_Outside_Cell, Stain_Precipitation, Platelet and others — [NLM datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)
- Evidence of overlap: patient folders in the statistics sheet (e.g., "142C38P3thinF_original", "143C39P4thinF_original") use the same C-number codes as the crops — [Dataset_statistics.xlsx](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/Dataset_statistics.xlsx). A per-photograph cross-check found the same patient and photo IDs in both cell_images and the point set (e.g., patient C100, IMG_20150918_144104, point-set folder 248C100P61ThinF) — [capstone, outputs/tables/nih_source_overlap.csv](https://github.com/noahtjonsk/malaria-cross-dataset)
- MIRA re-annotation: Cellpose plus manual correction converted the 800 point-set images to boxes. Counts are 155,201 non-infected, 6,805 infected, 220 WBC, and 19,592 "ambiguous" cells, mostly at field borders. The authors say the original set was probably annotated by a single expert and that cells on image borders were often left unlabelled. The data are on Zenodo (doi:10.5281/zenodo.17514694) — [Wilm et al. 2025, arXiv:2507.18483](https://arxiv.org/abs/2507.18483). The DOI returned HTTP 403 to a scripted request on 2026-11-02, probably bot blocking; I did not check it in a browser.

**NLM thin-smear P. vivax**: 171 infected patients, parasite annotations, 3024 × 4032 TIFF; the download link is "TBD" — [NLM datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)

**NLM Malaria Screener Sudan dataset (Yu et al. 2023)**
- 190 patients: 100 positive (P. falciparum and/or P. vivax) and 90 negative. They come from two primary hospitals, Alsororab (SOR) and Gezira Slanj (GS), 95 patients each, with one slide per patient carrying a thick and a thin smear. WHO Level 1 microscopists gave image-level counts only; for thin smears these are the RBC count and the infected-RBC count. There are 875 thin images (4.6 per patient), and 220,686 RBCs and 395 infected RBCs were counted on them — [Sudan Readme.pdf](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/Readme.pdf)
- P. falciparum thin images: 90 at GS and 197 at SOR. Infected RBCs counted on P. falciparum thin images: 75 at GS and 261 at SOR. Images are PNG, 4128 × 3096 at GS (landscape) and 3096 × 4128 at SOR (portrait). The readme warns that "Thin smear images of positive patients can have a zero count for infected RBCs", because positivity was decided on thick smears — [Sudan Readme.pdf](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/Readme.pdf)
- SudanData.zip is 49,174,857,598 bytes (~49 GB), last modified 2024-08-28 — [MalariaScreener index.json](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/index.json). The licence is an NLM notice allowing "any commercial or non-commercial purpose" — [Data-License-Agreement.pdf](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/Data-License-Agreement.pdf)
- Smears were stained with 3 % Giemsa for 45 min following WHO procedure, and the dataset is public at the NLM URL — [Yu et al. 2023, Malar J 22:33](https://pmc.ncbi.nlm.nih.gov/articles/PMC9883923/). Images were taken with a smartphone on an Olympus CX23 microscope — [Isewon dataset catalogue, Yu et al. 2023 entry](https://github.com/ItunuIsewon/Malaria_Blood_Film_Images)

**MP-IDB (Malaria Parasite Image Database)**
- Four species (Falciparum, Malariae, Ovale, Vivax). The life stages present in each image are coded in its filename (R, T, S, G), and each image has expert ground truth. The repository licence is MIT — [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis); [Loddo et al. 2019, SaMBa/LNCS 11379](https://doi.org/10.1007/978-3-030-13835-6_7)
- Repo contents via the GitHub API on 2026-11-02:
  - Falciparum: 104 images, 104 masks and 1,297 parasite crops.
  - Vivax: 40 images and 64 crops. Malariae: 37 images. Ovale: 29 images. That is 210 images in all.
  - The 104 Falciparum images come from only 10 distinct smear prefixes.
  - A sample image is a 2592 × 1944 JPEG.
  - The API reports a repository size of 3,113,149 KB (~3.1 GB), and the master.zip link resolves.
  
  Source: [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis)
- Other descriptions give 229 images (122 Pf, 37 Pm, 29 Po, 46 Pv) and state that "each image with the same part number [prefix] refers to the same patient" — [danielbarco/malaria_datasets](https://github.com/danielbarco/malaria_datasets). The M5 paper also counts MP-IDB as 229 images with 840 malarial cells and no boxes — [Sultani et al. 2022](https://arxiv.org/abs/2111.13656)
- Falciparum crops by stage: 1,230 rings, 18 schizonts, 42 trophozoites and 7 gametocytes. MP-IDB "has parasite crops and not healthy RBCs" — [Loddo, Fadda, Di Ruberto 2022, J Imaging 8(3):66](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/). A count of the filename stage letters gives similar proportions: of the 104 Pf images, 87 contain rings, 15 trophozoites, 17 schizonts and 7 gametocytes — [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis)
- Site: Switzerland — [Isewon catalogue, Summary_Table.md](https://github.com/ItunuIsewon/Malaria_Blood_Film_Images); "CHUV Lausanne" — [capstone README](https://github.com/noahtjonsk/malaria-cross-dataset)

**BBBC041 (P. vivax, Broad Bioimage Benchmark Collection)**
- 1,364 images (~80,000 cells) in three sets, from Brazil, Southeast Asia and a time course. Giemsa stain. Each cell has a class and a box. Classes are RBC and leukocyte (uninfected) and gametocyte, ring, trophozoite and schizont (infected), plus "difficult". Uninfected RBCs dominate heavily. malaria.zip is 2.26 GB (2,259,224,287 bytes; last modified 2018-08-27) under CC BY-NC-SA 3.0 — [BBBC041](https://bbbc.broadinstitute.org/BBBC041)
- The data are ex vivo samples from P. vivax patients in Manaus (Brazil) and Thailand, used for training and validation; Brazil (Acre) data form the test set. Thin smears were Giemsa-stained, and RBCs are about 97 % of ~100,000 cells. Manaus parasites were enriched by cellulose/Percoll purification, and Thailand samples were cultured ex vivo to schizont stage. The paper says "all non-RBC objects were annotated (boxed and labeled) by an expert malaria researcher" — [Hung et al. 2018, arXiv:1804.09548](https://arxiv.org/abs/1804.09548)
- The Kaggle mirror (kmader/malaria-bounding-boxes) returned HTTP 404 on 2026-11-02. Download from the Broad URL instead — [BBBC041](https://bbbc.broadinstitute.org/BBBC041)

**IML-Malaria**
- P. vivax, from a Lahore hospital in Pakistan. 345 images of Giemsa-stained slides, about 38,000 cells boxed, with infected cells labelled by life stage — [Arshad et al., arXiv:2102.08708](https://arxiv.org/abs/2102.08708). Images and a JSON file of per-cell boxes are on GitHub — [IML-Malaria GitHub](https://github.com/QaziAmmar/A-Dataset-and-Benchmark-for-Malaria-Life-Cycle-Classification-in-Thin-Blood-Smear-Images)
- Computed from annotations.json on 2026-11-02:
  - 345 images, 38,449 boxes.
  - 37,899 "red blood cell" boxes.
  - 529 infected: 261 gametocytes, 164 rings, 77 trophozoites, 27 schizonts.
  - 21 "difficult".
  - Median box 82 × 82 px.
  - The GitHub API reports no licence and a repository size of ~46 MB.
  
  Source: [IML-Malaria GitHub](https://github.com/QaziAmmar/A-Dataset-and-Benchmark-for-Malaria-Life-Cycle-Classification-in-Thin-Blood-Smear-Images). The 529 infected cells match the M5 paper's comparison table — [Sultani et al. 2022](https://arxiv.org/abs/2111.13656)

**M5 (multi-microscope, multi-magnification malaria)**
- Thin smears from P. vivax patients in Pakistan. 1,257 malarial regions were imaged at 100×, 400× and 1000× on a high-cost microscope (Olympus CX23, ~3,000 USD) and a low-cost one (XSZ-107BN, ~160 USD), giving 7,542 images. There are 20,331 malarial-cell boxes (3 × 3,624 on the high-cost microscope + 3 × 3,153 on the low-cost one). A haematologist annotated at 1000× on the high-cost microscope, and boxes were transferred to other magnifications by homography and then checked by hand. Photos were taken with a Honor 9x Lite phone — [Sultani et al., CVPR 2022, arXiv:2111.13656](https://arxiv.org/abs/2111.13656)
- 23 GB in total, PNG images with Pascal VOC annotations, on Google Drive and OneDrive; the repository has no licence — [M5 GitHub](https://github.com/intelligentMachines-ITU/LowCostMalariaDetection_CVPR_2022). The Google Drive folder returned HTTP 200, but the project page http://im.itu.edu.pk/m5-malaria-dataset/ did not connect on 2026-11-02.

**Lacuna Malaria Datasets (Makerere AI Lab, Uganda, and Ghana)**
- On Harvard Dataverse the collection is "Lacuna Malaria Datasets", licensed CC BY 4.0, released 2024-08-08, 7 files totalling 7.23 GB. Files include Thin_Uganda.rar (729,815,904 bytes), Thin_Images_Ghana.rar (1,513,527,392 bytes), three Thick_Ghana parts and one datasheet per country — [Dataverse doi:10.7910/DVN/VEADSE](https://doi.org/10.7910/DVN/VEADSE)
- Uganda:
  - 3,000 thick and 1,000 thin labelled images from Mulago Hospital and Kiruddu National Referral Hospital.
  - Smartphones were attached to an Olympus CX-23 with a 3D-printed adapter; at most 10 images were taken per thin slide.
  - Objects annotated on thin images: "Parasitized cell" 1,093, Trophozoite 53, WBC 984, Artefacts 7.
  - Slides were routine slides in the "pre-disposal stage".
  - The article is CC BY-NC 4.0.
  
  Source: [Nakasi et al. 2025, Data in Brief 58:111190](https://pmc.ncbi.nlm.nih.gov/articles/PMC11719325/). The Uganda datasheet adds YOLO-format boxes, the VGG Image Annotator, and capture at Kiruddu between August 2022 and February 2023 — [Dataverse](https://doi.org/10.7910/DVN/VEADSE)
- Ghana: 3,000 thick and 1,000 thin images from Princess Marie Louise Children's Hospital in Greater Accra, taken with a mobile phone. Thin-smear labels are gametocytes, trophozoites, ring, WBC and artifacts, boxed with makesense.ai and partly model-assisted. The datasheet notes "some instances have low quality" — [Ghana datasheet on Dataverse](https://doi.org/10.7910/DVN/VEADSE)
- Zindi "Lacuna Malaria Detection Challenge" (16 Aug – 17 Nov 2024; Uganda-themed): 2,747 training and 1,178 test images, taken by smartphone through the eyepiece, up to 40 images per slide, with boxes in Train.csv — [Zindi](https://zindi.africa/competitions/lacuna-malaria-detection-challenge). A third-party listing gives the licence as CC BY-SA 4.0, which conflicts with CC BY 4.0 on Dataverse — [hyper.ai listing](https://hyper.ai/en/datasets/34868)

**Tanzania (NM-AIST)**
- 75 samples (40 malaria, 35 non-malaria) from five health facilities in Tanga region, collected May–August 2024, Giemsa-stained, imaged with a 100× oil objective. After cleaning there are 1,064 thin "infected" and 270 thin "uninfected" images (3840 × 2160 JPEG). Labels are per image only (one folder per class) and species is not specified — [Lufyagila et al. 2024, Data in Brief 57:111169](https://pmc.ncbi.nlm.nih.gov/articles/PMC11648091/)
- Dataverse: CC0 1.0, 2.98 GB, with Thin_Infected.zip (831 MB) and Thin_Uninfected.zip (340 MB) — [doi:10.7910/DVN/O2WVWA](https://doi.org/10.7910/DVN/O2WVWA)

**PlasmoCount (Davidson et al.)**: Giemsa smears of in-vitro P. falciparum cultures, with ~38,000 RBCs labelled and a test set labelled by five annotators from three centres — [danielbarco/malaria_datasets](https://github.com/danielbarco/malaria_datasets). The Mendeley record is CC BY 4.0, version 2, published 2021-03-09 — [Mendeley j55fyhtxn4](https://data.mendeley.com/datasets/j55fyhtxn4/2); preprint [doi:10.1101/2021.01.26.21250284](https://doi.org/10.1101/2021.01.26.21250284). According to one catalogue it covers strains 3D7, NF54, Dd2 and D10 in 108 images — [Isewon catalogue](https://github.com/ItunuIsewon/Malaria_Blood_Film_Images)

**PlasmoID**: 559 thin-smear images with 691 parasites, mostly from rural Indonesia, covering four species. Images are 960 × 1280, taken at 100× with an Optilab camera, with ground truth for detection and segmentation — [Nugroho et al., arXiv:2211.15105](https://arxiv.org/abs/2211.15105). No public download link was found.

**Chula RBC-12**: a red-cell morphology dataset with no malaria classes. It has 12 classes (normal, macrocyte, microcyte, spherocyte, target cell, stomatocyte, ovalocyte, teardrop, burr, schistocyte, hypochromia, elliptocyte, plus uncategorised). The README gives 706 images (738 after elliptocytes were added) with more than 20,000 cells, at 640 × 480, captured on a Nikon DS-Fi2-L3 at 1000×. Labels are cell-centre points, and there is no licence file — [Chula-RBC-12 GitHub](https://github.com/Chula-PIC-Lab/Chula-RBC-12-Dataset)

**Other thin-smear datasets listed by a 2013–2023 scoping-review catalogue** (I did not check whether they are available): Taiwan TIME (P. falciparum, 8,145 images); Kudisthalert et al. 2020 (Thailand, P. falciparum, 23,248); Wang et al. 2023 (China, six species, Wright-Giemsa); Fu et al. 2023 (China, four species); a French National Reference Center set (P. falciparum, 1,250); Delgado-Ortet et al. 2020 (Spain, P. falciparum, May-Grünwald-Giemsa, 517) — [Isewon catalogue, Summary_Table.md](https://github.com/ItunuIsewon/Malaria_Blood_Film_Images)

### Inferences
- Only four datasets offer same-species (P. falciparum) data from another site: MP-IDB Falciparum, PlasmoCount (culture, not patient blood), the Sudan release (no cell coordinates), and possibly Lacuna (species not stated). Of these, only MP-IDB has expert pixel masks per parasite and published NIH-to-MP-IDB baselines to compare against.
- Anything derived from the NLM Chittagong collection is a leakage trap: NIH-NLM-ThinBloodSmearsPf, MIRA boxes, Kaggle/TFDS mirrors and re-crops. This needs to be said explicitly, because these sets look like "new data with bounding boxes".
- BBBC041, IML-Malaria and M5 are P. vivax. Any drop on them combines species shift with site shift, so they can only be presented as stress tests.
- Licences: for a course project, every dataset above can be used for inference with attribution. BBBC041 is non-commercial (NC). For IML-Malaria and M5 no licence is stated, so they should be cited, and the team should avoid redistributing crops from them.

### Gaps
- I found no dataset called "MaRCos"/"MaRCoS" in any search, catalogue or paper. It may be a different name or not public.
- PlasmoID has no public download link that I could find, and its availability in 2025–2026 is unknown.
- Neither the Lacuna article nor the datasheet excerpts I read state the Plasmodium species (Uganda or Ghana).
- I could not confirm BBBC041 per-class box counts or image resolutions from primary text. M5 appears to box only malarial cells, since its table counts "malarial cells" only, but I did not confirm whether healthy RBCs are boxed.
- I could not confirm the journal version of IML-Malaria from a primary page; I cite the arXiv version.
- I did not check the availability of TIME, Kudisthalert, Wang 2023 or the French NRC set.
- MP-IDB's image count differs between sources (210 in the repo, 229 in papers), and I did not resolve why.

## 2. Which datasets allow single-RBC crops comparable to the NIH crops, what preprocessing is needed, and how do those choices confound the test?

### Takeaway
BBBC041 and IML-Malaria box every RBC, so crops can be cut directly, but each crop includes plasma background and neighbouring cells and must be masked to black to look like NIH crops. MP-IDB and the Lacuna thin sets label only parasites, so the "uninfected" class has to be made with the team's own RBC segmentation, and that segmentation becomes part of what is being tested. The Sudan and Tanzania sets have no cell coordinates at all. Preprocessing choices move the results by more than 10 percentage points. In the capstone, Otsu background masking raised MP-IDB P. falciparum sensitivity by 11–15 pp for two of three CNNs, but lowered AUC on BBBC041 for all three.

### Cited Findings
- **NIH crops**: RBCs were cut out with a level-set segmentation — [Rajaraman et al. 2018](https://doi.org/10.7717/peerj.4568). Measured over all 27,558 crops, the median width is 130 px, the median upscale factor to 224 px is 1.81, and 26 % of pixels are black background. BBBC041 and MP-IDB crops have 0 % black — [capstone, outputs/tables/domain_summary.csv](https://github.com/noahtjonsk/malaria-cross-dataset)
- **Appearance differs strongly** (same capstone table):

  | Domain | Brightness | Contrast | Saturation | Red–blue stain index | Sharpness |
  |---|---|---|---|---|---|
  | NIH | 164.7 | 4.67 | 64.8 | +42.5 | 5.78 |
  | BBBC041 site_a | 92.5 | 22.8 | 56.7 | −24.0 | 24.3 |
  | BBBC041 site_b | 121.9 | 3.28 | 17.1 | −1.6 | 2.49 |
  | MP-IDB Falciparum | 123.7 | 14.3 | 76.9 | +42.7 | 7.72 |
  | MP-IDB Vivax | — | — | — | −18.1 | — |

  A classifier told to separate NIH cells from each external domain reached AUC 1.0, and ≥ 0.999 using appearance features alone — [capstone, domain_summary.csv and domain_classifier_auc.csv](https://github.com/noahtjonsk/malaria-cross-dataset)
- **MP-IDB scale and framing**: the parasite crops bundled with MP-IDB are tight around the parasite (median width 78 px, upscale factor 2.87). When the capstone re-framed parasites on their host cell, the host-cell side was about 114–128 px and the crop side about 137–168 px in the sample rows — [capstone, domain_summary.csv and mpidb_wholecell_framing.csv](https://github.com/noahtjonsk/malaria-cross-dataset)
- **Making negatives for MP-IDB (MalariaNet protocol)**: positive crops came from the expert parasite ground truth on 104 fields imaged at 100×. Uninfected crops came from automated RBC segmentation, excluding cells that overlapped a parasite or leukocyte. This gave 1,185 parasitised and 2,000 uninfected crops. The authors state that segmentation effects and laboratory effects "cannot be fully separated" — [Hou et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/)
- **BBBC041 crops**: MalariaNet used 2,452 parasitised cells and 3,000 sampled uninfected cells — [Hou et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/). The capstone scored 79,569 cells from 1,208 images ("site_a") and 5,917 cells from 120 images ("site_b"). Median cell widths were 135 and 172 px, against 130 px for NIH — [capstone](https://github.com/noahtjonsk/malaria-cross-dataset)
- **Masking, CNNs trained on NIH patient split, single seed**:

  | Model | MP-IDB Pf sensitivity, raw → Otsu-masked | BBBC041 site_a specificity, raw → masked | BBBC041 AUC, raw → masked (site_a; site_b) |
  |---|---|---|---|
  | VGG-16 | 57.4 % → 71.9 % | 65.5 % → 53.6 % | 0.972 → 0.966; 0.975 → 0.958 |
  | ResNet-50 | 52.6 % → 63.9 % | 87.3 % → 66.6 % | 0.920 → 0.902; 0.964 → 0.961 |
  | MobileNetV2 | 28.6 % → 27.2 % | 90.0 % → 78.9 % | 0.945 → 0.896; 0.930 → 0.872 |

  Source: [capstone, outputs/tables/rq2_*_s0.csv](https://github.com/noahtjonsk/malaria-cross-dataset). The capstone also reports that in its colour-matched crops, very dark BBBC041 site_a pixels fall below its black level, are treated as padding and leave "black holes" — [capstone README](https://github.com/noahtjonsk/malaria-cross-dataset)
- **Stage content**: Loddo et al. state that "NIH contains only ring-stage parasites", and that trophozoites, schizonts and gametocytes "greatly vary between the two types, while the ring stages are pretty similar". In context, the "two types" appear to be P. falciparum and P. vivax; this is my reading, not a quote — [Loddo et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/). The NLM annotations list "Gametocyte" as a separate label from infected/uninfected RBCs — [NLM datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html)
- **Labels are noisy**: on the BBBC041 test images, two expert annotators agreed with F1 of 82 % (trophozoite), 44 % (schizont), 67 % (ring), 63 % (gametocyte) and 92 % (leukocyte) — [Hung et al. 2018](https://arxiv.org/abs/1804.09548). In the NIH thin-smear images, visible cells at image borders were often left unannotated — [Wilm et al. 2025](https://arxiv.org/abs/2507.18483)
- **Magnification and capture**: NIH, Sudan and Uganda images were all taken by smartphone through a microscope eyepiece — [Rajaraman et al. 2018](https://doi.org/10.7717/peerj.4568); [Sudan Readme.pdf](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/Readme.pdf); [Nakasi et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11719325/). M5 shows that detectors fail across magnifications: Faster R-CNN trained at 1000× on the high-cost microscope scored 66.8 mAP at 1000×, 31.3 at 400× and 0.0 at 100× — [Sultani et al. 2022](https://arxiv.org/abs/2111.13656)
- **Count-only datasets**: the Sudan thin images carry only counts per image. Some positive patients have zero infected RBCs on the thin smear — [Sudan Readme.pdf](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/Readme.pdf). Tanzania images are labelled per image only — [Lufyagila et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11648091/)

### Inferences
- **A crop recipe that keeps the comparison fair** (my synthesis, not taken from any one paper):
  1. Estimate the median RBC diameter in pixels for each dataset and rescale whole images so it matches NIH. NIH crops are about 130 px wide; MP-IDB host cells are about 115–125 px, so close; BBBC041 site_b cells are about 172 px.
  2. Take a square window centred on the host cell at about 1.1–1.2× the cell diameter.
  3. Segment that cell (Otsu or watershed, or Cellpose or NLM's [RBCNet](https://github.com/LHNCBC/RBCNet)) and set pixels outside the mask to 0, so the background is black as in the NIH crops.
  4. Feed the crop through exactly the same nearest-neighbour resize to 224 and the same model-specific preprocessing as in training. For the YUV arm, apply YUV histogram equalisation exactly as in training.
- **Report two versions as a sensitivity analysis**: raw box crops and masked crops. The masking method alone changes results by 10–20 pp in either direction, and it can clip parasites lying on the cell edge (trophozoites, schizonts, gametocytes). Missed parasites then become artificial false negatives.
- **Proposed label mapping**:
  - BBBC041 and IML: ring, trophozoite, schizont and gametocyte map to "parasitised"; RBC maps to "uninfected"; leukocyte and difficult are excluded.
  - MP-IDB: parasite-mask components map to "parasitised". Segmented RBCs that do not overlap any mask map to "uninfected".
  - Lacuna: "Parasitized cell", ring, trophozoite and gametocyte map to "parasitised"; WBC and artefacts are excluded; uninfected cells must be segmented.
  - Primary analysis: ring-stage positives only, because NIH positives are reportedly rings. Other stages go in a separate stratum.
- **Dataset-specific confounds**: the effect of masking depends on the dataset (it helps on MP-IDB and hurts on BBBC041). So no single preprocessing choice is "correct", and preprocessing has to be fixed in advance rather than chosen on the external results.
- **Where the shift lies**: MP-IDB P. falciparum colour statistics are almost identical to NIH (red–blue stain index +42.7 vs +42.5). On MP-IDB the shift is therefore mostly geometry, background, sharpness and contrast, not stain colour. BBBC041 has the large colour shift (−24.0).

### Gaps
- No paper reports how much of a NIH-to-external drop is due to the segmentation used to make negatives versus the site itself. MalariaNet explicitly says the two cannot be separated.
- I found no published RBC-diameter-in-pixels figures per dataset. The 115–172 px values come only from the capstone's crop statistics.

## 3. What drop do published NIH-to-external (or reverse) experiments report?

### Takeaway
Every NIH-to-external experiment I found reports a large zero-shot drop:
- **MP-IDB P. falciparum (same species)**: the best-controlled number is from MalariaNet (2026). Slide-disjoint NIH accuracy of 95.6 % fell to 79.5 ± 2.9 % (sensitivity 74.0 %, specificity 82.7 %, AUC 0.865).
- **BBBC041 (cross-species)**: accuracy fell to 53–64 %, with specificity collapsing to 18–37 % at the NIH threshold.
- **Loddo et al. 2022**: NIH-trained CNNs scored 32–69 % on MP-IDB falciparum crops, and only fine-tuning on MP-IDB brought them back (92.6 % average).
- **Capstone (patient-split NIH training)**: sensitivity on MP-IDB P. falciparum parasites was 29–57 %, against 97–98 % on held-out NIH patients. BBBC041 AUC stayed at 0.92–0.97.

The team should expect a double-digit drop in accuracy and MCC. Much of it comes from the decision threshold no longer fitting the new data, rather than from the model losing all ability to rank cells.

### Cited Findings
- **Loddo, Fadda, Di Ruberto 2022 (J Imaging 8(3):66, doi:10.3390/jimaging8030066)**:
  - Binary accuracy on NIH was 97.68 % for ResNet-18 and 97.25 % averaged over 11 CNNs.
  - Exp1 trained on NIH and tested on MP-IDB-FC (MP-IDB falciparum crops). Per-network accuracy: AlexNet 42.71, DenseNet-201 49.73, ResNet-18 68.23, ResNet-50 68.23, ResNet-101 69.10, GoogLeNet 68.23, ShuffleNet 32.23, SqueezeNet 68.23, MobileNetV2 57.12, Inception-v3 41.84, VGG-16 53.59. The table's stated average is 60.61 %.
  - Exp2 trained on NIH and fine-tuned on MP-IDB, and averaged 92.59 % (DenseNet-201 97.45 ± 1.40).
  - The authors wrote: "when the target domain differs excessively from the source domain, it is hard to directly apply the models trained with NIH to MP-IDB-FC."
  - Caveats: the MP-IDB-FC test labels are four life stages, and the paper does not explain how the binary NIH output was mapped onto them. Four networks give exactly 68.23 %, with no explanation.
  
  Source: [PMC8951236](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/)
- **Hou et al. 2026, MalariaNet (Biosensors 16(7):358, doi:10.3390/bios16070358)**:
  - NIH accuracy was 97.06 ± 0.45 % with a per-cell split and 95.61 ± 1.02 % with a slide-disjoint split. Across eight architectures the leakage gap was −0.25 to −1.45 pp, and for EfficientNet-B0 −0.47 to −0.56 pp under controlled retraining.
  - Zero-shot NIH → MP-IDB P. falciparum (slide-disjoint, 3 seeds): accuracy 79.5 ± 2.9 %, sensitivity 74.0 ± 8.3 %, specificity 82.7 ± 5.8 %, AUC 0.865 ± 0.029.
  - NIH → BBBC041 (P. vivax), slide-disjoint: accuracy 53.2 ± 5.2 %, sensitivity 96.4 ± 4.2 %, specificity 18.0 ± 12.8 %, AUC 0.768 ± 0.050.
  - NIH → BBBC041 with the per-cell-trained model: accuracy 63.79 %, sensitivity 96.33 %, specificity 37.20 %, AUC 0.830.
  - A variant without one module reached 74.03 % accuracy on BBBC041.
  - Training used flips, rotation, colour jitter and random affine augmentation.
  - Stated limitation: "only one additional laboratory (MP-IDB) for same-species testing, using well-formed cell crops rather than field captures"; the authors also note that cross-site results from per-cell-trained models do not reliably predict slide-disjoint behaviour.
  
  Source: [PMC13406217](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/)
- **Capstone (unpublished; NIH split 70/15/15 by patient; ImageNet CNNs fine-tuned; threshold fixed at 0.5; 95 % CIs by resampling patients/images; seed 0 only)**:

  | Test set (cells) | VGG-16 sens / spec / AUC | ResNet-50 sens / spec / AUC | MobileNetV2 sens / spec / AUC |
  |---|---|---|---|
  | NIH hold-out (4,177) | 98.2 / 96.6 / 0.997 | 97.2 / 98.4 / 0.996 | 97.1 / 98.2 / 0.996 |
  | BBBC041 site_a (79,569) | 99.3 / 65.5 / 0.972 | 79.3 / 87.3 / 0.920 | 83.7 / 90.0 / 0.945 |
  | BBBC041 site_b (5,917) | 89.8 / 95.0 / 0.975 | 68.0 / 98.1 / 0.964 | 30.4 / 99.1 / 0.930 |
  | MP-IDB Pf, parasites only (1,297) | sens 57.4 (drop 40.9 pp, CI 34.7–47.1) | sens 52.6 (drop 44.6 pp) | sens 28.6 (drop 68.5 pp) |
  | MP-IDB other species (140) | sens 80.0 | sens 56.4 | sens 38.6 |

  Sources: [capstone, outputs/tables/rq1_*_s0.csv and rq1_compare_s0.csv](https://github.com/noahtjonsk/malaria-cross-dataset). The architectures differed significantly in their drops; for example, on BBBC041 site_a, VGG-16 lost 20.0 pp more specificity than ResNet-50 (adjusted CI 16.8–23.1) — [capstone, rq1_compare_s0.csv](https://github.com/noahtjonsk/malaria-cross-dataset)
- **Yu et al. 2023 (Malar J 22:33)**: a field test in Sudan (190 patients) of NLM's Malaria Screener, trained on data from Bangladesh and Thailand.
  - With threshold calibration, patient-level accuracy was 74.1 % against expert microscopy and 71.8 % against nested PCR.
  - In post-study experiments, the newer PlasmodiumVF-Net reached 83.1 % and 81.0 % without using any data from the test sites.
  
  Source: [PubMed 36707822](https://pubmed.ncbi.nlm.nih.gov/36707822/). The authors write that "unlike the training data, the field data contains more parasite-like staining artifacts, which are difficult for the model to distinguish", and that PVF-Net "was trained and calibrated using a dataset from Bangladesh" — [PMC9883923](https://pmc.ncbi.nlm.nih.gov/articles/PMC9883923/)
- **Sultani et al. 2022 (M5, detection, not NIH)**: moving from the high-cost to the low-cost microscope at the same 1000× magnification, Faster R-CNN fell from 66.8 mAP (in-domain) to 17.1 mAP ("source only"). Low-cost-microscope images showed "change in color distribution" and were "more blurred and less clear" — [arXiv:2111.13656](https://arxiv.org/abs/2111.13656)
- **Wilm et al. 2025 (within NIH, across annotation subsets)**: Faster R-CNN recall for infected cells was 0.77 when trained on the NIH polygon subset and tested on MIRA boxes, and 0.91 the other way. Annotation protocol therefore shifts results even within a single hospital — [arXiv:2507.18483](https://arxiv.org/abs/2507.18483)
- **Alawfi 2025 (Front Cell Infect Microbiol, doi:10.3389/fcimb.2025.1615993; not NIH)**: across MP-IDB, MP-IDB2, IML-Malaria and "MD-2019", accuracy over the 12 train→test pairs was 0.75–0.88, against 0.89–1.00 in-dataset. These are single runs, and the paper has internal inconsistencies — [Frontiers](https://www.frontiersin.org/journals/cellular-and-infection-microbiology/articles/10.3389/fcimb.2025.1615993/full)

### Inferences
- **Expected range for the team's EfficientNet-B0 ensemble** (98.45 % accuracy in-domain):
  - On a balanced, MalariaNet-style MP-IDB P. falciparum crop set, roughly 75–85 % accuracy and AUC around 0.85–0.90, a drop of about 13–23 pp.
  - Sensitivity on MP-IDB parasite crops could be anywhere from about 30 % to 75 %, depending on architecture and framing.
  - On BBBC041, accuracy at the NIH threshold could fall to 50–65 % even if AUC stays above 0.8.
  
  These are extrapolations from other architectures, not measurements.
- **Metrics to report**: because zero-shot shift mostly breaks the decision threshold (huge swings in sensitivity or specificity while AUC holds up), report AUC (threshold-free), sensitivity and specificity at the frozen NIH threshold, and MCC. Optionally, add re-thresholded numbers on a separate external calibration split, clearly labelled as adaptation.
- **Variance between models**: architectures differ widely in how much they drop (MobileNetV2 lost 68.5 pp of MP-IDB sensitivity, VGG-16 40.9 pp). Reporting the spread across the 10 fold-models in each arm is therefore informative, alongside the ensemble.

### Gaps
- No published NIH-to-external result exists for an EfficientNet-B0 classifier or a k-fold ensemble. MalariaNet includes EfficientNet-B0 only in its leakage analysis.
- I found no study that trains on an external dataset and tests on NIH.
- From the abstract and the text I extracted, I could not separate how much of the Sudan patient-level result comes from thin-smear versus thick-smear analysis.
- The per-network Exp1 values I extracted from Loddo et al. average 56.3 %, not the 60.61 % the table states. Either my extraction or the paper's table is wrong, so check the PDF before quoting the average.

## 4. Did stain normalisation, colour augmentation or domain adaptation recover the drop?

### Takeaway
No malaria study I found shows classical stain normalisation recovering an NIH-to-external drop.
- **Only direct test (unpublished capstone)**: test-time Reinhard colour transfer to NIH lowered BBBC041 AUC for all three CNNs. Histogram matching made the models call almost every cell parasitised, which looked like "recovery" on MP-IDB's positives-only set.
- **Learned image translation**: helps partly (M5: 17.1 → 33.3–37.5 mAP, against 66.8 in-domain).
- **Fine-tuning on target data**: recovers most of the drop (Loddo: 60.6 → 92.6 %).
- **Strongest multi-centre evidence** (histopathology, 9 centres, 760 CNNs): colour augmentation during training matters most, the top configuration used no normalisation at all, and classical normalisation never beat grayscale.

Prediction for the team: the YUV arm is unlikely to close the external gap. Even so, an external test is the first setting where the hypothesis could show any effect, so it is worth pre-registering and running.

### Cited Findings
- **Capstone, colour transfer after masking** (test-time only, single seed):
  - Reinhard transfer to NIH statistics reduced BBBC041 site_a AUC from 0.966 (masked) to 0.856 for VGG-16, from 0.902 to 0.745 for ResNet-50, and from 0.896 to 0.841 for MobileNetV2. Relative to raw crops, the reductions were 0.972 → 0.856, 0.920 → 0.745 and 0.945 → 0.841.
  - On MP-IDB P. falciparum, Reinhard sensitivity was 66.4 / 52.3 / 32.9 %, against 71.9 / 63.9 / 27.2 % for masked crops alone.
  - Histogram matching gave MP-IDB P. falciparum sensitivity of 99.5 / 98.1 / 95.4 %, but BBBC041 specificity fell to 5.9 / 6.6 / 44.4 % (site_a) and 1.1 / 15.0 / 41.9 % (site_b), and site_b AUC to 0.730 / 0.725 / 0.694.
  
  Source: [capstone, outputs/tables/rq2_*_s0.csv](https://github.com/noahtjonsk/malaria-cross-dataset). The README notes that Reinhard transfer "amplifies the noise on flat, grey site_b cells, because it stretches their small colour spread to NIH's" — [capstone README](https://github.com/noahtjonsk/malaria-cross-dataset)
- **MalariaNet** trained with colour-jitter augmentation and still dropped to 79.5 % (MP-IDB) and 53.2 % (BBBC041). Its fixed "Giemsa projection" is a built-in design choice, not a normalisation step, and stain normalisation was not tested as an intervention — [Hou et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/)
- **Loddo et al.** applied a per-channel colour-balancing equation (C_out = C_in · m_im / m_c) to all images, used rotation, translation and reflection augmentation, and still saw the Exp1 collapse. Fine-tuning on MP-IDB (Exp2) was what recovered performance — [Loddo et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/)
- **M5 domain adaptation** (high-cost → low-cost microscope, 1000×, mAP):
  - Source-only: 17.1.
  - Feature-alignment domain-adaptation methods from the literature: 15.5 to 24.8.
  - Fine-tuning on CycleGAN "fake-LCM" images: 33.3.
  - Ranking + triplet loss: 37.5.
  - In-domain reference: 66.8.
  
  Source: [Sultani et al. 2022](https://arxiv.org/abs/2111.13656)
- **Yu et al. 2023** needed threshold calibration in Sudan, giving 74.1 % patient-level accuracy against microscopy, and blamed parasite-like staining artefacts — [PubMed 36707822](https://pubmed.ncbi.nlm.nih.gov/36707822/); [PMC9883923](https://pmc.ncbi.nlm.nih.gov/articles/PMC9883923/)
- **Tellez et al. 2019** (Med Image Anal 58:101544; H&E histopathology; 4 tasks; 9 laboratories in total; every model trained only on Radboudumc data and tested on 9 external test sets; 760 CNNs):
  - Stain colour augmentation (HSV or HED) "was crucial to obtain top classification performance, regardless of the stain color normalization technique used".
  - "Overall top performance was achieved without the use of color normalization"; the best-ranked configuration was no normalisation with light HED augmentation (mean rank 1.2).
  - "None of the classical approaches, LUT or Deconvolution, surpassed the performance of Grayscale".
  - "All stain color normalization techniques obtained a poor performance when no color augmentation was used".
  - Example: with no normalisation, external AUC on one lymph-node centre was 0.406 with basic augmentation and 0.968 with HED-light.
  
  Source: [arXiv:1902.06543](https://arxiv.org/abs/1902.06543)
- **Jahanifar et al. 2023** (ACM Computing Surveys) benchmarked 28 domain-generalisation algorithms in computational pathology and found that "careful experiment design and Stain Augmentation technique can be very effective", but that "there is no one-size-fits-all solution" — [Consensus record](https://consensus.app/papers/details/9c73b57beb1f5dfb8edc2ccfa568b40c/)
- **Otálora et al. 2019**: across Gleason grading and mitosis datasets, "color augmentation and DANN training obtain most often the best results" — [Consensus record](https://consensus.app/papers/details/2678acc6a3e0503e8e9fba02e5cc3963/)
- **Xu et al. 2025 (BeerLaNet)**: a trainable, physics-based colour normalisation evaluated on an in-house collection of malaria blood smears for cross-domain detection and classification, reported to beat "many state-of-the-art stain normalization methods". The abstract gives no numbers — [Consensus record](https://consensus.app/papers/details/12855c5ef4e35a41bbe6cb05578e4d32/)

### Inferences
- **What the evidence supports**: the malaria and pathology results agree that matching the test images' colours to the training set does not reliably recover cross-site drops, and can make them worse. Colour augmentation during training, learned translation, or fine-tuning on target data do better. The team's YUV-HE arm is a fixed per-image normalisation applied in both training and testing, closer to "normalisation" than to "augmentation". The histopathology prior is therefore that it adds little unless combined with colour augmentation.
- **What YUV-HE can and cannot fix**: if the YUV step equalises only the luma (Y) channel, it standardises brightness and contrast but leaves the chroma (U/V) that carries stain hue unchanged. This is an assumption about the team's code and should be checked.
  - The measured shifts include large brightness and contrast differences (NIH brightness 164.7 vs BBBC041 site_a 92.5; contrast 4.67 vs 22.8), which YUV-HE could plausibly reduce.
  - They also include a hue shift (red–blue index +42.5 vs −24.0), which it would not touch.
  - Testable prediction: the YUV arm gains relative to the raw arm on BBBC041 (large brightness, contrast and colour shift) more than on MP-IDB P. falciparum (colour almost identical to NIH).
- **Choosing the test set for the hypothesis**: MP-IDB P. falciparum is a weak test of a stain-normalisation hypothesis, because its colour already matches NIH. BBBC041 is a strong colour-shift test but is confounded by species. Running both, with predictions written down beforehand, separates "normalisation helps under colour shift" from "normalisation helps under any site shift".
- **Why run it even though YUV lost in-domain**: the −0.26 pp MCC in-domain result does not settle the question either way. A null or negative external result would still be informative, and would agree with Tellez's finding that normalisation alone is not enough.

### Gaps
- No peer-reviewed malaria paper compares stain normalisation (Reinhard, Macenko, histogram equalisation, YUV) against colour augmentation for NIH-to-external transfer. The only direct evidence is the unpublished, single-seed capstone.
- No study tests YUV or luminance histogram equalisation specifically for malaria cross-site transfer.
- I did not obtain numbers for BeerLaNet's malaria experiments.

## 5. How much work is one external test with the existing 30 models, and which pitfalls must be reported?

### Takeaway
With 30 trained Keras models, inference takes minutes; nearly all the work is building fair crops and honest statistics. Rough effort estimates (inferences):

| Dataset | Effort | Why |
|---|---|---|
| IML-Malaria | ~1 day | 46 MB; every cell boxed; but P. vivax and only 529 positives |
| BBBC041 | 2–3 days | 2.26 GB; every cell boxed; needs masking |
| MP-IDB P. falciparum | 3–5 days | ~3 GB; parasite masks only, so negatives must be segmented |
| Lacuna Uganda thin | 4–6 days | 0.73 GB; no uninfected labels; species unconfirmed |
| Sudan | several weeks | 49 GB; no cell coordinates; patient- or count-level evaluation only |

### Cited Findings
- **Download sizes**:
  - BBBC041: 2.26 GB — [BBBC041](https://bbbc.broadinstitute.org/BBBC041)
  - MP-IDB: repository ~3.1 GB per the GitHub API — [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis)
  - IML-Malaria: ~46 MB — [IML GitHub](https://github.com/QaziAmmar/A-Dataset-and-Benchmark-for-Malaria-Life-Cycle-Classification-in-Thin-Blood-Smear-Images)
  - M5: 23 GB — [M5 GitHub](https://github.com/intelligentMachines-ITU/LowCostMalariaDetection_CVPR_2022)
  - Lacuna: Uganda thin 0.73 GB, Ghana thin 1.51 GB — [Dataverse](https://doi.org/10.7910/DVN/VEADSE)
  - Tanzania: 2.98 GB — [Dataverse](https://doi.org/10.7910/DVN/O2WVWA)
  - Sudan: 49.2 GB — [NLM index.json](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/index.json)
- **Annotation formats**:
  - BBBC041: per-cell class plus box — [BBBC041](https://bbbc.broadinstitute.org/BBBC041)
  - IML-Malaria: one JSON file of {image_name, objects:[{type, bbox{x,y,h,w}}]}, with a plotting script — [IML GitHub](https://github.com/QaziAmmar/A-Dataset-and-Benchmark-for-Malaria-Life-Cycle-Classification-in-Thin-Blood-Smear-Images)
  - MP-IDB: binary masks and stage letters in filenames — [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis)
  - Lacuna Uganda: YOLO text files — [Dataverse datasheet](https://doi.org/10.7910/DVN/VEADSE)
  - M5: Pascal VOC — [M5 GitHub](https://github.com/intelligentMachines-ITU/LowCostMalariaDetection_CVPR_2022)
- **Measured time from the capstone pipeline**:
  - Building manifests and about 86,000 cached crops (BBBC041 plus MP-IDB): about 15 min and 2.9 GB.
  - Per-image statistics for 115,000 cells: about 5 min.
  - Validating background-removal methods: about 40 min.
  - Otsu-masked crops: about 15 min; colour-transferred crops: about 20 min.
  - Training ran on a Colab T4.
  
  Source: [capstone README](https://github.com/noahtjonsk/malaria-cross-dataset). The capstone code is PyTorch and the GitHub API reports no licence for it, so it is a reference design rather than a drop-in for TF/Keras.
- **Statistical unit**: MP-IDB Falciparum's 104 images come from 10 distinct smear prefixes — [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis) — and a prefix identifies the same patient — [danielbarco/malaria_datasets](https://github.com/danielbarco/malaria_datasets).
- **Uncertainty**: MalariaNet found that per-cell Wilson intervals were anti-conservative compared with slide-level cluster bootstraps (±0.6 pp vs ±1.2–3.3 pp) — [Hou et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/)
- **Class balance**: BBBC041 is >95 % uninfected cells — [BBBC041](https://bbbc.broadinstitute.org/BBBC041). IML-Malaria has 529 infected cells among 38,449 boxes (computed from annotations.json) — [IML GitHub](https://github.com/QaziAmmar/A-Dataset-and-Benchmark-for-Malaria-Life-Cycle-Classification-in-Thin-Blood-Smear-Images). MP-IDB P. falciparum positives are 95 % rings (1,230 of 1,297) — [Loddo et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/)
- **A positives-only test set hides degenerate models**: histogram matching produced 95–99.5 % "sensitivity" on MP-IDB parasites, while the same models' specificity on BBBC041 fell to 1–44 % — [capstone, rq2_*_s0.csv](https://github.com/noahtjonsk/malaria-cross-dataset)

### Inferences
- **Steps and estimated effort for MP-IDB P. falciparum** (estimates):
  1. Download and parse the masks into connected components, giving one box per parasite: about 0.5 day.
  2. Segment RBCs to obtain host cells and negatives (Otsu plus watershed, or Cellpose or RBCNet), excluding cells that touch any parasite mask, WBCs or debris; check segmentation quality visually on about 50 cells: 1–2 days.
  3. Rescale to the NIH RBC diameter, mask the background to black, apply the identical resize and preprocessing for each arm, and save PNGs: 0.5–1 day.
  4. Run inference with 30 models on about 3,000 crops: minutes. EfficientNet-B0 at 224 px costs well under 1 GFLOP per image, so this is fine even on a laptop CPU.
  5. Compute metrics with a patient-cluster bootstrap (10 clusters) and also an image-level bootstrap: 0.5 day.
  6. Write-up: 0.5–1 day.
- **Pitfalls to report explicitly**:
  - Species and stage mismatch (P. vivax sets; MP-IDB's non-ring stages).
  - Magnification and scale mismatch, and how it was handled.
  - The masking method, and that results change with it.
  - Negatives generated by the team's own segmenter, not by experts.
  - Prevalence differences (report sensitivity and specificity, not only accuracy).
  - The threshold is frozen from NIH; nothing is tuned on the external set.
  - Positives-only sets.
  - Patient-level clustering: MP-IDB has only 10 smears, so CIs will be wide.
  - Label noise (inter-expert F1 44–92 % for stages; unannotated border cells).
  - Leakage avoided by excluding all NLM-Chittagong-derived sets.
  - Licence and attribution (BBBC041 is NC; IML-Malaria and M5 have no licence).
  - Same preprocessing for both arms. Pay particular attention to channel order (OpenCV reads BGR), value range, and applying YUV-HE only in the YUV arm, exactly as in training.
- **Minimum honest claim**: an external result from 10 Swiss patients is a robustness probe, not a clinical validation. The limitations slide should change from "no external test set" to something like "one small same-species external test (MP-IDB, 10 patients) showing X; a multi-site field test remains future work".

### Gaps
- I could not measure the actual GitHub archive size for MP-IDB: the codeload ZIP streams without a content length. Downloading it directly, or using a shallow clone with git-lfs if needed, may differ from the 3.1 GB repository-size figure.
- There is no published timing for TF/Keras pipelines of this kind; the person-day figures are my estimates.

## 6. Which single dataset should the team use, and why?

### Takeaway
Use the MP-IDB Falciparum subset as the single external test set. It is the only freely licensed, cell-precise dataset with the same species, stain and smear type from a different country and laboratory. It is small enough to process in under a week, and it already has published NIH-to-MP-IDB baselines to compare against: MalariaNet's 79.5 % accuracy and 0.865 AUC, Loddo's 32–69 %, and the capstone's 29–57 % parasite sensitivity. If time allows, add BBBC041 as a clearly labelled "cross-species, large-colour-shift stress test", because that is where a normalisation effect is most likely to show.

### Cited Findings
- MP-IDB Falciparum is P. falciparum on Giemsa-stained thin smears from Switzerland. It has expert ground truth per image, an MIT licence and about 3 GB of data — [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis); [Isewon catalogue](https://github.com/ItunuIsewon/Malaria_Blood_Film_Images)
- Its positives are mostly ring stage (1,230 of 1,297 crops), matching the NIH positives, which Loddo et al. describe as "only ring-stage" — [Loddo et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/)
- A peer-reviewed zero-shot NIH-to-MP-IDB benchmark with a documented protocol for making negatives already exists (1,185 parasitised and 2,000 uninfected crops; accuracy 79.5 ± 2.9 %, AUC 0.865 ± 0.029) — [Hou et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13406217/). So do an earlier benchmark — [Loddo et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/) — and an open pipeline (the capstone) — [capstone](https://github.com/noahtjonsk/malaria-cross-dataset)
- The alternatives each have a blocking problem:
  - The NLM thin-smear images share patients and photos with the training crops — [NLM datasheet](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html); [capstone overlap table](https://github.com/noahtjonsk/malaria-cross-dataset)
  - The Sudan set has only image-level counts and is 49 GB — [Sudan Readme.pdf](https://data.lhncbc.nlm.nih.gov/public/Malaria/MalariaScreener/Readme.pdf)
  - BBBC041, IML-Malaria and M5 are P. vivax — [BBBC041](https://bbbc.broadinstitute.org/BBBC041); [arXiv:2102.08708](https://arxiv.org/abs/2102.08708); [arXiv:2111.13656](https://arxiv.org/abs/2111.13656)
  - The Lacuna thin sets have no uninfected class, and their species is not stated in the excerpts I read — [Nakasi et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11719325/)
- MP-IDB's weaknesses:
  - Only 10 smears/patients in the Falciparum subset — [MP-IDB GitHub](https://github.com/andrealoddo/MP-IDB-The-Malaria-Parasite-Image-Database-for-Image-Processing-and-Analysis); [danielbarco/malaria_datasets](https://github.com/danielbarco/malaria_datasets)
  - No expert negatives — [Loddo et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8951236/)
  - Colour close to NIH (red–blue index +42.7 vs +42.5) — [capstone domain_summary.csv](https://github.com/noahtjonsk/malaria-cross-dataset)

### Inferences
- **A fair, defensible protocol on MP-IDB P. falciparum**:
  1. Use parasite masks for positives (ring stratum primary; others reported separately).
  2. Use segmented, mask-free RBCs for negatives, excluding WBCs and debris, in a fixed ratio such as MalariaNet's roughly 1:1.7, or with all cells and prevalence reported.
  3. Frame whole cells, rescale to the NIH RBC diameter, use a black background, and the identical resize and preprocessing as in training.
  4. Freeze the NIH threshold.
  5. Report both arms (raw and YUV) for the ensemble and for all 10 fold-models.
  6. Report AUC, sensitivity, specificity and MCC with patient-cluster (n = 10) and image-cluster bootstrap CIs.
  7. Repeat with unmasked crops as a sensitivity analysis.
  8. Write down the predictions beforehand. For example: "accuracy drops by more than 10 pp; the YUV arm's AUC is within ±0.02 of the raw arm's on MP-IDB".
- **Second dataset if time allows**: BBBC041. It costs about two more days and tests the case where colour shift is large, which is where the team's stain-normalisation idea would have to prove itself. Label it explicitly as confounded by species.
- **Future-work line for the deck**: the NLM Sudan set (P. falciparum, a different country, the same smartphone-on-microscope protocol, 190 patients) is the natural next external test at patient level. It needs RBC segmentation and evaluation against counts, so it is out of scope for this project.

### Gaps
- No published study has run NIH-trained models on MP-IDB with the exact framing proposed here (whole cell, black background, NIH-matched scale), so the expected numbers for this protocol are extrapolated rather than measured.
- Whether the Lacuna Ghana or Uganda thin sets are P. falciparum, and how good their annotations are, remains unverified. If confirmed, they could become a larger same-species field alternative to MP-IDB.
