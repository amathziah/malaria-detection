# Slides

| File | What it is |
|---|---|
| [`Malaria_Phase3_Final.pptx`](Malaria_Phase3_Final.pptx) · [PDF](Malaria_Phase3_Final.pdf) | **Final deck, 17 slides plus references**, in five parts that follow the brief's six steps; a tracker at the top right of every slide shows the part. Opening: title, what we achieved, roadmap. Part 1, the problem: microscopy and the NIH data, 11 studies, our question (image vs patient split). Part 2, reproduction: base-paper checklist, the model, reproduced within 1 pp and 25× faster. Part 3, our change: two predictions fixed before training and the 2 × 2 design. Part 4, results: every metric for all four experiments, 98 % holds on unseen patients (H1), the model is already stain-robust (H2), what our predictions taught us. Part 5: failure analysis, cells to patients (screening view, no clinical claim), contributions, scope and next steps. Every number is generated from `results/` ([`src/`](src)); the failure-analysis figure comes from [`../src/deck_figures.py`](../src/deck_figures.py) |
| [`Malaria_Phase2_Long.pptx`](Malaria_Phase2_Long.pptx) · [PDF](Malaria_Phase2_Long.pdf) | Full presentation, 31 slides: Phase 1 literature review, the base paper, what its own code revealed, how to read the metrics, the paper-exact 10-fold reproduction and its results (graphs for every result), the GPU engineering, hypotheses H1/H2 with the ablation plan, references |
| [`Malaria_Phase2_Short.pptx`](Malaria_Phase2_Short.pptx) · [PDF](Malaria_Phase2_Short.pdf) | Short version, 13 slides: everything done after Phase 1, with the results graphs |
| [`figures/`](figures) | The decks' graphs as PNG files (results vs. paper, per-fold accuracy, training curves, ROC, metrics primer, timing, speed-ups, cell samples, augmentation) |
| [`archive/`](archive) | Earlier decks: the original Phase 2 deck and the 24-slide working deck with the first (3-fold) results |

Every slide has speaker notes (PowerPoint: View → Notes). All numbers come from
[`results/A0_10fold_paper/`](../results/A0_10fold_paper), [`results/A0_baseline/`](../results/A0_baseline) and, for the Phase 3 deck, [`results/ablation/`](../results/ablation) and [`results/phase3b/`](../results/phase3b).
GitHub cannot preview `.pptx` files; the PDF copies open directly in the browser. The Phase 2 PDFs were exported
from PowerPoint, the Phase 3 PDF from LibreOffice, with Carlito and Caladea standing in for Calibri and Cambria
(the same character widths, so the layout is unchanged).
