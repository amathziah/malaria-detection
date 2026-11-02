# Slides

| File | What it is |
|---|---|
| [`Malaria_Phase3_Final.pptx`](Malaria_Phase3_Final.pptx) · [PDF](Malaria_Phase3_Final.pdf) | **Final deck (Phase 3), 24 slides**: the problem, the data and the patient-leakage trap, the literature, the code-exact reproduction, H1/H2 with the 2 × 2 design and the statistics, the results (with leakage measured on identical cells), the clinical angle, the patient-level analysis, limitations, conclusion. Every number is generated from `results/` ([`src/`](src)) |
| [`Malaria_Phase2_Long.pptx`](Malaria_Phase2_Long.pptx) · [PDF](Malaria_Phase2_Long.pdf) | Full presentation, 31 slides: Phase 1 literature review, the base paper, what its own code revealed, how to read the metrics, the paper-exact 10-fold reproduction and its results (graphs for every result), the GPU engineering, hypotheses H1/H2 with the ablation plan, references |
| [`Malaria_Phase2_Short.pptx`](Malaria_Phase2_Short.pptx) · [PDF](Malaria_Phase2_Short.pdf) | Short version, 13 slides: everything done after Phase 1, with the results graphs |
| [`figures/`](figures) | The decks' graphs as PNG files (results vs. paper, per-fold accuracy, training curves, ROC, metrics primer, timing, speed-ups, cell samples, augmentation) |
| [`archive/`](archive) | Earlier decks: the original Phase 2 deck and the 24-slide working deck with the first (3-fold) results |

Every slide has speaker notes (PowerPoint: View → Notes). All numbers come from
[`results/A0_10fold_paper/`](../results/A0_10fold_paper), [`results/A0_baseline/`](../results/A0_baseline) and, for the Phase 3 deck, [`results/ablation/`](../results/ablation) and [`results/phase3b/`](../results/phase3b).
GitHub cannot preview `.pptx` files; the PDF copies open directly in the browser. The Phase 2 PDFs were exported
from PowerPoint, the Phase 3 PDF from LibreOffice, with Carlito and Caladea standing in for Calibri and Cambria
(the same character widths, so the layout is unchanged).
