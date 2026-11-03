// Results, conclusion and references: every number is read from results/ablation/ (ablation_stats.py output).
const fs = require("fs");

module.exports = async function (L, EXP, CON) {
  const { pres, HEX, W, M, R, T, card, iconBubble, imgFit, stat, addSlide, fmt, pct, fa } = L;
  const ABL = L.ABL, P3B = L.P3B;
  const p3 = (f) => R("results/phase3b", f);
  const pp = (x) => (x >= 0 ? "+" : "−") + fmt(Math.abs(100 * x)) + " pp";
  const ci = (e) => `95 % CI ${pp(e.lo)} to ${pp(e.hi)}`;
  const sig = (e) => e.p_holm < 0.05;
  const abl = (f) => R("results/ablation", f);

  // ================================================================ every metric, all four experiments (rule 2 of the brief)
  let s;
  const ids = ["A0", "A1", "A2", "A3"];
  if (ids.every((e) => EXP[e])) {
    s = addSlide("CONTENT", "Phase 3: results", "RESULTS AT A GLANCE", "Every metric, all four experiments");
    const row = (label, f) => [label, ...ids.map((e) => f(EXP[e]))];
    const tbl = [["", "A0 · image split", "A1 · patient split", "A2 · patient + YUV", "A3 · image + YUV"],
      row("Hold-out set", (r) => `${r.holdout_cells.toLocaleString("en-US")} cells, ${r.holdout_patients} patients`),
      row("Ensemble accuracy", (r) => `${pct(r.ens_accuracy)} %`),
      row("Recall (sensitivity)", (r) => `${pct(r.ens_recall)} %`),
      row("Specificity", (r) => `${pct(r.ens_specificity)} %`),
      row("MCC × 100", (r) => pct(r.ens_mcc)),
      row("ROC-AUC", (r) => `${pct(r.ens_auc)} %`),
      row("Missed / false alarms", (r) => `${r.missed} / ${r.flagged}`),
      row("Fold MCC, mean ± SD", (r) => `${pct(r.fold_mcc_mean)} ± ${pct(r.fold_mcc_sd)}`)];
    s.addTable(tbl.map((r, i) => r.map((c, j) => ({ text: c, options: {
      bold: i === 0 || j === 0 || i === 3 || i === 6, color: i === 0 ? HEX.white : (i === 3 || i === 6) && j > 0 ? HEX.teal : HEX.ink,
      fill: { color: i === 0 ? HEX.navy : i % 2 ? HEX.white : HEX.light }, fontSize: 15, align: j === 0 ? "left" : "center" } }))),
    { x: M, y: 1.55, w: W - 2 * M, colW: [2.93, 2.3, 2.3, 2.3, 2.3], rowH: 0.5, border: { type: "solid", pt: 0.5, color: HEX.line }, valign: "middle", margin: 0.08 });
    T(s, "Ten-model ensembles, clean evaluation, each on its own hold-out set: A1 and A2 share the 40 unseen patients; A0 and A3 share the paper's split, whose test cells come from all 200 patients. " +
      "95 % patient-bootstrap intervals are in the paper (Table III). Under the paper's augmented protocol A0 scores 97.62 % (slide 10).",
      { x: M, y: 6.1, w: W - 2 * M, h: 0.75, fontSize: 12, color: HEX.muted, italic: true, valign: "top" });
    s.addNotes(`Before the hypothesis tests, here is every number in one place, because the brief asks for recall and AUC, not just accuracy. Each column is a ten-model ensemble on its own hold-out set: A1 and A2 share the 40 unseen patients, while A0 and A3 share the paper's split. Recall stays between ${pct(Math.min(...ids.map((e) => EXP[e].ens_recall)))} and ${pct(Math.max(...ids.map((e) => EXP[e].ens_recall)))} per cent and ROC-AUC between ${pct(Math.min(...ids.map((e) => EXP[e].ens_auc)))} and ${pct(Math.max(...ids.map((e) => EXP[e].ens_auc)))} per cent in every experiment. The last row is the cross-validation: the patient-split folds score lower and vary more. The next slides test these differences properly.`);
  }

  // ================================================================ H1
  const h1 = CON["A1 vs A0"];
  s = addSlide("CONTENT", "Phase 3: results", "H1 · LEAKAGE",
    h1 ? (sig(h1.ensemble.mcc) && h1.ensemble.mcc.est < 0
      ? `Unseen patients cost ${fmt(Math.abs(100 * h1.ensemble.mcc.est), 1)} pp of MCC: H1 holds`
      : "Unseen patients cost little: H1 is not supported") : "H1 · results pending");
  if (h1) {
    const a0 = EXP.A0, a1 = EXP.A1;
    stat(s, M, 1.6, 3.4, `${pct(a0.ens_mcc, 1)} → ${pct(a1.ens_mcc, 1)}`, "ensemble MCC × 100: image split (A0) → patient split (A1)", HEX.teal, false, 36);
    stat(s, M, 3.25, 3.4, pp(h1.ensemble.mcc.est), `ensemble MCC on unseen patients, ${ci(h1.ensemble.mcc)}; Holm p = ${fmt(h1.ensemble.mcc.p_holm, 2)}`, h1.ensemble.mcc.est < 0 ? HEX.orange : HEX.teal);
    stat(s, M, 4.9, 3.4, pp(h1.fold.mcc.diff),
      `fold MCC over the 160 CV patients (${ci(h1.fold.mcc)}; Holm p = ${fmt(h1.fold.mcc.p_holm, 2)}): small and fragile`, HEX.orange);
    imgFit(s, abl("ablation_fold_mcc.png"), 4.25, 1.5, 8.5, 5.3);
  }
  s.addNotes(h1 ? `H1 asked whether splitting by patient lowers the scores. A0's ensemble MCC is ${pct(EXP.A0.ens_mcc)}; on the 40 unseen patients A1 reaches ${pct(EXP.A1.ens_mcc)}. The difference is ${pp(h1.ensemble.mcc.est)} with a ${ci(h1.ensemble.mcc)}, from a bootstrap that resamples whole patients. Each dot on the right is one fold; the orange experiments test on patients the model has seen, the teal ones on patients it has not. Cross-validation points the way H1 predicted, but once the folds' shared training data is accounted for the interval only just excludes zero and Holm p is ${fmt(h1.fold.mcc.p_holm, 2)}. The next slide measures leakage properly, on identical cells.` : "");

  // ================================================================ leakage on identical cells (Phase 3b)
  if (P3B && P3B.E2.oof.n_cells) {
    const lk = P3B.E2;
    s = addSlide("CONTENT", "Phase 3: results", "LEAKAGE ON IDENTICAL CELLS", "Scored on the same cells, leakage is real but small");
    stat(s, M, 1.6, 3.4, pp(lk.oof.mcc.est),
      `MCC on ${lk.oof.n_cells.toLocaleString("en-US")} cells of ${lk.oof.n_patients} patients, out-of-fold models (${ci(lk.oof.mcc)})`, HEX.orange);
    stat(s, M, 3.4, 3.4, pp(lk.holdout.mcc.est),
      `MCC on ${lk.holdout.n_cells.toLocaleString("en-US")} cells of the ${lk.holdout.n_patients} held-out patients, ensembles (${ci(lk.holdout.mcc)})`, HEX.teal);
    T(s, "Same cells, two models: one had seen other cells of the patient (A0), the other never saw the patient (A1).",
      { x: M, y: 5.3, w: 3.4, h: 1.2, fontSize: 14, color: HEX.muted, italic: true, valign: "top" });
    imgFit(s, p3("phase3b_leakage.png"), 4.25, 1.5, 8.5, 5.3);
    s.addNotes(`Both earlier comparisons score different cells, and the pre-registered one could only detect about two points of MCC. Here both models score the same cells. Across ${lk.oof.n_cells.toLocaleString("en-US")} cross-validation cells of ${lk.oof.n_patients} patients, the models that never saw the patient are ${fmt(Math.abs(100 * lk.oof.mcc.est))} points of MCC lower, with an interval from ${fmt(Math.abs(100 * lk.oof.mcc.hi))} to ${fmt(Math.abs(100 * lk.oof.mcc.lo))}. On the ${lk.holdout.n_cells.toLocaleString("en-US")} hold-out cells of our 40 unseen patients, the two ensembles make exactly the same number of each kind of error. So leakage exists on this dataset, but it costs about half a point of accuracy. This analysis was fixed in a dated addendum before we ran it.`);
  }

  // ================================================================ H2 + control
  const h2 = CON["A2 vs A1"], ctl = CON["A3 vs A0"];
  s = addSlide("CONTENT", "Phase 3: results", "H2 · STAIN NORMALISATION",
    h2 ? (sig(h2.ensemble.mcc) && h2.ensemble.mcc.est > 0 && h2.fold.mcc.diff >= h2.fold.mcc.ref_sd
      ? "YUV normalisation helps on unseen patients: H2 holds"
      : (sig(h2.ensemble.mcc) && h2.ensemble.mcc.est < 0 ? "YUV normalisation hurts on unseen patients: H2 is rejected"
        : "YUV normalisation doesn't help on unseen patients: H2 is rejected")) : "H2 · results pending");
  const eqH2 = P3B && P3B.E1.rows.find((r) => r.contrast === "A2 vs A1" && r.level === "ensemble" && r.metric === "mcc");
  if (h2) {
    imgFit(s, abl("ablation_contrasts.png"), M, 1.45, W - 2 * M, 3.35);
    const box = (x, title, col, lines) => {
      card(s, x, 4.95, 5.9, 1.85, HEX.light, `box_${title}`);
      T(s, title, { x: x + 0.3, y: 5.08, w: 5.4, h: 0.35, fontSize: 15, bold: true, color: col });
      T(s, lines, { x: x + 0.3, y: 5.45, w: 5.4, h: 1.3, fontSize: 13, color: HEX.ink, valign: "top" });
    };
    box(M, "H2 · A2 vs A1 (same 40 unseen patients)", HEX.giemsa,
      `Mean fold MCC ${pp(h2.fold.mcc.diff)} vs A1's fold SD ${fmt(100 * h2.fold.mcc.ref_sd)} pp (pre-registered rule: ` +
      `${h2.fold.mcc.diff < h2.fold.mcc.ref_sd ? "reject" : "keep"}). Ensemble MCC ${pp(h2.ensemble.mcc.est)}, ${ci(h2.ensemble.mcc)}` +
      (eqH2 ? `: equivalent to zero within ±1 pp (90 % CI ${pp(eqH2.lo90)} to ${pp(eqH2.hi90)}).` : `; recall ${pp(h2.ensemble.recall.est)}.`));
    box(M + 6.2, "Control · A3 vs A0 (patients shared)", HEX.orange,
      `Mean fold MCC ${pp(ctl.fold.mcc.diff)} vs A0's fold SD ${fmt(100 * ctl.fold.mcc.ref_sd)} pp. Ensemble MCC ${pp(ctl.ensemble.mcc.est)}, ${ci(ctl.ensemble.mcc)}: ` +
      (Math.abs(ctl.fold.mcc.diff) < ctl.fold.mcc.ref_sd ? "YUV changes little when patients are shared." : "YUV changes the score even when patients are shared."));
  }
  s.addNotes(h2 ? "Each panel shows a difference in percentage points with its 95 per cent interval; a filled dot means it survives the Holm correction. H2 is the middle row: the same 40 unseen patients, with and without the YUV step. The control row applies the same step under the paper's split." : "");

  // ================================================================ predictions vs outcomes (rule 1 of the brief)
  if (h1 && h2 && P3B) {
    s = addSlide("CONTENT", "Phase 3: results", "PREDICTIONS VS OUTCOMES", "Both predictions were wrong, and we can say why");
    const spread = EXP.A1.fold_mcc_sd / EXP.A0.fold_mcc_sd;
    const leak = Math.abs(100 * P3B.E2.oof.mcc.est);
    const cards = [
      ["H1 · PATIENT LEAKAGE", HEX.teal, [
        ["Predicted", "a clear drop on unseen patients, and a wider fold-to-fold spread."],
        ["Observed", `the spread widened ${fmt(spread, 1)}× as predicted, but the drop is small: ${fmt(leak)} pp of MCC on identical cells, and none on the 40-patient hold-out set.`],
        ["Likely why", "the decisive cue, purple-stained parasite chromatin, looks alike in every patient, and the paper's heavy colour, contrast and blur augmentation already hides each patient's stain."]]],
      ["H2 · YUV STAIN NORMALISATION", HEX.giemsa, [
        ["Predicted", "higher recall and MCC on unseen patients."],
        ["Observed", `MCC ${pp(h2.ensemble.mcc.est)}, within ±1 pp of zero; recall ${pp(h2.ensemble.recall.est)} and specificity ${pp(h2.ensemble.specificity.est)}, neither significant after correction.`],
        ["Likely why", "the step equalises brightness only, not stain colour; the augmentation already varies brightness and contrast; and Umer et al.'s large gain was measured against a model that had not trained."]]]];
    cards.forEach(([head, col, rowsC], i) => {
      const x = M + i * 6.2;
      card(s, x, 1.55, 5.9, 4.3, HEX.light, `predict_${i}`);
      T(s, head, { x: x + 0.3, y: 1.72, w: 5.3, h: 0.32, fontSize: 13, bold: true, color: col, charSpacing: 2 });
      T(s, rowsC.flatMap(([k, v], j) => [{ text: k + "  ", options: { bold: true, color: col } },
        { text: v, options: { breakLine: j < rowsC.length - 1 } }]),
      { x: x + 0.3, y: 2.2, w: 5.3, h: 3.55, fontSize: 16, color: HEX.ink, valign: "top", paraSpaceAfter: 14 });
    });
    card(s, M, 6.0, W - 2 * M, 0.82, HEX.navy, "learned");
    T(s, [{ text: "What we learned:  ", options: { bold: true, color: "7FD3E0" } },
      { text: "measure a gain against a strong baseline, and measure leakage on identical cells. Next test: colour augmentation on another lab's smears [16].", options: { color: HEX.white } }],
    { x: M + 0.3, y: 6.05, w: W - 2 * M - 0.6, h: 0.72, fontSize: 14, valign: "middle" });
    s.addNotes(`The brief says being wrong is fine if the reasoning is good, so here is ours. For H1 we got the direction right: the folds of unseen patients vary ${fmt(spread, 1)} times more. But the size was wrong: on identical cells, leakage costs under one point of MCC. The likely reason is that the decisive cue, the purple-stained parasite, looks the same in every patient, and the paper's augmentation already randomises colour and contrast, so the model can't lean on a patient's stain. For H2, the YUV step changes only brightness, not stain colour; the augmentation already covers brightness; and Umer's large gain was measured against a model that had failed to train. Our experiments don't separate these reasons, so we present them as the most likely explanations. The next experiment follows from them: colour augmentation, tested on another laboratory's smears.`);
  }

  // ================================================================ per patient (failure analysis)
  const csvPath = abl("ablation_per_patient.csv");
  s = addSlide("CONTENT", "Phase 3: results", "FAILURE ANALYSIS", "Errors cluster in a few patients");
  if (fs.existsSync(csvPath) && EXP.A1) {
    const rows = fs.readFileSync(csvPath, "utf8").trim().split("\n");
    const head = rows.shift().split(",");
    const recs = rows.map((r) => Object.fromEntries(r.split(",").map((v, i) => [head[i], v]))).filter((r) => r.experiment === "A1");
    const errs = recs.map((r) => +r.missed + +r.flagged).sort((a, b) => b - a);
    const total = errs.reduce((a, b) => a + b, 0);
    let cum = 0, nHalf = 0;
    while (cum < total / 2) cum += errs[nHalf++];
    const perfect = errs.filter((e) => e === 0).length;
    stat(s, M, 1.6, 3.3, `${nHalf} of ${recs.length}`, `held-out patients account for half of A1's ${total} errors`, HEX.orange);
    stat(s, M, 3.4, 3.3, `${perfect} / ${recs.length}`, "unseen patients with every cell classified correctly", HEX.teal);
    if (P3B) {
      const fa_ = P3B.E4.false_alarms.holdout;
      stat(s, M, 5.2, 3.3, `${fa_.infected.flagged} of ${fa_.infected.flagged + fa_.healthy.flagged}`,
        `false alarms fall on infected patients' smears (${fmt(100 * fa_.infected.rate)} % vs ${fmt(100 * fa_.healthy.rate)} % of uninfected cells)`, HEX.giemsa);
    } else {
      T(s, "Errors cluster by patient, not by chance: one more reason to evaluate, and to report, per patient.",
        { x: M, y: 5.3, w: 3.3, h: 1.2, fontSize: 14, color: HEX.muted, italic: true, valign: "top" });
    }
    imgFit(s, abl("ablation_per_patient_top12.png"), 4.2, 1.45, 8.55, 5.4);
  }
  s.addNotes("Looking per patient shows where the misses come from: half of the errors on the 40 unseen patients come from seven of them, and fourteen patients have none; a permutation test confirms the clustering. False alarms also concentrate on infected patients' smears, which fits some parasites missed in the labels, or genuinely ambiguous cells next to parasites. Without an expert we cannot tell which, so we prepared a blinded gallery of all 86 errors for our own triage. A single accuracy number hides all of this.");

  // ================================================================ screening view (no clinical claim)
  s = addSlide("CONTENT", "Phase 3: results", "SCREENING VIEW · NO CLINICAL CLAIM", "Recall first: a missed infection costs more than a false alarm");
  const rowsT = [["Experiment", "Threshold (chosen on CV folds)", "Hold-out recall at 0.5 → at threshold", "Specificity at threshold", "ECE"]];
  ["A0", "A1", "A2", "A3"].filter((e) => EXP[e]).forEach((e) => {
    const r = EXP[e];
    rowsT.push([e + (e === "A0" || e === "A3" ? " · image split" : " · patient split"), fmt(r.cv_threshold, 3),
      `${pct(r.ens_recall)} → ${pct(r.recall_at_cv_threshold)} %`, `${pct(r.specificity_at_cv_threshold)} %`, fmt(r.ece, 3)]);
  });
  s.addTable(rowsT.map((r, i) => r.map((c, j) => ({ text: c, options: {
    bold: i === 0 || j === 0, color: i === 0 ? HEX.white : HEX.ink, fill: { color: i === 0 ? HEX.navy : i % 2 ? HEX.white : HEX.light },
    fontSize: 14, align: j === 0 ? "left" : "center" } }))),
  { x: M, y: 1.7, w: W - 2 * M, colW: [2.6, 2.4, 3.3, 2.0, 1.83], rowH: 0.55, border: { type: "solid", pt: 0.5, color: HEX.line }, valign: "middle", margin: 0.08 });
  const why2 = [[fa.FaSearchPlus, "Tune for recall", "The decision threshold is chosen on the 10 CV folds (best F2), never on the hold-out set, then applied once."],
    [fa.FaThermometerHalf, "Calibration", "Label smoothing (0.1) caps confidence near 0.95, so probabilities read as under-confident (ECE ≈ 0.05)."]];
  for (let i = 0; i < why2.length; i++) {
    const x = M + i * 6.2;
    await iconBubble(s, why2[i][0], x, 5.05, 0.7, HEX.teal);
    T(s, why2[i][1], { x: x + 0.9, y: 5.0, w: 5.0, h: 0.4, fontSize: 17, bold: true, fontFace: "Cambria" });
    T(s, why2[i][2], { x: x + 0.9, y: 5.42, w: 5.0, h: 1.1, fontSize: 14, color: HEX.muted, valign: "top" });
  }
  s.addNotes("This is a screening-oriented view of the same predictions, not a clinical claim. For screening, missing an infected cell is worse than a false alarm. Choosing the threshold on the cross-validation folds, never on the test set, raises recall on the held-out cells at a modest cost in specificity. Calibration is also reported: the paper's label smoothing makes the probabilities under-confident.");

  // ================================================================ from cells to patients (Phase 3b)
  if (P3B) {
    const pl = P3B.E3, hh = pl.holdout, sel = pl.selected;
    s = addSlide("CONTENT", "Phase 3: results", "FROM CELLS TO PATIENTS", `Combined per patient: ${hh.tp} of ${hh.n_infected} infected, ${hh.tn} of ${hh.n_healthy} healthy`);
    stat(s, M, 1.6, 3.4, `${hh.tp} / ${hh.n_infected}`,
      `infected held-out patients found (${fmt(100 * hh.sens, 1)} %; 95 % CI ${fmt(100 * hh.sens_ci[0], 1)} to ${fmt(100 * hh.sens_ci[1], 1)})`, HEX.teal);
    stat(s, M, 3.4, 3.4, `${hh.tn} / ${hh.n_healthy}`,
      `healthy held-out patients cleared (95 % CI ${fmt(100 * hh.spec_ci[0], 1)} to ${fmt(100 * hh.spec_ci[1], 1)} %)`, HEX.orange);
    T(s, `Rule chosen on the 160 CV patients only: positive if at least ${sel.tau} cells have P ≥ ${fmt(sel.t, 2)}. Exploratory: NIH curated the crops, so this is not diagnostic accuracy on a smear.`,
      { x: M, y: 5.25, w: 3.4, h: 1.5, fontSize: 13, color: HEX.muted, italic: true, valign: "top" });
    imgFit(s, p3("phase3b_patient_level.png"), 4.25, 1.5, 8.5, 5.0);
    s.addNotes(`A clinic needs a diagnosis per patient, not per cell. We chose the rule on the 160 cross-validation patients only: positive if at least ${sel.tau} cells score ${fmt(sel.t, 2)} or more. Applied once to the 40 unseen patients, it finds ${hh.tp} of ${hh.n_infected} infected patients and clears all ${hh.n_healthy} healthy ones. The two it misses, ${hh.misclassified.join(" and ")}, are the only ones with just three parasitized cells in the dataset. This is exploratory: NIH selected the cell crops, so finding a patient here is easier than on a real smear.`);
  }

  // ================================================================ limitations
  pres.addSection({ title: "Closing" });
  s = addSlide("CONTENT", "Closing", "HONEST LIMITS", "What these results do not show");
  const lim = [[fa.FaUserInjured, "Curated cells, not smears", "Our patient-level rule is exploratory: NIH kept about 68 uninfected crops per patient and curated the parasitized ones, so it is not diagnostic accuracy on a smear."],
    [fa.FaHospital, "One hospital", "A patient split removes patient leakage, not site or stain-protocol effects; there is no external test set."],
    [fa.FaTag, "One expert's labels", "Fuhad et al. set aside 5.1 % of cells as mislabelled or suspicious, and our false alarms concentrate on infected smears. We keep the original labels, as the paper did."],
    [fa.FaDiceFive, "One split, one run", "A different draw of 40 hold-out patients, or a second training seed, would move the numbers; the CIs show by how much."]];
  for (let i = 0; i < lim.length; i++) {
    const col = i % 2, row = Math.floor(i / 2), x = M + col * 6.2, y = 1.7 + row * 2.45;
    card(s, x, y, 5.9, 2.15, HEX.light, `lim_${i}`);
    await iconBubble(s, lim[i][0], x + 0.3, y + 0.3, 0.75, HEX.orange);
    T(s, lim[i][1], { x: x + 1.3, y: y + 0.3, w: 4.4, h: 0.4, fontSize: 18, bold: true, fontFace: "Cambria" });
    T(s, lim[i][2], { x: x + 1.3, y: y + 0.75, w: 4.4, h: 1.3, fontSize: 14, color: HEX.muted, valign: "top" });
  }
  s.addNotes("Four limits. The patient-level result rests on curated crops, not whole smears. All data come from one hospital. Labels come from one expert, and our false alarms concentrate on infected patients' smears, which fits some label noise. And each comparison rests on one hold-out split and one training run per fold; the intervals quantify that uncertainty.");

  // ================================================================ conclusion
  s = addSlide("CONTENT_DARK", "Closing", "CONCLUSION", "What we take away");
  const items = [["Reproducible", "Rebuilt from the authors' code, the ensemble lands within 1 pp of the paper on every metric, trained 25× faster."],
    ["98 % survives unseen patients", h1 ? `${pct(EXP.A1.ens_accuracy)} % on 40 held-out patients. Leakage is real but small: ` +
      (P3B ? `${fmt(Math.abs(100 * P3B.E2.oof.mcc.est))} pp of MCC on identical cells. ` : `${pp(h1.fold.mcc.diff)} MCC in cross-validation. `) + "H1 is not supported." : "pending"],
    ["YUV doesn't help", h2 ? `Stain normalisation changes MCC on unseen patients by ${pp(h2.ensemble.mcc.est)}` +
      (eqH2 ? ", within ±1 pp of zero. H2 is rejected." : " and nothing on shared ones. H2 is rejected.") : "pending"]];
  items.forEach(([h, t], i) => {
    const y = 1.75 + i * 1.5;
    s.addShape(pres.shapes.OVAL, { x: M, y: y + 0.05, w: 0.62, h: 0.62, fill: { color: [HEX.teal, HEX.orange, HEX.giemsa][i] }, line: { color: [HEX.teal, HEX.orange, HEX.giemsa][i] } });
    T(s, String(i + 1), { x: M, y: y + 0.05, w: 0.62, h: 0.62, fontSize: 22, bold: true, color: HEX.white, align: "center", valign: "middle" });
    T(s, h, { x: M + 0.9, y, w: 7.3, h: 0.5, fontSize: 20, bold: true, color: HEX.white, fontFace: "Cambria" });
    T(s, t, { x: M + 0.9, y: y + 0.48, w: 7.3, h: 0.9, fontSize: 15, color: "C9D3DF", valign: "top" });
  });
  card(s, 9.2, 1.75, 3.53, 4.4, "1D2C4B", "next");
  T(s, "Next", { x: 9.45, y: 1.95, w: 3, h: 0.4, fontSize: 18, bold: true, color: "7FD3E0" });
  T(s, [{ text: "An external test set from another lab (MP-IDB)", options: { bullet: true, breakLine: true } },
    { text: "Blind triage of our errors; compare with an independent relabelling", options: { bullet: true, breakLine: true } },
    { text: "Patient-level rules on whole smears", options: { bullet: true, breakLine: true } },
    { text: "Distil the ensemble into one light model", options: { bullet: true } }],
  { x: 9.45, y: 2.45, w: 3.1, h: 3.5, fontSize: 14, color: HEX.white, valign: "top", paraSpaceAfter: 8 });
  T(s, "Thank you · questions welcome · github.com/amathziah/malaria-detection", { x: M, y: 6.35, w: 9, h: 0.4, fontSize: 14, color: "7FD3E0" });
  s.addNotes("Three takeaways: the paper is reproducible from its code; the leakage question has a measured answer; and so does the stain-normalisation question. The next steps follow from the limits.");

  // ================================================================ references
  s = addSlide("CONTENT", "Closing", "REFERENCES", "Sources");
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
  s.addNotes("The eleven studies from Phase 1, the base paper, the statistical methods we rely on, and the stain-augmentation study behind our next experiment.");
};
