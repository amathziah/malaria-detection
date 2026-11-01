// node build.js <repo> <out.pptx>
const L = require("./build_deck.js");
const { pres, HEX, W, M, R, A0, ABL, T, card, iconBubble, cellImg, imgFit, stat, addSlide, fmt, pct, fa } = L;

const EXP = ABL ? Object.fromEntries(ABL.experiments.map((e) => [e.experiment, e])) : {};
const CON = ABL ? Object.fromEntries(ABL.contrasts.map((c) => [c.contrast, c])) : {};
const have = (...ids) => ids.every((i) => EXP[i]);

async function main() {
  // ================================================================ 1 · title
  pres.addSection({ title: "Opening" });
  let s = addSlide("TITLE_DARK", "Opening", "PHASE 3 · FINAL PRESENTATION", "Does 98 % survive unseen patients?");
  s.addText("Reproducing an EfficientNet-B0 ensemble for malaria cell detection from its authors' own code, then testing it on patients it has never seen",
    { placeholder: "body" });
  // cluster of real cells (the deck's motif)
  cellImg(s, "parasitized_3", 8.55, 0.85, 2.7, "2B3A57");
  cellImg(s, "uninfected_2", 10.9, 2.65, 1.75, "2B3A57");
  cellImg(s, "parasitized_0", 8.2, 3.75, 1.9, "2B3A57");
  cellImg(s, "uninfected_1", 10.35, 4.65, 1.35, "2B3A57");
  cellImg(s, "parasitized_1", 11.75, 0.95, 1.15, "2B3A57");
  const team = [["J Amathziah", "230139"], ["C Murali Madhav", "230115"], ["Ravi Yadav", "230131"], ["Pugazhendhi J", "230066"]];
  team.forEach(([n, r], i) => {
    T(s, [{ text: n, options: { bold: true, color: HEX.white, breakLine: true } }, { text: r, options: { color: "AEB7C4" } }],
      { x: M + i * 1.85, y: 5.55, w: 1.8, h: 0.6, fontSize: 13 });
  });
  T(s, "Department of Computer Science · Rishihood University, Sonipat · github.com/amathziah/malaria-detection",
    { x: M, y: 6.55, w: 9, h: 0.3, fontSize: 11, color: "AEB7C4" });
  s.addNotes("Malaria is still diagnosed by a person counting cells under a microscope. Deep-learning papers report 96 to 99.9 per cent accuracy on the public NIH cell images. Our question is whether those numbers survive two tests: can we reproduce them exactly, and do they hold on patients the model has never seen?");

  // ================================================================ 2 · answer up front
  s = addSlide("CONTENT_DARK", "Opening", "THE ANSWER, UP FRONT", "Reproduced within 1 pp, then tested on unseen patients");
  const a1acc = have("A1") ? pct(EXP.A1.ens_accuracy) + " %" : "–";
  const yuv = CON["A2 vs A1"] ? (100 * CON["A2 vs A1"].ensemble.mcc.est >= 0 ? "+" : "−") + fmt(Math.abs(100 * CON["A2 vs A1"].ensemble.mcc.est)) + " pp" : "–";
  stat(s, M, 1.9, 3.7, "97.62 %", "ensemble accuracy with the paper's own recipe, 10 folds, paper protocol (paper: 98.29 %; every metric within 1 pp)", "7FD3E0", true);
  stat(s, M + 4.15, 1.9, 3.7, a1acc, "the same recipe on 40 patients no model ever saw (patient-level split, clean evaluation)", "F3A57F", true);
  stat(s, M + 8.3, 1.9, 3.6, yuv, "change in MCC from YUV stain normalisation on unseen patients", HEX.white, true);
  const h1c = CON["A1 vs A0"], h2c = CON["A2 vs A1"];
  T(s, h1c && h2c ? [
    { text: "Yes, largely: ", options: { bold: true, color: HEX.white } },
    { text: `the ensemble scores ${pct(EXP.A1.ens_accuracy)} % on 40 held-out patients. Cross-validation over the other 160 patients shows a small leakage effect (MCC ${(100 * h1c.fold.mcc.diff).toFixed(2).replace("-", "−")} pp). YUV stain normalisation does not help. By their pre-registered tests, both hypotheses are rejected.`, options: { color: "C9D3DF" } }]
    : "Results of the A1–A3 runs are added here once the analysis is in.",
    { x: M, y: 4.55, w: W - 2 * M, h: 1.6, fontSize: 18, valign: "top" });
  s.addNotes("Three numbers carry the talk. First, the paper's recipe, rebuilt from its own code, lands within one percentage point of the paper. Second, what happens to the same recipe when the test patients are new. Third, whether the stain normalisation we proposed helps on those new patients.");

  // ================================================================ 3 · why automate
  pres.addSection({ title: "Problem and data" });
  s = addSlide("CONTENT", "Problem and data", "THE PROBLEM", "Microscopy is the gold standard, and it doesn't scale");
  const why = [
    [fa.FaHourglassHalf, "Slow", "A thin smear holds hundreds of cells; a technician checks them one by one."],
    [fa.FaUserMd, "Expert-dependent", "It needs a trained microscopist, scarce exactly where malaria is common."],
    [fa.FaBalanceScale, "Subjective", "Counts and calls vary between observers and between laboratories."],
    [fa.FaMicroscope, "Automatable", "Single-cell images are a well-posed vision task: parasitized or uninfected."],
  ];
  for (let i = 0; i < why.length; i++) {
    const x = M + i * 3.07;
    card(s, x, 1.85, 2.85, 3.0, HEX.light, `why_${i}`);
    await iconBubble(s, why[i][0], x + 0.3, 2.15, 0.8, i === 3 ? HEX.teal : HEX.navy);
    T(s, why[i][1], { x: x + 0.3, y: 3.1, w: 2.3, h: 0.45, fontSize: 20, bold: true, fontFace: "Cambria" });
    T(s, why[i][2], { x: x + 0.3, y: 3.6, w: 2.3, h: 1.15, fontSize: 14, color: HEX.muted, valign: "top" });
  }
  T(s, [{ text: "Goal: ", options: { bold: true, color: HEX.teal } },
    { text: "classify single red-blood-cell images as parasitized or uninfected, accurately on new patients, and light enough to run where it is needed." }],
    { x: M, y: 5.3, w: W - 2 * M, h: 0.8, fontSize: 18 });
  s.addNotes("Giemsa microscopy works, but it is slow, it depends on scarce experts, and results vary between people and labs. Classifying single cells is a clean vision task, which is why so many papers attack it.");

  // ================================================================ 4 · dataset
  s = addSlide("CONTENT", "Problem and data", "THE DATA", "27,558 cells from 200 patients");
  stat(s, M, 1.75, 2.9, "27,558", "single-cell images, 50 % parasitized", HEX.ink);
  stat(s, M, 3.45, 2.9, "200", "patients: 150 infected, 50 healthy (Chittagong Medical College Hospital)", HEX.ink);
  stat(s, M, 5.15, 2.9, "75 %", "of uninfected cells come from infected patients' smears", HEX.orange);
  const cells = [["parasitized_3", "Parasitized"], ["parasitized_0", "Parasitized"], ["parasitized_1", "Parasitized"],
    ["uninfected_2", "Uninfected"], ["uninfected_1", "Uninfected"], ["uninfected_0", "Uninfected"]];
  cells.forEach(([n, l], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    cellImg(s, n, 4.25 + col * 1.75, 1.8 + row * 2.0, 1.45, l === "Parasitized" ? HEX.giemsa : HEX.line);
    T(s, l, { x: 4.1 + col * 1.75, y: 3.32 + row * 2.0, w: 1.75, h: 0.3, fontSize: 12, color: HEX.muted, align: "center" });
  });
  card(s, 9.6, 1.8, 3.13, 3.9, HEX.tealTint, "filename");
  T(s, "The patient is in the file name", { x: 9.85, y: 2.0, w: 2.7, h: 0.4, fontSize: 16, bold: true, color: HEX.teal });
  T(s, [{ text: "C33", options: { bold: true, color: HEX.orange } }, { text: "P1thinF_IMG_2015…_cell_179.png", options: { color: HEX.ink } }],
    { x: 9.85, y: 2.5, w: 2.75, h: 0.5, fontSize: 12, fontFace: "Courier New" });
  T(s, "C33 = patient 33. We checked this key against NIH's own patient-to-cell mapping: all 27,558 cells map to 200 patients.",
    { x: 9.85, y: 3.15, w: 2.7, h: 2.4, fontSize: 14, color: HEX.ink, valign: "top" });
  s.addNotes("The NIH dataset has 27,558 segmented cells, half parasitized. They come from 200 patients. Two facts matter for us: each file name starts with the patient's case number, and three quarters of the uninfected cells come from infected patients, so almost every patient contributes to both classes.");

  // ================================================================ 5 · the trap: image vs patient split
  s = addSlide("CONTENT", "Problem and data", "THE TRAP", "A random split puts the same patient on both sides");
  const pcol = ["D9622B", "00809A", "8E3B8E", "C9A227", "4C6A92", "7A9E7E"];
  const drawSplit = (x0, title, sub, assign) => {
    T(s, title, { x: x0, y: 1.7, w: 5.6, h: 0.45, fontSize: 20, bold: true, fontFace: "Cambria" });
    T(s, sub, { x: x0, y: 2.15, w: 5.6, h: 0.4, fontSize: 14, color: HEX.muted });
    [["TRAINING", 0], ["TEST", 1]].forEach(([lab, side]) => {
      const bx = x0 + side * 2.95;
      card(s, bx, 2.7, 2.65, 2.75, side ? HEX.orangeTint : HEX.tealTint, `${title}_${lab}`);
      T(s, lab, { x: bx + 0.2, y: 2.82, w: 2.2, h: 0.3, fontSize: 12, bold: true, color: side ? HEX.orange : HEX.teal, charSpacing: 2 });
      assign(side).forEach((p, j) => {
        const cx = bx + 0.3 + (j % 5) * 0.45, cy = 3.3 + Math.floor(j / 5) * 0.45;
        s.addShape(pres.shapes.OVAL, { x: cx, y: cy, w: 0.32, h: 0.32, fill: { color: pcol[p] }, line: { color: "FFFFFF", width: 1.5 } });
      });
    });
  };
  const rnd = [[0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 2, 4, 1, 3, 5], [1, 3, 5, 0, 2, 4]];
  drawSplit(M, "Image split (the paper)", "cells shuffled at random: every patient on both sides", (side) => rnd[side]);
  const grp = [[0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0, 1, 2, 3, 0, 1], [4, 4, 4, 5, 5, 5]];
  drawSplit(M + 6.25, "Patient split (ours)", "whole patients go to one side only", (side) => grp[side]);
  T(s, [{ text: "Each colour is one patient. ", options: { bold: true } },
    { text: "A patient's cells share stain, lighting and blood, so under an image split the model can recognise the patient instead of the parasite. Only 2 of the 11 studies we reviewed evaluate on unseen patients." }],
    { x: M, y: 5.75, w: W - 2 * M, h: 0.9, fontSize: 16, color: HEX.ink });
  s.addNotes("This is the core idea of the project. Under the paper's random image split, the same patient's cells sit in both training and test, so a high test score can come from recognising the patient's stain. A patient-level split removes that shortcut. In our literature review, only Rajaraman and colleagues reported patient-level results.");

  // ================================================================ 6 · literature
  s = addSlide("CONTENT", "Problem and data", "PHASE 1 · 11 STUDIES", "High reported accuracy, rarely measured on new patients");
  const lit = [["Zhao '20", 96.5], ["Hemachandran '23", 97.06], ["Masud '20", 97.30], ["Liang '16", 97.37], ["Mujahid '24", 97.57],
    ["Marques '22 (base)", 98.29], ["Fuhad '20", 99.23], ["Madhu '23", 99.35], ["Umer '20", 99.9]];
  s.addChart(pres.charts.BAR, [{ name: "Reported accuracy (%)", labels: lit.map((r) => r[0]), values: lit.map((r) => r[1]) }], {
    x: M, y: 1.6, w: 7.6, h: 5.1, barDir: "bar", chartColors: [HEX.teal], invertedColors: [HEX.teal],
    valAxisMinVal: 95, valAxisMaxVal: 100, valAxisMajorUnit: 1, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0#", dataLabelFontSize: 12, dataLabelColor: HEX.ink, dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, catAxisLabelColor: HEX.ink, valAxisLabelColor: HEX.muted,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "E3E6EA", size: 0.75 },
    catGridLine: { style: "none" }, showLegend: false, showTitle: true, title: "Headline accuracy as reported (%) · axis starts at 95",
    titleFontSize: 13, titleColor: HEX.ink, titleFontFace: "+mn-lt", barGapWidthPct: 45,
  });
  const gaps = [[fa.FaUsers, "Patient leakage", "Most split images at random; only Rajaraman et al. ['18, '19] test on unseen patients."],
    [fa.FaRandom, "Not comparable", "5-fold, 10-fold and 80:20 protocols; original or cleaned labels."],
    [fa.FaCode, "Rarely reproducible", "Marques et al. published their executed notebook, so we could rebuild it exactly."]];
  for (let i = 0; i < gaps.length; i++) {
    const y = 1.75 + i * 1.65;
    await iconBubble(s, gaps[i][0], 8.65, y, 0.7, i === 2 ? HEX.teal : HEX.orange);
    T(s, gaps[i][1], { x: 9.55, y: y - 0.05, w: 3.2, h: 0.4, fontSize: 17, bold: true, fontFace: "Cambria" });
    T(s, gaps[i][2], { x: 9.55, y: y + 0.38, w: 3.2, h: 1.1, fontSize: 13, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Phase 1 reviewed eleven studies. Accuracies cluster between 96.5 and 99.9 per cent, but protocols differ, and most split images at random. We picked Marques et al. as our base paper because their executed notebook is public, so the recipe can be rebuilt exactly.");

  // ================================================================ 7 · what the code revealed
  pres.addSection({ title: "Phase 2: reproduction" });
  s = addSlide("CONTENT", "Phase 2: reproduction", "PHASE 2 · BASE PAPER", "The authors' code differs from their paper's text");
  const diff = [["Setting", "Paper's text / our first guess", "Authors' code (what we follow)"],
    ["Weights", "ImageNet", "noisy-student, qubvel efficientnet 1.1.1"],
    ["Head", "GAP → dropout → 1 sigmoid", "GAP → 128 → 64 → 32 (dropout 0.3) → 2 softmax"],
    ["Loss", "binary cross-entropy", "categorical cross-entropy, label smoothing 0.1"],
    ["Schedule", "≤ 15 epochs, early stopping", "33 epochs, LR halved on plateau, best checkpoint"],
    ["Batch size", "128", "16 (1,240 steps per epoch)"],
    ["Hold-out", "10 %", "20 % = 5,512 images, never trained on"],
    ["Augmentation", "flips, 90° rotations", "heavy albumentations: noise, blur, distortions, CLAHE…"],
    ["Evaluation", "clean images", "augmented images (one generator for all)"]];
  s.addTable(diff.map((r, i) => r.map((c, j) => ({ text: c, options: {
    bold: i === 0 || j === 0, color: i === 0 ? HEX.white : j === 2 ? HEX.teal : HEX.ink,
    fill: { color: i === 0 ? HEX.navy : i % 2 ? HEX.white : HEX.light }, fontSize: i === 0 ? 13 : 13 } }))),
  { x: M, y: 1.65, w: 8.4, colW: [1.6, 3.0, 3.8], rowH: 0.47, border: { type: "solid", pt: 0.5, color: HEX.line }, fontFace: "Calibri", valign: "middle", margin: 0.08 });
  card(s, 9.35, 1.65, 3.38, 4.25, HEX.orangeTint, "paper_quirks");
  T(s, "Two things the paper's numbers hide", { x: 9.6, y: 1.85, w: 2.9, h: 0.75, fontSize: 16, bold: true, color: HEX.orange, valign: "top" });
  T(s, [{ text: "Precision and recall are swapped ", options: { bold: true } }, { text: "in the text: the true ensemble recall is 97.74 %, not 98.82 %.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Every reported prediction was on an augmented image. ", options: { bold: true } }, { text: "We report both protocols; it changes our numbers by ≤ 0.23 pp." }],
  { x: 9.6, y: 2.65, w: 2.95, h: 3.1, fontSize: 13, valign: "top" });
  T(s, "32 automated tests check the rebuild against the paper's printed outputs (e.g. its 4,223,934 parameters).",
    { x: M, y: 6.0, w: 8.4, h: 0.6, fontSize: 13, color: HEX.muted, italic: true });
  s.addNotes("Marques et al. published their executed notebook as a supplementary file. It differs from the paper's text in eight places, from the pretrained weights to the batch size, and we follow the code. Reading it closely also showed that the paper swaps precision and recall, and that every prediction it reports was made on a randomly augmented image.");

  // ================================================================ 8 · model
  s = addSlide("CONTENT", "Phase 2: reproduction", "THE MODEL", "EfficientNet-B0 with the paper's head: 4.2 M parameters");
  L.imgFit(s, R("docs/figures/architecture.png"), M - 0.2, 1.45, W - 2 * M + 0.4, 4.85);
  T(s, "224 × 224 cell → 16 MBConv blocks shrink the image to 7 × 7 while growing 3 colour channels into 1,280 feature maps → three dense layers → P(parasitized), P(uninfected). Ten such models, one per fold, are averaged.",
    { x: M, y: 6.25, w: W - 2 * M, h: 0.6, fontSize: 14, color: HEX.muted });
  s.addNotes("The backbone turns a 224 by 224 cell into 1,280 pattern strengths through a stem convolution and sixteen MBConv blocks in seven stages. The paper's head then narrows that to 128, 64 and 32 units and a two-way softmax. The ensemble averages the softmax outputs of the ten fold models.");

  // ================================================================ 9 · reproduction results (native chart)
  s = addSlide("CONTENT", "Phase 2: reproduction", "PHASE 2 · RESULT", "A faithful reproduction: every metric within 1 pp");
  const metricsLbl = ["Fold acc.", "Ensemble acc.", "Recall", "Precision", "Specificity", "F1", "ROC-AUC"];
  const paperV = [97.56, 98.29, 97.74, 98.82, 98.84, 98.28, 99.76];
  const oursV = A0 ? [A0.mean_fold.accuracy, A0.ensemble.accuracy, A0.ensemble.recall, A0.ensemble.precision, A0.ensemble.specificity, A0.ensemble.f1, A0.ensemble.auc]
    : [97.55, 97.62, 97.07, 98.11, 98.17, 97.59, 99.73];
  s.addChart(pres.charts.BAR, [
    { name: "Marques et al. (2022)", labels: metricsLbl, values: paperV },
    { name: "Ours · 10 folds, paper protocol", labels: metricsLbl, values: oursV }], {
    x: M, y: 1.55, w: 8.9, h: 5.15, barDir: "col", barGrouping: "clustered", chartColors: ["A9C9D1", HEX.teal],
    valAxisMinVal: 96, valAxisMaxVal: 100, valAxisMajorUnit: 1, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.00", dataLabelFontSize: 9, dataLabelColor: HEX.ink, dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, catAxisLabelRotate: 0, valAxisLabelFontSize: 11, catAxisLabelColor: HEX.ink, valAxisLabelColor: HEX.muted,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "E3E6EA", size: 0.75 },
    catGridLine: { style: "none" }, showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt",
    legendColor: HEX.ink, showTitle: true, title: "Hold-out set, 5,512 cells (%) · axis starts at 96", titleFontSize: 13,
    titleColor: HEX.ink, titleFontFace: "+mn-lt", barGapWidthPct: 60,
  });
  stat(s, 9.85, 1.75, 2.9, "−0.01 pp", "fold accuracy, 97.55 vs 97.56 %", HEX.teal);
  stat(s, 9.85, 3.55, 2.9, "−0.67 pp", "ensemble accuracy: 97.62 vs 98.29 % (≈ 3 standard errors)", HEX.orange);
  T(s, "Ensemble on 5,512 hold-out cells: 80 infected cells missed, 51 healthy cells flagged (paper: 62 and 32).",
    { x: 9.85, y: 5.4, w: 2.9, h: 1.2, fontSize: 13, color: HEX.muted, valign: "top" });
  s.addNotes("Across all ten folds, the fold models match the paper to a hundredth of a point: 97.55 against 97.56 per cent. The ensemble lands 0.67 points below the paper's 98.29. That gap is about three standard errors on 5,512 cells, so part of it is probably real; the paper's unseeded split, which cannot be recovered, and the newer TensorFlow are the remaining differences.");

  // ================================================================ 10 · engineering
  s = addSlide("CONTENT", "Phase 2: reproduction", "ENGINEERING", "Ten GPUs in parallel: 11 min per fold, not 4 h 46 min");
  stat(s, M, 1.7, 3.6, "≈ 25×", "faster per fold, same computation", HEX.teal);
  stat(s, M, 3.4, 3.6, "≈ 11 min", "per fold on an RTX 4090 (paper: 4 h 46 min on a GTX 1050)", HEX.ink);
  stat(s, M, 5.1, 3.6, "10", "RunPod GPUs at once, one fold each; trained models published as a GitHub release", HEX.ink);
  const speed = [[fa.FaDatabase, "Decode once", "27,558 images resized once into a shared uint8 cache"],
    [fa.FaCogs, "Parallel, seeded augmentation", "worker processes, each batch seeded by (fold, epoch, batch)"],
    [fa.FaMemory, "Bytes to the GPU", "uint8 batches, scaled by 1/255 inside the model"],
    [fa.FaBolt, "XLA-compiled step", "fused kernels: 21 → 12.5 ms per training step"],
    [fa.FaCheckCircle, "Same maths", "float32 throughout; results identical for any worker count"]];
  for (let i = 0; i < speed.length; i++) {
    const y = 1.75 + i * 0.98;
    await iconBubble(s, speed[i][0], 5.05, y, 0.62, i === 4 ? HEX.teal : HEX.navy);
    T(s, speed[i][1], { x: 5.9, y: y - 0.02, w: 6.8, h: 0.35, fontSize: 16, bold: true });
    T(s, speed[i][2], { x: 5.9, y: y + 0.32, w: 6.8, h: 0.35, fontSize: 13, color: HEX.muted });
  }
  s.addNotes("The paper needed nearly two days of GPU time. We changed nothing in the maths, only where time was wasted: decoding every image once, running the augmentation in parallel with per-batch seeds, sending bytes instead of floats to the GPU, and compiling the training step. Ten cloud GPUs then train the ten folds at the same time.");

  // ================================================================ 11 · section: phase 3
  pres.addSection({ title: "Phase 3: hypotheses" });
  s = addSlide("SECTION_DARK", "Phase 3: hypotheses", "PHASE 3", "Two hypotheses, one change at a time");
  s.addText("Registered in our Phase 2 deck, with the analysis plan committed before any new model was trained", { placeholder: "body" });
  cellImg(s, "parasitized_0", 9.1, 1.6, 2.4, "2B3A57");
  cellImg(s, "parasitized_0_yuv", 10.3, 3.7, 2.4, "2B3A57");

  // ================================================================ 12 · hypotheses
  s = addSlide("CONTENT", "Phase 3: hypotheses", "WHAT WE TEST", "H1: leakage inflates scores · H2: normalisation helps");
  const hyp = [["H1 · VALIDATION", "Split by patient, not by image", HEX.teal,
    "Accuracy and MCC fall below the image-split baseline; fold-to-fold spread widens.",
    "Cells of one patient share stain, lighting and blood: a random split lets the model recognise the patient."],
  ["H2 · PREPROCESSING", "YUV + histogram equalisation (Umer et al.)", HEX.giemsa,
    "Higher recall and MCC than H1 on unseen patients; little change on the random split.",
    "Equalising brightness removes slide-specific cues, so the network must rely on the parasite."]];
  hyp.forEach(([k, t, col, exp, why], i) => {
    const x = M + i * 6.2;
    card(s, x, 1.65, 5.9, 3.95, HEX.light, `hyp_${i}`);
    T(s, k, { x: x + 0.35, y: 1.85, w: 5.2, h: 0.3, fontSize: 12, bold: true, color: col, charSpacing: 2 });
    T(s, t, { x: x + 0.35, y: 2.2, w: 5.3, h: 0.5, fontSize: 21, bold: true, fontFace: "Cambria" });
    T(s, [{ text: "We expect  ", options: { bold: true, color: col } }, { text: exp, options: { breakLine: true } },
      { text: " ", options: { breakLine: true, fontSize: 8 } },
      { text: "Because  ", options: { bold: true, color: col } }, { text: why }],
    { x: x + 0.35, y: 2.85, w: 5.25, h: 2.6, fontSize: 15, valign: "top" });
  });
  card(s, M, 5.85, W - 2 * M, 0.85, HEX.navy, "falsify");
  T(s, [{ text: "Falsifiable:  ", options: { bold: true, color: "7FD3E0" } },
    { text: "if H2's gain over H1 is smaller than the fold-to-fold SD, we reject H2. If patient and image splits score the same, we reject H1.", options: { color: HEX.white } }],
  { x: M + 0.3, y: 5.95, w: W - 2 * M - 0.6, h: 0.65, fontSize: 15, valign: "middle" });
  s.addNotes("These are the hypotheses exactly as we stated them in Phase 2, with their falsification rules. We fixed them, and the full analysis plan, before training any of the new models, so the results cannot bend the questions.");

  // ================================================================ 13 · design matrix
  s = addSlide("CONTENT", "Phase 3: hypotheses", "ABLATION DESIGN", "A 2 × 2 design: each arrow changes one thing");
  const gx = 3.1, gy = 2.05, cw = 3.3, ch = 1.75, gap = 0.55;
  T(s, "image split (paper)", { x: gx, y: gy - 0.5, w: cw, h: 0.4, fontSize: 15, bold: true, color: HEX.orange, align: "center" });
  T(s, "patient split", { x: gx + cw + gap, y: gy - 0.5, w: cw, h: 0.4, fontSize: 15, bold: true, color: HEX.teal, align: "center" });
  T(s, "original RGB", { x: M, y: gy + 0.6, w: 2.3, h: 0.4, fontSize: 15, bold: true, align: "right" });
  T(s, "YUV + hist-eq", { x: M, y: gy + ch + gap + 0.6, w: 2.3, h: 0.4, fontSize: 15, bold: true, align: "right" });
  const cellsG = [["A0", "baseline · done", 0, 0, HEX.orange], ["A1", "H1", 1, 0, HEX.teal], ["A3", "control", 0, 1, HEX.orange], ["A2", "H2", 1, 1, HEX.teal]];
  cellsG.forEach(([id, sub, cx, cy, col]) => {
    const x = gx + cx * (cw + gap), y = gy + cy * (ch + gap);
    card(s, x, y, cw, ch, cx ? HEX.tealTint : HEX.orangeTint, `cell_${id}`);
    T(s, id, { x: x + 0.3, y: y + 0.2, w: 1.2, h: 0.8, fontSize: 40, bold: true, color: col, fontFace: "Cambria" });
    T(s, sub, { x: x + 0.3, y: y + 1.05, w: cw - 0.5, h: 0.4, fontSize: 15, color: HEX.ink });
    const r = EXP[id];
    if (r) T(s, `MCC ${pct(r.ens_mcc)}\nacc. ${pct(r.ens_accuracy)} %`, { x: x + 1.55, y: y + 0.25, w: 1.6, h: 0.8, fontSize: 14, color: HEX.ink, align: "right" });
  });
  const arrow = (x1, y1, x2, y2, label, lx, ly) => {
    s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
      line: { color: HEX.ink, width: 2, endArrowType: "triangle" }, flipH: x2 < x1, flipV: y2 < y1 });
    T(s, label, { x: lx, y: ly, w: 1.6, h: 0.3, fontSize: 12, bold: true, color: HEX.ink, align: "center" });
  };
  arrow(gx + cw + 0.05, gy + ch / 2, gx + cw + gap - 0.05, gy + ch / 2, "H1", gx + cw - 0.52, gy + ch / 2 - 0.42);
  arrow(gx + cw + gap + cw / 2, gy + ch + 0.05, gx + cw + gap + cw / 2, gy + ch + gap - 0.05, "H2", gx + cw + gap + cw / 2 + 0.05, gy + ch + 0.12);
  arrow(gx + cw / 2, gy + ch + 0.05, gx + cw / 2, gy + ch + gap - 0.05, "control", gx + cw / 2 + 0.05, gy + ch + 0.12);
  card(s, 10.5, 1.55, 2.23, 4.65, HEX.light, "same_recipe");
  T(s, "Held fixed", { x: 10.7, y: 1.75, w: 1.9, h: 0.35, fontSize: 15, bold: true, color: HEX.teal });
  T(s, "model and weights\nloss and optimiser\n33 epochs, batch 16\naugmentation\nper-fold seeds\n10-model ensemble\nA1 = A2 split\nA3 = A0 split",
    { x: 10.7, y: 2.15, w: 1.95, h: 3.9, fontSize: 13, color: HEX.ink, valign: "top", paraSpaceAfter: 4 });
  s.addNotes("The design is a two by two grid: split type across, preprocessing down. A0 is our reproduction. A1 changes only the split, which tests H1. A2 adds the YUV normalisation on the patient split, which tests H2. A3 applies YUV under the paper's split as a control. A1 and A2 share one split, and A3 reuses A0's split cell for cell, so those comparisons are paired.");

  // ================================================================ 14 · patient split + YUV
  s = addSlide("CONTENT", "Phase 3: hypotheses", "THE TWO SWITCHES", "40 held-out patients and a stain-normalised input");
  stat(s, M, 1.7, 3.0, "40", "patients held out (28 infected): 5,550 cells, 50.7 % parasitized", HEX.teal);
  stat(s, M, 3.4, 3.0, "160", "patients in 10 folds of 15–17 patients, StratifiedGroupKFold", HEX.ink);
  T(s, "Split committed to the repository; every run checks its fingerprint.", { x: M, y: 5.15, w: 3.0, h: 0.9, fontSize: 13, color: HEX.muted, italic: true, valign: "top" });
  const yuvPairs = [["parasitized_0", "parasitized_0_yuv", "Parasitized"], ["uninfected_0", "uninfected_0_yuv", "Uninfected"]];
  yuvPairs.forEach(([a, b, l], i) => {
    const y = 1.75 + i * 2.35;
    cellImg(s, a, 4.3, y, 1.9, HEX.line);
    cellImg(s, b, 7.1, y, 1.9, HEX.giemsa);
    s.addShape(pres.shapes.LINE, { x: 6.35, y: y + 0.95, w: 0.6, h: 0.001, line: { color: HEX.ink, width: 2, endArrowType: "triangle" } });
    T(s, l, { x: 4.3, y: y + 1.95, w: 4.7, h: 0.3, fontSize: 12, color: HEX.muted });
  });
  T(s, "original", { x: 4.3, y: 6.35, w: 1.9, h: 0.3, fontSize: 12, bold: true, align: "center" });
  T(s, "YUV + hist-eq", { x: 7.1, y: 6.35, w: 1.9, h: 0.3, fontSize: 12, bold: true, align: "center", color: HEX.giemsa });
  card(s, 9.55, 1.7, 3.18, 4.6, HEX.light, "yuv_steps");
  T(s, "How the YUV step works", { x: 9.8, y: 1.9, w: 2.8, h: 0.4, fontSize: 15, bold: true, color: HEX.giemsa });
  T(s, [{ text: "1  RGB → YUV (OpenCV)", options: { breakLine: true } },
    { text: "2  equalise the brightness (Y) histogram", options: { breakLine: true } },
    { text: "3  YUV → RGB, colour unchanged", options: { breakLine: true } },
    { text: "4  the paper's resize and augmentation" }],
  { x: 9.8, y: 2.4, w: 2.8, h: 2.1, fontSize: 13, valign: "top", paraSpaceAfter: 6 });
  T(s, "It stretches each cell's narrow brightness range to the full range, which also amplifies texture.",
    { x: 9.8, y: 4.65, w: 2.8, h: 1.5, fontSize: 13, color: HEX.muted, italic: true, valign: "top" });
  s.addNotes("The patient split holds out 40 whole patients, 5,550 cells, chosen by a rule on labels only. The remaining 160 patients form ten folds. On the right is H2's input: we convert each cell to YUV, equalise the brightness histogram, and convert back. The stretch is strong, which is exactly why it needs testing rather than assuming.");

  // ================================================================ 15 · statistics
  s = addSlide("CONTENT", "Phase 3: hypotheses", "HOW WE DECIDE", "Patients, not cells, are the unit of evidence");
  const st = [[fa.FaUserFriends, "Patient bootstrap", "Every interval resamples whole patients (10,000 times), because a patient's cells are not independent."],
    [fa.FaExchangeAlt, "Paired where possible", "A2 vs A1 and A3 vs A0 compare the same cells: corrected resampled t-test over folds (Nadeau & Bengio) and a paired bootstrap of the ensemble."],
    [fa.FaFilter, "Holm correction", "Three contrasts, so p-values are corrected for testing three times."],
    [fa.FaLock, "Fixed in advance", "Primary metric MCC, clean evaluation, decision rules: committed to GitHub before the runs."]];
  for (let i = 0; i < st.length; i++) {
    const col = i % 2, row = Math.floor(i / 2), x = M + col * 6.2, y = 1.7 + row * 2.45;
    card(s, x, y, 5.9, 2.15, HEX.light, `stat_${i}`);
    await iconBubble(s, st[i][0], x + 0.3, y + 0.3, 0.75, i === 3 ? HEX.teal : HEX.navy);
    T(s, st[i][1], { x: x + 1.3, y: y + 0.3, w: 4.4, h: 0.4, fontSize: 18, bold: true, fontFace: "Cambria" });
    T(s, st[i][2], { x: x + 1.3, y: y + 0.75, w: 4.4, h: 1.3, fontSize: 14, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Cells from one patient are correlated, so treating 5,500 cells as independent would make every difference look significant. All our intervals resample whole patients. Where two experiments share their cells we use paired tests, and we correct for running three comparisons. All of this was fixed before the runs.");

  // ================================================================ results slides (filled from results/ablation)
  pres.addSection({ title: "Phase 3: results" });
  await require("./results_slides.js")(L, EXP, CON);

  await pres.writeFile({ fileName: L.OUT });
  await L.applyTheme(L.OUT, L.THEME);
  console.log("wrote", L.OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
