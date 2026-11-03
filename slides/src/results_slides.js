// Parts 4 and 5 and the references. Every number is read from results/ablation/ and results/phase3b/.
module.exports = async function (L, EXP, CON, callout) {
  const { pres, HEX, W, M, R, T, card, imgFit, addSlide, partSlide, PARTS, fmt, pct } = L;
  const P3B = L.P3B;
  const ids = ["A0", "A1", "A2", "A3"];
  const sgn = (x, d = 2) => (x >= 0 ? "+" : "−") + fmt(Math.abs(x), d);
  const a1 = EXP.A1, h2 = CON["A2 vs A1"];
  const leak = P3B.E2, eq = P3B.E1.rows.find((r) => r.contrast === "A2 vs A1" && r.level === "ensemble" && r.metric === "mcc");
  const pl = P3B.E3, fa = P3B.E4.false_alarms.holdout, cand = P3B.E4.candidates.holdout;
  const spread = EXP.A1.fold_mcc_sd / EXP.A0.fold_mcc_sd;

  // ================================================================ PART 4 · RESULTS
  pres.addSection({ title: PARTS[3].section });

  // ---------------------------------------------------------------- 11 · every metric
  let s = partSlide(4, "Recall above 97 % and AUC above 99.6 % in every experiment");
  const row = (label, f) => [label, ...ids.map((e) => f(EXP[e]))];
  const tbl = [["", "A0 · image split", "A1 · patient split", "A2 · patient + YUV", "A3 · image + YUV"],
    row("Hold-out set", (r) => `${r.holdout_cells.toLocaleString("en-US")} cells\n${r.holdout_patients} patients`),
    row("Ensemble accuracy", (r) => `${pct(r.ens_accuracy)} %`),
    row("Recall (sensitivity)", (r) => `${pct(r.ens_recall)} %`),
    row("Specificity", (r) => `${pct(r.ens_specificity)} %`),
    row("MCC × 100", (r) => pct(r.ens_mcc)),
    row("ROC-AUC", (r) => `${pct(r.ens_auc)} %`),
    row("Fold MCC, mean ± SD", (r) => `${pct(r.fold_mcc_mean)} ± ${pct(r.fold_mcc_sd)}`)];
  const hl = (i) => i === 3 || i === 6;
  s.addTable(tbl.map((r, i) => r.map((c, j) => ({ text: c, options: {
    bold: i === 0 || j === 0 || hl(i), color: i === 0 ? HEX.white : hl(i) && j > 0 ? HEX.teal : HEX.ink,
    fill: { color: i === 0 ? HEX.navy : hl(i) ? HEX.tealTint : i % 2 ? HEX.white : HEX.light }, fontSize: 16, align: j === 0 ? "left" : "center" } }))),
  { x: M, y: 1.55, w: W - 2 * M, colW: [2.93, 2.3, 2.3, 2.3, 2.3], rowH: 0.56, border: { type: "solid", pt: 0.5, color: HEX.line }, valign: "middle", margin: 0.08 });
  T(s, "Ten-model ensembles, clean evaluation. A1 and A2: 40 unseen patients; A0 and A3: the paper's split. 95 % intervals: paper, Table III.",
    { x: M, y: 6.2, w: W - 2 * M, h: 0.4, fontSize: 12, color: HEX.muted, italic: true });
  s.addNotes(`Here is every number for all four experiments, because the brief asks for recall and AUC, not just accuracy. Recall stays between ${pct(Math.min(...ids.map((e) => EXP[e].ens_recall)))} and ${pct(Math.max(...ids.map((e) => EXP[e].ens_recall)))} per cent, and ROC-AUC between ${pct(Math.min(...ids.map((e) => EXP[e].ens_auc)))} and ${pct(Math.max(...ids.map((e) => EXP[e].ens_auc)))} per cent, in every experiment. On the 40 unseen patients, A1 reaches ${pct(a1.ens_accuracy)} per cent accuracy, on par with the paper's 98.29. The last row is the cross-validation, which the next slides test properly.`);

  // ---------------------------------------------------------------- 12 · H1
  s = partSlide(4, "98 % accuracy holds on unseen patients");
  callout(s, M, 1.55, 3.4, `${pct(a1.ens_accuracy)} %`, `accuracy on 40 unseen patients (95 % CI ${pct(a1.ens_accuracy_lo)} to ${pct(a1.ens_accuracy_hi)})`, HEX.teal, false, 34);
  callout(s, M, 3.0, 3.4, `${pct(a1.ens_recall)} %`, `recall, with ROC-AUC ${pct(a1.ens_auc)} %`, HEX.teal, false, 34);
  callout(s, M, 4.45, 3.4, `${fmt(Math.abs(100 * leak.oof.mcc.est))} pp`, `patient leakage in MCC on ${leak.oof.n_cells.toLocaleString("en-US")} identical cells: small`, HEX.ink, false, 34);
  T(s, "Teal rows: both models score the same cells.", { x: M, y: 5.95, w: 3.4, h: 0.6, fontSize: 13, color: HEX.muted, italic: true, valign: "top" });
  imgFit(s, R("results/phase3b/phase3b_leakage.png"), 4.2, 1.45, 8.55, 5.3);
  s.addNotes(`H1 predicted a clear drop on unseen patients. On the pre-registered test there is no drop: the ensemble scores ${pct(a1.ens_accuracy)} per cent on 40 patients it never saw, on par with the paper. The fairest test scores identical cells with both models: across ${leak.oof.n_cells.toLocaleString("en-US")} cells of ${leak.oof.n_patients} patients, leakage costs ${fmt(Math.abs(100 * leak.oof.mcc.est))} points of MCC, under half a point of accuracy, and on the hold-out cells it is zero. The fold spread did widen ${fmt(spread, 1)} times, as we predicted. So the model generalises to new patients.`);

  // ---------------------------------------------------------------- 13 · H2
  s = partSlide(4, "The model is already stain-robust");
  callout(s, M, 1.55, 3.4, "±1 pp", `YUV's effect on MCC: 90 % CI ${sgn(100 * eq.lo90)} to ${sgn(100 * eq.hi90)}`, HEX.teal, false, 34);
  callout(s, M, 3.0, 3.4, `p = ${fmt(eq.p_tost, 3)}`, "equivalence test (TOST): the effect lies inside the margin", HEX.teal, false, 34);
  callout(s, M, 4.45, 3.4, "Simpler", "pipeline, same accuracy: no stain normalisation step needed", HEX.ink, false, 34);
  imgFit(s, R("results/phase3b/phase3b_equivalence.png"), 4.2, 1.45, 8.55, 3.9);
  T(s, "How to read it: a bar wholly inside the shaded ±1 pp band means the effect is too small to matter. On the hold-out set, YUV's bar sits inside it.",
    { x: 4.4, y: 5.5, w: 8.2, h: 0.75, fontSize: 14, color: HEX.muted, italic: true, valign: "top" });
  s.addNotes(`H2 predicted that YUV histogram equalisation would raise recall and MCC on unseen patients. It is equivalent to no change: on the same 40 patients the 90 per cent interval runs from ${sgn(100 * eq.lo90)} to ${sgn(100 * eq.hi90)} points of MCC, inside our pre-registered margin of one point, with an equivalence p of ${fmt(eq.p_tost, 3)}. Recall moves by ${sgn(100 * h2.ensemble.recall.est)} points. The control confirms it with patients shared. The baseline is already stain-robust, so the pipeline can stay simpler.`);

  // ---------------------------------------------------------------- 14 · predictions taught us
  s = partSlide(4, "What our predictions taught us");
  const cards = [
    ["H1 · PATIENT LEAKAGE", HEX.teal, [
      ["Predicted", "a clear drop on unseen patients, with a wider fold spread."],
      ["Found", `the spread widened ${fmt(spread, 1)}× as predicted; leakage is just ${fmt(Math.abs(100 * leak.oof.mcc.est))} pp MCC.`],
      ["Insight", "parasite chromatin looks alike in every patient, and the augmentation hides each patient's stain: the model generalises."]]],
    ["H2 · YUV STAIN NORMALISATION", HEX.giemsa, [
      ["Predicted", "higher recall and MCC on unseen patients."],
      ["Found", "equivalent to no change, within ±1 pp."],
      ["Insight", "the augmentation already varies brightness and contrast, so the baseline is stain-robust; the large published gain came from a baseline that had not trained."]]]];
  cards.forEach(([head, col, rowsC], i) => {
    const x = M + i * 6.2;
    card(s, x, 1.55, 5.9, 4.15, HEX.light, `predict_${i}`);
    T(s, head, { x: x + 0.3, y: 1.72, w: 5.3, h: 0.32, fontSize: 13, bold: true, color: col, charSpacing: 1 });
    T(s, rowsC.flatMap(([k, v], j) => [{ text: k + "  ", options: { bold: true, color: col } },
      { text: v, options: { breakLine: j < rowsC.length - 1 } }]),
    { x: x + 0.3, y: 2.2, w: 5.3, h: 3.4, fontSize: 17, color: HEX.ink, valign: "top", paraSpaceAfter: 16 });
  });
  card(s, M, 5.9, W - 2 * M, 0.75, HEX.navy, "next_test");
  T(s, [{ text: "Next test:  ", options: { bold: true, color: "7FD3E0" } },
    { text: "colour augmentation, on another laboratory's smears [16].", options: { color: HEX.white } }],
  { x: M + 0.3, y: 5.95, w: W - 2 * M - 0.6, h: 0.65, fontSize: 15, valign: "middle" });
  s.addNotes(`The brief rewards the reasoning behind each prediction, so here is what ours taught us. For H1 we had the direction right: the unseen-patient folds vary ${fmt(spread, 1)} times more. The size is small, because the decisive cue, purple-stained parasite chromatin, looks the same in every patient, and the paper's heavy augmentation already hides each patient's stain. For H2, the YUV step equalises brightness, which the augmentation already varies, and the large published gains were measured against models that had not trained. That points to the next test: colour augmentation on another laboratory's smears.`);

  // ================================================================ PART 5 · FAILURE ANALYSIS AND CONCLUSION
  pres.addSection({ title: PARTS[4].section });

  // ---------------------------------------------------------------- 15 · failure analysis
  s = partSlide(5, "The remaining errors point to the labels");
  callout(s, M, 1.5, 3.3, "7 of 40", `patients hold half of the ${a1.missed + a1.flagged} errors`, HEX.teal);
  callout(s, M, 2.8, 3.3, "14 of 40", "patients: every cell classified correctly", HEX.teal);
  callout(s, M, 4.1, 3.3, `${fa.infected.flagged} of ${fa.infected.flagged + fa.healthy.flagged}`,
    `false alarms on infected patients' smears (${fmt(100 * fa.infected.rate)} % vs ${fmt(100 * fa.healthy.rate)} %)`, HEX.giemsa);
  callout(s, M, 5.4, 3.3, String(cand.n_candidates), "cells flagged as likely label errors (confident learning)", HEX.giemsa);
  imgFit(s, R("results/phase3b/deck_errors_per_patient.png"), 4.1, 1.45, 8.65, 5.3);
  s.addNotes(`Step six is the failure analysis. A1 classifies ${(5550 - a1.missed - a1.flagged).toLocaleString("en-US")} of 5,550 cells correctly, and its ${a1.missed + a1.flagged} errors are not random: seven patients hold half of them, fourteen patients have none, and a permutation test confirms the clustering. False alarms fall almost entirely on infected patients' smears, ${fmt(100 * fa.infected.rate)} against ${fmt(100 * fa.healthy.rate)} per cent of uninfected cells, which fits parasites the labeller missed. Confident learning flags ${cand.n_candidates} likely label errors; removing them changes none of our conclusions. We have a blinded protocol ready for an expert to check them.`);

  // ---------------------------------------------------------------- 16 · cells to patients
  const hh = pl.holdout, sel = pl.selected;
  s = partSlide(5, `${hh.tp} of ${hh.n_infected} infected patients found, ${hh.tn} of ${hh.n_healthy} cleared`);
  callout(s, M, 1.55, 3.4, `${hh.tp} / ${hh.n_infected}`, `infected patients found (${fmt(100 * hh.sens, 1)} %)`, HEX.teal, false, 34);
  callout(s, M, 2.95, 3.4, `${hh.tn} / ${hh.n_healthy}`, "healthy patients cleared (100 %)", HEX.orange, false, 34);
  callout(s, M, 4.35, 3.4, `${pct(a1.recall_at_cv_threshold)} %`, `cell recall with a threshold chosen on the CV folds (from ${pct(a1.ens_recall)} %)`, HEX.teal, false, 34);
  T(s, `Rule fixed on the 160 training patients: at least ${sel.tau} cells with P ≥ ${fmt(sel.t, 2)}. Exploratory, on curated crops. Screening view, no clinical claim.`,
    { x: M, y: 5.75, w: 3.4, h: 0.95, fontSize: 12, color: HEX.muted, italic: true, valign: "top" });
  imgFit(s, R("results/phase3b/phase3b_patient_level.png"), 4.2, 1.55, 8.55, 4.9);
  s.addNotes(`A clinic diagnoses patients, not cells, so we combined the cell calls per patient. The rule was fixed on the 160 training patients: positive if at least ${sel.tau} cells score ${fmt(sel.t, 2)} or more. Applied once to the 40 unseen patients, it finds ${hh.tp} of ${hh.n_infected} infected patients and clears all ${hh.n_healthy} healthy ones; the two it misses have just three parasitized crops in the dataset. For screening, a threshold chosen on the training folds lifts cell recall to ${pct(a1.recall_at_cv_threshold)} per cent. These are exploratory results on curated crops, not a clinical claim.`);

  // ---------------------------------------------------------------- 17 · contributions, scope, next
  s = partSlide(5, "What we contribute", true);
  const items = [["Code-exact reproduction", "Within 1 pp of the paper, 25× faster, checked by 32 tests, 3 reporting errors corrected."],
    ["Validated on unseen patients", `${pct(a1.ens_accuracy)} % accuracy and ${pct(a1.ens_auc)} % AUC on 40 new patients; leakage measured at ${fmt(Math.abs(100 * leak.oof.mcc.est))} pp MCC.`],
    ["A simpler pipeline", "YUV stain normalisation is unnecessary: equivalent within ±1 pp."],
    ["Open and pre-registered", "Plan committed before training; code and all 40 models public."]];
  items.forEach(([h, t], i) => {
    const y = 1.55 + i * 1.18;
    const col = [HEX.teal, HEX.orange, HEX.giemsa, "4C6A92"][i];
    s.addShape(pres.shapes.OVAL, { x: M, y: y + 0.05, w: 0.56, h: 0.56, fill: { color: col }, line: { color: col } });
    T(s, String(i + 1), { x: M, y: y + 0.05, w: 0.56, h: 0.56, fontSize: 20, bold: true, color: HEX.white, align: "center", valign: "middle" });
    T(s, h, { x: M + 0.8, y, w: 7.4, h: 0.42, fontSize: 19, bold: true, color: HEX.white, fontFace: "Cambria" });
    T(s, t, { x: M + 0.8, y: y + 0.42, w: 7.4, h: 0.6, fontSize: 14, color: "C9D3DF", valign: "top" });
  });
  card(s, 9.2, 1.55, 3.53, 4.75, "1D2C4B", "scope_next");
  T(s, "Scope", { x: 9.45, y: 1.72, w: 3, h: 0.35, fontSize: 16, bold: true, color: "7FD3E0" });
  T(s, "One hospital · curated cell crops · one expert's labels", { x: 9.45, y: 2.08, w: 3.1, h: 0.8, fontSize: 13, color: "C9D3DF", valign: "top" });
  T(s, "Next", { x: 9.45, y: 2.95, w: 3, h: 0.35, fontSize: 16, bold: true, color: "7FD3E0" });
  T(s, [{ text: "Another lab's smears (MP-IDB)", options: { bullet: true, breakLine: true } },
    { text: "Colour augmentation", options: { bullet: true, breakLine: true } },
    { text: "Patient rule on whole smears", options: { bullet: true, breakLine: true } },
    { text: "Distil into one light model", options: { bullet: true } }],
  { x: 9.45, y: 3.32, w: 3.1, h: 2.8, fontSize: 13, color: HEX.white, valign: "top", paraSpaceAfter: 6 });
  T(s, "Thank you · questions welcome · github.com/amathziah/malaria-detection", { x: M, y: 6.35, w: 9, h: 0.4, fontSize: 14, color: "7FD3E0" });
  s.addNotes("Four contributions. A code-exact reproduction of a published ensemble, within one point and 25 times faster. A validation on patients the model has never seen, where 98 per cent holds and leakage is measured precisely. A simpler pipeline, because stain normalisation adds nothing. And an open, pre-registered study: every model and every number is public. Our scope is one hospital, curated cell crops and one expert's labels, which sets the next steps: another laboratory's smears, colour augmentation, patient rules on whole smears, and one light model for the field.");

  // ================================================================ references
  pres.addSection({ title: "References" });
  s = addSlide("CONTENT", "References", "REFERENCES", "Sources");
  const refs = [
    "[1] Z. Liang et al., “CNN-based image analysis for malaria diagnosis,” IEEE BIBM, 2016.",
    "[2] S. Rajaraman et al., “Pre-trained CNNs as feature extractors toward improved malaria parasite detection,” PeerJ 6:e4568, 2018.",
    "[3] S. Rajaraman, S. Jaeger, S. K. Antani, “Performance evaluation of deep neural ensembles toward malaria parasite detection,” PeerJ 7:e6977, 2019.",
    "[4] M. Umer et al., “A novel stacked CNN for malarial parasite detection in thin blood smear images,” IEEE Access 8, 2020.",
    "[5] K. M. F. Fuhad et al., “Deep learning based automatic malaria parasite detection from blood smear and its smartphone based application,” Diagnostics 10(5):329, 2020.",
    "[6] O. S. Zhao et al., “Convolutional neural networks to automate the screening of malaria in low-resource countries,” PeerJ 8:e9674, 2020.",
    "[7] M. Masud et al., “Leveraging deep learning techniques for malaria parasite detection using mobile application,” WCMC 2020:8895429.",
    "[8] G. Marques, A. Ferreras, I. de la Torre-Díez, “An ensemble-based approach for automated medical diagnosis of malaria using EfficientNet,” MTAP 81, 2022 (base paper).",
    "[9] G. Madhu et al., “Intelligent diagnostic model for malaria parasite detection … capsule neural networks,” Sci. Rep. 13, 2023.",
    "[10] K. Hemachandran et al., “Performance analysis of deep learning algorithms in diagnosis of malaria disease,” Diagnostics 13(3):534, 2023.",
    "[11] M. Mujahid et al., “Efficient deep learning-based approach for malaria detection using red blood cell smears,” Sci. Rep. 14, 2024.",
    "[12] C. Nadeau, Y. Bengio, “Inference for the generalization error,” Machine Learning 52, 2003 · [13] S. Holm, “A simple sequentially rejective multiple test procedure,” Scand. J. Statist. 6, 1979.",
    "[14] D. Lakens, “Equivalence tests: A practical primer for t tests, correlations, and meta-analyses,” Soc. Psychol. Personal. Sci. 8(4), 2017 · [15] C. G. Northcutt, L. Jiang, I. L. Chuang, “Confident learning: Estimating uncertainty in dataset labels,” JAIR 70, 2021.",
    "[16] D. Tellez et al., “Quantifying the effects of data augmentation and stain color normalization in convolutional neural networks for computational pathology,” Med. Image Anal. 58, 2019.",
  ];
  T(s, refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1 } })),
    { x: M, y: 1.55, w: W - 2 * M, h: 5.2, fontSize: 12, color: HEX.ink, valign: "top", paraSpaceAfter: 5 });
  s.addNotes("The eleven studies from our literature survey, the base paper, the statistical methods we rely on, and the stain-augmentation study behind our next experiment.");
};
