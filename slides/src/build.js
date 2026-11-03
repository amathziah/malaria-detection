// node build.js <repo> <out.pptx>
// Final deck: 17 slides plus references, in five parts that follow the brief's six steps.
const L = require("./build_deck.js");
const { pres, HEX, W, M, R, A0, ABL, T, card, iconBubble, cellImg, imgFit, stat, addSlide, partSlide, PARTS, fmt, pct, fa } = L;

const EXP = ABL ? Object.fromEntries(ABL.experiments.map((e) => [e.experiment, e])) : {};
const CON = ABL ? Object.fromEntries(ABL.contrasts.map((c) => [c.contrast, c])) : {};

// a compact callout: big number over a short label
function callout(s, x, y, w, big, label, color, dark = false, size = 30) {
  T(s, big, { x, y, w, h: 0.58, fontSize: size, bold: true, color, fontFace: "Cambria", valign: "bottom" });
  T(s, label, { x, y: y + 0.62, w, h: 0.62, fontSize: 13, color: dark ? "C9D3DF" : HEX.muted, valign: "top" });
}

async function main() {
  // ================================================================ 1 · title
  pres.addSection({ title: "Opening" });
  let s = addSlide("TITLE_DARK", "Opening", "CV RESEARCH-REPRODUCTION PROJECT · FINAL DEFENCE", "98 % Accuracy Holds on Unseen Patients");
  s.addText("Code-exact reproduction and pre-registered patient-level validation of an EfficientNet-B0 malaria ensemble",
    { placeholder: "body" });
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
  s.addNotes("Malaria is still diagnosed by a person counting blood cells under a microscope, and deep-learning papers report up to 99.9 per cent accuracy on the public NIH cell images. We took one of the strongest, an EfficientNet-B0 ensemble at 98 per cent, and asked two questions. Can it be rebuilt exactly from its authors' code? And does its accuracy hold on patients the model has never seen? The answer to both is yes, and the next slide shows the evidence.");

  // ================================================================ 2 · what we achieved
  s = addSlide("CONTENT_DARK", "Opening", "AT A GLANCE", "What we achieved");
  const a1 = EXP.A1, leak = L.P3B ? Math.abs(100 * L.P3B.E2.oof.mcc.est) : 0.85;
  const wins = [
    ["Within 1 pp", "of the paper on every metric, rebuilt from the authors' own code", "7FD3E0"],
    ["25× faster", "11 minutes per fold instead of 4 h 46 min, with the same maths", "7FD3E0"],
    [a1 ? pct(a1.ens_accuracy) + " %" : "98.45 %", `accuracy on 40 unseen patients; recall ${a1 ? pct(a1.ens_recall) : "98.05"} %, ROC-AUC ${a1 ? pct(a1.ens_auc) : "99.80"} %`, "F3A57F"],
    [fmt(leak) + " pp", "patient leakage in MCC, measured on 17,591 identical cells: small", HEX.white],
    ["±1 pp", "YUV stain normalisation is unnecessary: equivalent to no change", HEX.white],
    ["26 of 28", "infected patients found and 12 of 12 healthy cleared (exploratory)", HEX.white]];
  wins.forEach(([big, lab, col], i) => {
    const x = M + (i % 3) * 4.1, y = 1.6 + Math.floor(i / 3) * 2.3;
    T(s, big, { x, y, w: 3.8, h: 0.85, fontSize: 40, bold: true, color: col, fontFace: "Cambria", valign: "bottom" });
    T(s, lab, { x, y: y + 0.92, w: 3.7, h: 0.8, fontSize: 15, color: "C9D3DF", valign: "top" });
  });
  T(s, "Pre-registered before training · patient-level statistics · all 40 models and the code are public",
    { x: M, y: 6.3, w: W - 2 * M, h: 0.4, fontSize: 15, bold: true, color: "7FD3E0" });
  s.addNotes(`Six results carry the talk. We rebuilt the paper's ensemble from its authors' code and matched it within one point on every metric, while training 25 times faster. On 40 patients the models never saw, it scores ${a1 ? pct(a1.ens_accuracy) : "98.45"} per cent, with ${a1 ? pct(a1.ens_recall) : "98.05"} per cent recall and ${a1 ? pct(a1.ens_auc) : "99.80"} per cent ROC-AUC. Measured on identical cells, patient leakage is small, and the popular YUV stain normalisation turns out to be unnecessary. Combined per patient, the model finds 26 of 28 infected patients. Every analysis was fixed before training, and all 40 models are public.`);

  // ================================================================ 3 · roadmap: a visual journey through the five parts
  s = addSlide("CONTENT_DARK", "Opening", "ROADMAP", "Five parts, following the brief's six steps");
  const journey = [
    [fa.FaMicroscope, "The problem", "27,558 cells · 200 patients", "Brief step 1 · slides 4 to 6"],
    [fa.FaRedo, "Reproduction", "within 1 pp · 25× faster", "Brief steps 2 and 3 · slides 7 to 9"],
    [fa.FaFlask, "Our change", "2 predictions, fixed before training", "Brief step 4 · slide 10"],
    [fa.FaChartBar, "Results", "98.45 % on unseen patients", "Brief step 5 · slides 11 to 14"],
    [fa.FaSearch, "Failure analysis and conclusion", "26 of 28 patients found", "Brief step 6 · slides 15 to 17"]];
  const trackY = 3.95, node = 1.0, colW = (W - 2 * M) / journey.length;
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: trackY - 0.11, w: W - 2 * M, h: 0.22,
    fill: { color: "7FD3E0", transparency: 55 }, line: { color: "7FD3E0", width: 0, transparency: 100 }, objectName: "journey_track" });
  for (let i = 0; i < journey.length; i++) {
    const [Ico, name, teaser, step] = journey[i];
    const cx = M + (i + 0.5) * colW, nx = cx - node / 2, ny = trackY - node / 2;
    if (i < journey.length - 1) {
      s.addShape(pres.shapes.CHEVRON, { x: cx + colW / 2 - 0.09, y: trackY - 0.14, w: 0.18, h: 0.28,
        fill: { color: "7FD3E0" }, line: { color: "7FD3E0", width: 0 }, objectName: `journey_chevron_${i + 1}` });
    }
    s.addShape(pres.shapes.OVAL, { x: nx, y: ny, w: node, h: node, fill: { color: HEX.teal },
      line: { color: "7FD3E0", width: 2 }, objectName: `journey_node_${i + 1}` });
    s.addImage({ data: await L.icon(Ico, HEX.white), x: cx - 0.25, y: trackY - 0.25, w: 0.5, h: 0.5 });
    s.addShape(pres.shapes.OVAL, { x: nx + node - 0.27, y: ny - 0.07, w: 0.34, h: 0.34, fill: { color: HEX.white },
      line: { color: HEX.navy, width: 1.5 }, objectName: `journey_badge_${i + 1}` });
    T(s, String(i + 1), { x: nx + node - 0.27, y: ny - 0.07, w: 0.34, h: 0.34, fontSize: 12, bold: true, color: HEX.teal,
      align: "center", valign: "middle" });
    T(s, `PART ${i + 1}`, { x: cx - colW / 2 + 0.08, y: 2.0, w: colW - 0.16, h: 0.3, fontSize: 11, bold: true, color: "7FD3E0",
      charSpacing: 3, align: "center" });
    T(s, name, { x: cx - colW / 2 + 0.08, y: 2.3, w: colW - 0.16, h: 0.95, fontSize: 18, bold: true, color: HEX.white,
      fontFace: "Cambria", align: "center", valign: "top" });
    T(s, teaser, { x: cx - colW / 2 + 0.1, y: trackY + node / 2 + 0.25, w: colW - 0.2, h: 0.75, fontSize: 15, bold: true,
      color: "7FD3E0", align: "center", valign: "top" });
    T(s, step, { x: cx - colW / 2 + 0.1, y: trackY + node / 2 + 1.0, w: colW - 0.2, h: 0.55, fontSize: 11.5, color: "AEB7C4",
      align: "center", valign: "top" });
  }
  T(s, "The tracker at the top right of every slide shows where we are.",
    { x: M, y: 6.45, w: W - 2 * M, h: 0.35, fontSize: 14, color: "C9D3DF", italic: true, align: "center" });
  s.addNotes("The talk follows the brief in five parts, and each part has a headline. Part one, the problem: 27,558 cells from 200 patients. Part two, the reproduction: within one point of the paper, 25 times faster. Part three, our change: two predictions, fixed before any training. Part four, the results: 98.45 per cent on patients the model has never seen. Part five, the failure analysis and conclusion: 26 of 28 infected patients found. The tracker at the top right of every slide shows where we are.");

  // ================================================================ PART 1 · THE PROBLEM
  pres.addSection({ title: PARTS[0].section });

  // ---------------------------------------------------------------- 4 · problem and data
  s = partSlide(1, "Automating malaria microscopy, one cell at a time");
  const why = [[fa.FaHourglassHalf, "Slow", "Hundreds of cells per smear, checked by eye"],
    [fa.FaUserMd, "Expert-dependent", "Needs trained microscopists, scarce where malaria is common"],
    [fa.FaBalanceScale, "Variable", "Calls differ between observers and laboratories"]];
  for (let i = 0; i < why.length; i++) {
    const y = 1.7 + i * 1.12;
    await iconBubble(s, why[i][0], M, y, 0.62, HEX.navy);
    T(s, why[i][1], { x: M + 0.82, y: y - 0.04, w: 3.0, h: 0.36, fontSize: 17, bold: true, fontFace: "Cambria" });
    T(s, why[i][2], { x: M + 0.82, y: y + 0.32, w: 3.0, h: 0.6, fontSize: 13, color: HEX.muted, valign: "top" });
  }
  card(s, M, 5.2, 3.75, 1.45, HEX.tealTint, "goal");
  T(s, [{ text: "Our goal  ", options: { bold: true, color: HEX.teal } },
    { text: "call each red blood cell parasitized or uninfected, accurately on new patients." }],
  { x: M + 0.2, y: 5.3, w: 3.4, h: 1.25, fontSize: 15, valign: "middle" });
  const cells = [["parasitized_3", "parasitized"], ["parasitized_0", "parasitized"], ["parasitized_1", "parasitized"],
    ["uninfected_2", "uninfected"], ["uninfected_1", "uninfected"], ["uninfected_0", "uninfected"]];
  cells.forEach(([n, l], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    cellImg(s, n, 4.75 + col * 1.4, 1.85 + row * 2.2, 1.15, l === "parasitized" ? HEX.giemsa : HEX.line);
    T(s, l, { x: 4.6 + col * 1.4, y: 3.1 + row * 2.2, w: 1.45, h: 0.3, fontSize: 12, color: HEX.muted, align: "center" });
  });
  stat(s, 9.15, 1.5, 3.6, "27,558", "single-cell images from the NIH dataset, half parasitized", HEX.ink, false, 40);
  stat(s, 9.15, 3.25, 3.6, "200", "patients: 150 infected, 50 healthy", HEX.ink, false, 40);
  card(s, 9.15, 5.05, 3.58, 1.6, HEX.light, "filename");
  T(s, [{ text: "C33", options: { bold: true, color: HEX.orange } }, { text: "P1thinF_IMG_…_cell_179.png", options: { color: HEX.ink } }],
    { x: 9.35, y: 5.18, w: 3.3, h: 0.4, fontSize: 12, fontFace: "Courier New" });
  T(s, "Every file name starts with the patient ID; we verified all 27,558 against NIH's mapping.",
    { x: 9.35, y: 5.62, w: 3.25, h: 0.95, fontSize: 13, color: HEX.muted, valign: "top" });
  s.addNotes("Giemsa microscopy is the gold standard for malaria, but it is slow, it needs scarce experts, and calls vary between observers. Classifying single cells is a clean computer-vision task. The NIH dataset gives us 27,558 cell images, half parasitized, from 200 patients photographed at Chittagong Medical College Hospital. Crucially, every file name starts with the patient's ID, which we verified against NIH's own mapping. That is what lets us test the model on patients it has never seen.");

  // ---------------------------------------------------------------- 5 · literature
  s = partSlide(1, "11 studies report up to 99.9 %; 2 test unseen patients");
  const lit = [["Zhao '20", 96.5], ["Hemachandran '23", 97.06], ["Masud '20", 97.30], ["Liang '16", 97.37], ["Mujahid '24", 97.57],
    ["Marques '22 (base)", 98.29], ["Fuhad '20", 99.23], ["Madhu '23", 99.35], ["Umer '20", 99.9]];
  s.addChart(pres.charts.BAR, [{ name: "Reported accuracy (%)", labels: lit.map((r) => r[0]), values: lit.map((r) => r[1]) }], {
    x: M, y: 1.5, w: 7.6, h: 5.25, barDir: "bar", chartColors: [HEX.teal], invertedColors: [HEX.teal],
    valAxisMinVal: 95, valAxisMaxVal: 100, valAxisMajorUnit: 1, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0#", dataLabelFontSize: 12, dataLabelColor: HEX.ink, dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, catAxisLabelColor: HEX.ink, valAxisLabelColor: HEX.muted,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "E3E6EA", size: 0.75 },
    catGridLine: { style: "none" }, showLegend: false, showTitle: true, title: "Headline accuracy as reported (%) · axis starts at 95",
    titleFontSize: 13, titleColor: HEX.ink, titleFontFace: "+mn-lt", barGapWidthPct: 45,
  });
  const gaps = [[fa.FaUsers, "The open question", "9 of 11 split cells at random, so the same patients sit in training and test."],
    [fa.FaRandom, "Hard to compare", "5-fold, 10-fold and 80/20 protocols; original or cleaned labels."],
    [fa.FaCode, "Our base paper", "Marques et al. published executed code, so it can be rebuilt exactly."]];
  for (let i = 0; i < gaps.length; i++) {
    const y = 1.75 + i * 1.65;
    await iconBubble(s, gaps[i][0], 8.65, y, 0.7, i === 2 ? HEX.teal : HEX.navy);
    T(s, gaps[i][1], { x: 9.55, y: y - 0.05, w: 3.2, h: 0.4, fontSize: 17, bold: true, fontFace: "Cambria" });
    T(s, gaps[i][2], { x: 9.55, y: y + 0.38, w: 3.2, h: 1.1, fontSize: 13, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Step one of the brief is the literature survey. We reviewed eleven studies: they report between 96.5 and 99.9 per cent accuracy, on different protocols, so the numbers are hard to compare. Nine of the eleven split cells at random, which puts the same patients in training and test. Only Rajaraman and colleagues measured unseen patients. We chose Marques et al. as our base paper: a strong 98 per cent result, a standard architecture, and an executed notebook we could rebuild line by line.");

  // ---------------------------------------------------------------- 6 · the question
  s = partSlide(1, "Our question: does 98 % hold on new patients?");
  const pcol = ["D9622B", "00809A", "8E3B8E", "C9A227", "4C6A92", "7A9E7E"];
  const drawSplit = (x0, title, sub, assign) => {
    T(s, title, { x: x0, y: 1.6, w: 5.6, h: 0.45, fontSize: 20, bold: true, fontFace: "Cambria" });
    T(s, sub, { x: x0, y: 2.05, w: 5.6, h: 0.4, fontSize: 14, color: HEX.muted });
    [["TRAINING", 0], ["TEST", 1]].forEach(([lab, side]) => {
      const bx = x0 + side * 2.95;
      card(s, bx, 2.6, 2.65, 2.75, side ? HEX.orangeTint : HEX.tealTint, `${title}_${lab}`);
      T(s, lab, { x: bx + 0.2, y: 2.72, w: 2.2, h: 0.3, fontSize: 12, bold: true, color: side ? HEX.orange : HEX.teal, charSpacing: 2 });
      assign(side).forEach((p, j) => {
        const cx = bx + 0.3 + (j % 5) * 0.45, cy = 3.2 + Math.floor(j / 5) * 0.45;
        s.addShape(pres.shapes.OVAL, { x: cx, y: cy, w: 0.32, h: 0.32, fill: { color: pcol[p] }, line: { color: "FFFFFF", width: 1.5 } });
      });
    });
  };
  const rnd = [[0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 2, 4, 1, 3, 5], [1, 3, 5, 0, 2, 4]];
  drawSplit(M, "Image split (the paper)", "cells shuffled at random: every patient on both sides", (side) => rnd[side]);
  const grp = [[0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0, 1, 2, 3, 0, 1], [4, 4, 4, 5, 5, 5]];
  drawSplit(M + 6.25, "Patient split (ours)", "whole patients go to one side only", (side) => grp[side]);
  T(s, [{ text: "Each colour is one patient. ", options: { bold: true } },
    { text: "A patient's cells share stain, lighting and blood, so we hold out whole patients: the model must recognise the parasite, not the patient." }],
  { x: M, y: 5.7, w: W - 2 * M, h: 0.9, fontSize: 16, color: HEX.ink });
  s.addNotes("This is the question at the heart of the project. Under the paper's random image split, cells of the same patient sit in both training and test, so part of a high score could come from recognising the patient's stain and lighting. We split by patient instead: whole patients are held out, so the model has to recognise the parasite itself. If the 98 per cent survives this test, the result is real.");

  // ================================================================ PART 2 · REPRODUCTION
  pres.addSection({ title: PARTS[1].section });

  // ---------------------------------------------------------------- 7 · base paper and checklist
  s = partSlide(2, "Base paper checklist: every gap closed");
  const STATUS = { Yes: HEX.teal, Partly: HEX.orange, No: HEX.giemsa };
  const checklist = [["Checklist item", "Paper", "What we did"],
    ["Data public", "Yes", "Downloaded; patient IDs verified against NIH's mapping"],
    ["Code public", "Yes", "Rebuilt from the authors' executed notebook"],
    ["Model size", "Yes", "4,223,934 parameters, matched exactly"],
    ["Hyperparameters", "Partly", "Text and code differ in 8 places: we follow the code"],
    ["Data split", "No", "Seeded and fingerprinted: identical on every machine"],
    ["Evaluation protocol", "No", "Both reported: clean and augmented images"],
    ["Patient-level test", "No", "Our hypothesis H1"],
    ["Trained models", "No", "All 40 of ours public on GitHub"]];
  s.addTable(checklist.map((r, i) => r.map((c, j) => ({ text: c, options: {
    bold: i === 0 || j <= 1, color: i === 0 ? HEX.white : j === 1 ? STATUS[c] : j === 2 ? HEX.teal : HEX.ink,
    fill: { color: i === 0 ? HEX.navy : i % 2 ? HEX.white : HEX.light }, fontSize: 14, align: j === 1 ? "center" : "left" } }))),
  { x: M, y: 1.55, w: 8.3, colW: [2.3, 1.0, 5.0], rowH: 0.52, border: { type: "solid", pt: 0.5, color: HEX.line }, fontFace: "Calibri", valign: "middle", margin: 0.08 });
  card(s, 9.25, 1.55, 3.48, 4.68, HEX.light, "found");
  T(s, "Marques et al. (2022)", { x: 9.5, y: 1.7, w: 3.0, h: 0.35, fontSize: 15, bold: true, color: HEX.teal });
  callout(s, 9.5, 2.1, 3.0, "8", "places where the code differs from the paper's text; we follow the code", HEX.ink, false, 34);
  callout(s, 9.5, 3.55, 3.0, "3", "reporting errors we found and corrected", HEX.ink, false, 34);
  T(s, "Precision and recall swapped · test images augmented · \"accuracy\" = (P + R) / 2",
    { x: 9.5, y: 4.85, w: 3.0, h: 1.2, fontSize: 12, color: HEX.muted, italic: true, valign: "top" });
  s.addNotes("Step two of the brief is the reproducibility checklist for our base paper, Marques et al. 2022. The essentials are there: public data, the authors' executed notebook, and the exact model size. Where the paper was incomplete, we closed the gap: we seeded and fingerprinted the split, report both evaluation protocols, and publish all 40 of our models. Reading the code closely, we found eight places where it differs from the text, and three reporting errors, which we corrected in our paper.");

  // ---------------------------------------------------------------- 8 · model
  s = partSlide(2, "EfficientNet-B0 and the paper's head: 4.2 M parameters");
  imgFit(s, R("docs/figures/architecture.png"), M - 0.1, 1.4, W - 2 * M + 0.2, 5.0);
  T(s, "Ten fold models, each trained on a different nine tenths of the data, averaged into one ensemble.",
    { x: M, y: 6.45, w: W - 2 * M, h: 0.4, fontSize: 14, color: HEX.muted });
  s.addNotes("The model is the paper's exactly: a noisy-student EfficientNet-B0 backbone, sixteen MBConv blocks that turn a 224 by 224 cell into 1,280 features, and the paper's dense head of 128, 64 and 32 units with a two-way softmax. That is 4,223,934 parameters, matching the paper's Table 2 to the last digit, and an automated test checks it. Ten such models, one per cross-validation fold, are averaged into the ensemble.");

  // ---------------------------------------------------------------- 9 · reproduction result
  s = partSlide(2, "Reproduced within 1 pp of the paper, 25× faster");
  const metricsLbl = ["Fold acc.", "Ensemble acc.", "Recall", "Precision", "Specificity", "F1", "ROC-AUC"];
  const paperV = [97.56, 98.29, 97.74, 98.82, 98.84, 98.28, 99.76];
  const oursV = A0 ? [A0.mean_fold.accuracy, A0.ensemble.accuracy, A0.ensemble.recall, A0.ensemble.precision, A0.ensemble.specificity, A0.ensemble.f1, A0.ensemble.auc]
    : [97.55, 97.62, 97.07, 98.11, 98.17, 97.59, 99.73];
  s.addChart(pres.charts.BAR, [
    { name: "Marques et al. (2022)", labels: metricsLbl, values: paperV },
    { name: "Ours · 10 folds, paper protocol", labels: metricsLbl, values: oursV }], {
    x: M, y: 1.5, w: 8.6, h: 5.25, barDir: "col", barGrouping: "clustered", chartColors: ["A9C9D1", HEX.teal],
    valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.00", dataLabelFontSize: 9, dataLabelColor: HEX.ink, dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, catAxisLabelRotate: 0, valAxisLabelFontSize: 11, catAxisLabelColor: HEX.ink, valAxisLabelColor: HEX.muted,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "E3E6EA", size: 0.75 },
    catGridLine: { style: "none" }, showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt",
    legendColor: HEX.ink, showTitle: true, title: "Hold-out set, 5,512 cells (%)", titleFontSize: 13,
    titleColor: HEX.ink, titleFontFace: "+mn-lt", barGapWidthPct: 60,
  });
  callout(s, 9.6, 1.55, 3.13, "32", "automated tests check the rebuild against the paper's outputs", HEX.teal);
  callout(s, 9.6, 2.85, 3.13, "97.55 %", "mean fold accuracy, against the paper's 97.56 %", HEX.teal);
  callout(s, 9.6, 4.15, 3.13, "11 min", "per fold on one RTX 4090, against 4 h 46 min", HEX.ink);
  callout(s, 9.6, 5.45, 3.13, "US$6.95", "for 30 more models on ten cloud GPUs at once", HEX.ink);
  s.addNotes("Step three is the reproduction. Across all ten folds our models match the paper to a hundredth of a point, 97.55 against 97.56 per cent, and every headline metric is within one point, including ROC-AUC at 99.73 against 99.76. Thirty-two automated tests check the rebuild against the paper's printed outputs. We also made it fast without changing the maths: images decoded once, parallel seeded augmentation and a compiled training step bring a fold from nearly five hours to eleven minutes, so all 30 new models cost under seven dollars.");

  // ================================================================ PART 3 · OUR CHANGE
  pres.addSection({ title: PARTS[2].section });

  // ---------------------------------------------------------------- 10 · predictions and design
  s = partSlide(3, "Two predictions, fixed before training");
  const gx = 2.2, gy = 1.95, cw = 2.45, ch = 1.35, gp = 0.5;
  T(s, "image split (paper)", { x: gx, y: gy - 0.42, w: cw, h: 0.35, fontSize: 14, bold: true, color: HEX.orange, align: "center" });
  T(s, "patient split", { x: gx + cw + gp, y: gy - 0.42, w: cw, h: 0.35, fontSize: 14, bold: true, color: HEX.teal, align: "center" });
  T(s, "original RGB", { x: M, y: gy + ch / 2 - 0.2, w: 1.45, h: 0.4, fontSize: 14, bold: true, align: "right" });
  T(s, "YUV + hist-eq", { x: M, y: gy + ch + gp + ch / 2 - 0.2, w: 1.45, h: 0.4, fontSize: 14, bold: true, align: "right" });
  [["A0", "baseline", 0, 0, HEX.orange], ["A1", "H1", 1, 0, HEX.teal], ["A3", "control", 0, 1, HEX.orange], ["A2", "H2", 1, 1, HEX.teal]]
    .forEach(([id, sub, cx, cy, col]) => {
      const x = gx + cx * (cw + gp), y = gy + cy * (ch + gp);
      card(s, x, y, cw, ch, cx ? HEX.tealTint : HEX.orangeTint, `cell_${id}`);
      T(s, id, { x: x + 0.25, y: y + 0.18, w: 1.1, h: 0.7, fontSize: 34, bold: true, color: col, fontFace: "Cambria" });
      T(s, sub, { x: x + 0.25, y: y + 0.88, w: cw - 0.4, h: 0.35, fontSize: 14, color: HEX.ink });
    });
  const arrow = (x1, y1, x2, y2, label, lx, ly) => {
    s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
      line: { color: HEX.ink, width: 2, endArrowType: "triangle" } });
    T(s, label, { x: lx, y: ly, w: 0.9, h: 0.3, fontSize: 12, bold: true, color: HEX.ink });
  };
  arrow(gx + cw + 0.05, gy + ch / 2, gx + cw + gp - 0.05, gy + ch / 2, "H1", gx + cw + 0.08, gy + ch / 2 - 0.36);
  arrow(gx + cw / 2, gy + ch + 0.05, gx + cw / 2, gy + ch + gp - 0.05, "control", gx + cw / 2 + 0.1, gy + ch + 0.1);
  arrow(gx + cw + gp + cw / 2, gy + ch + 0.05, gx + cw + gp + cw / 2, gy + ch + gp - 0.05, "H2", gx + cw + gp + cw / 2 + 0.1, gy + ch + 0.1);
  const preds = [["H1 · PATIENT SPLIT", HEX.teal, "on unseen patients accuracy drops, and the fold-to-fold spread widens."],
    ["H2 · YUV STAIN NORMALISATION", HEX.giemsa, "equalising brightness raises recall and MCC on unseen patients."]];
  preds.forEach(([k, col, txt], i) => {
    const y = 1.55 + i * 1.95;
    card(s, 8.0, y, 4.73, 1.75, HEX.light, `pred_${i}`);
    T(s, k, { x: 8.25, y: y + 0.18, w: 4.3, h: 0.3, fontSize: 12, bold: true, color: col, charSpacing: 1 });
    T(s, [{ text: "We predicted  ", options: { bold: true, color: col } }, { text: txt }],
      { x: 8.25, y: y + 0.55, w: 4.3, h: 1.1, fontSize: 15, valign: "top" });
  });
  card(s, M, 5.6, W - 2 * M, 0.95, HEX.navy, "fixed");
  T(s, [{ text: "Committed to GitHub before training (0c086ee):  ", options: { bold: true, color: "7FD3E0" } },
    { text: "patient bootstrap · paired tests · Holm correction · MCC as the primary metric", options: { color: HEX.white } }],
  { x: M + 0.3, y: 5.65, w: W - 2 * M - 0.6, h: 0.85, fontSize: 15, valign: "middle" });
  s.addNotes("Step four: our change and our predictions, fixed before any new model was trained. The design is a two by two grid. A1 changes only the split, to unseen patients, and tests H1: we predicted that accuracy would drop and the folds would spread. A2 adds YUV histogram equalisation on those unseen patients, testing H2: we predicted higher recall and MCC. A3 is the control. Everything else is identical, and the hypotheses, decision rules and statistics were committed to GitHub before training, so the results could not shape the questions.");

  // ================================================================ parts 4 and 5, references
  await require("./results_slides.js")(L, EXP, CON, callout);

  await pres.writeFile({ fileName: L.OUT });
  await L.applyTheme(L.OUT, L.THEME);
  console.log("wrote", L.OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
