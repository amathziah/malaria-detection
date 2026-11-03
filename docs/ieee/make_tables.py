#!/usr/bin/env python3
"""Write docs/ieee/tables.tex from the results files, so every number in the paper comes from results/.

Usage:
    python docs/ieee/make_tables.py                      # reads results/, writes docs/ieee/tables.tex
    python docs/ieee/make_tables.py --results <dir>      # e.g. a copy of results/ for a dry run
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def pct(x, d=2):
    return f"{100 * x:.{d}f}"


def signed(x, d=2):
    s = f"{100 * x:+.{d}f}"
    return s.replace("-", "$-$")


def p_fmt(p):
    if p != p:  # NaN
        return "n/a"
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def reproduction_table(a0):
    paper = a0["paper"]
    rows = [("Mean fold accuracy", paper["mean_fold_accuracy"], a0["mean_fold"]["accuracy"], a0["mean_fold_clean"]["accuracy"]),
            ("Ensemble accuracy", paper["accuracy"], a0["ensemble"]["accuracy"], a0["ensemble_clean"]["accuracy"]),
            ("Ensemble recall", paper["recall"], a0["ensemble"]["recall"], a0["ensemble_clean"]["recall"]),
            ("Ensemble precision", paper["precision"], a0["ensemble"]["precision"], a0["ensemble_clean"]["precision"]),
            ("Ensemble specificity", paper["specificity"], a0["ensemble"]["specificity"], a0["ensemble_clean"]["specificity"]),
            ("Ensemble F1", paper["f1"], a0["ensemble"]["f1"], a0["ensemble_clean"]["f1"]),
            ("Ensemble ROC-AUC", paper["auc"], a0["ensemble"]["auc"], a0["ensemble_clean"]["auc"])]
    lines = [r"\begin{table}[t]", r"\centering",
             r"\caption{Reproduction of~\cite{marques2022} on the 5{,}512-cell hold-out set (\%). ``Paper protocol'' scores augmented images, as the authors' code did; ``clean'' scores the original images.}",
             r"\label{tab:repro}", r"\footnotesize", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
             r"Metric & Paper & Ours (paper) & Ours (clean) & $\Delta$ \\", r"\midrule"]
    for name, p, o, c in rows:
        lines.append(f"{name} & {p:.2f} & {o:.2f} & {c:.2f} & {o - p:+.2f} \\\\".replace("+-", "-").replace(" -", " $-$"))
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def num(n):
    return f"{n:,}".replace(",", "{,}")


def experiments_table(abl):
    """Table III: one row of values per experiment, its 95 % intervals on a smaller row below."""
    lines = [r"\begin{table*}[t]", r"\centering",
             r"\caption{Ablation results, clean evaluation (\%). Folds: mean $\pm$ SD over the ten cross-validation "
             r"test parts. Ensemble: the ten-model ensemble on each hold-out set, with 95\,\% patient-bootstrap "
             r"intervals below each value. MCC $\times$100.}",
             r"\label{tab:ablation}", r"\footnotesize", r"\setlength{\tabcolsep}{4pt}",
             r"\resizebox{\ifdim\width>\textwidth\textwidth\else\width\fi}{!}{%",
             r"\begin{tabular}{@{}lllrrcccccc@{}}", r"\toprule",
             r" & & & \multicolumn{2}{c}{Hold-out set} & \multicolumn{2}{c}{Folds, mean $\pm$ SD} & "
             r"\multicolumn{4}{c}{Ensemble on the hold-out set [95\,\% CI]} \\",
             r"\cmidrule(lr){4-5} \cmidrule(lr){6-7} \cmidrule(l){8-11}",
             r"ID & Split & Prep. & Cells & Patients & MCC & Accuracy & Accuracy & MCC & Recall & ROC-AUC \\",
             r"\midrule"]
    metrics = ("accuracy", "mcc", "recall", "auc")
    for i, r in enumerate(abl["experiments"]):
        prep = "YUV" if r["preprocess"] == "yuv" else "none"
        lines.append(f"{r['experiment']} & {r['split']} & {prep} & {num(r['holdout_cells'])} & {r['holdout_patients']} & "
                     f"{pct(r['fold_mcc_mean'])} $\\pm$ {pct(r['fold_mcc_sd'])} & "
                     f"{pct(r['fold_accuracy_mean'])} $\\pm$ {pct(r['fold_accuracy_sd'])} & "
                     + " & ".join(pct(r["ens_" + m]) for m in metrics) + r" \\")
        cis = " & ".join(rf"{{\scriptsize [{pct(r['ens_' + m + '_lo'])}, {pct(r['ens_' + m + '_hi'])}]}}"
                         for m in metrics)
        gap = r"[3pt]" if i < len(abl["experiments"]) - 1 else ""
        lines.append(f" & & & & & & & {cis} \\\\{gap}")
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table*}"]
    return "\n".join(lines)


def contrasts_table(abl):
    names = {"A1 vs A0": "H1: A1 $-$ A0 (unpaired)", "A2 vs A1": "H2: A2 $-$ A1 (paired)", "A3 vs A0": "Control: A3 $-$ A0 (paired)"}
    metrics = [("mcc", "MCC"), ("accuracy", "Accuracy"), ("recall", "Recall"), ("specificity", "Specificity"), ("auc", "ROC-AUC")]
    lines = [r"\begin{table*}[t]", r"\centering",
             r"\caption{Contrasts (new $-$ reference, percentage points). Fold: mean difference over the ten folds with 95\,\% CI (the corrected resampled $t$ of Nadeau and Bengio; for the unpaired H1 contrast, a Welch-type $t$ with the correction applied to each arm). Ensemble: hold-out difference with 95\,\% patient-bootstrap CI. $p$-values Holm-corrected over the three contrasts.}",
             r"\label{tab:contrasts}", r"\begin{tabular}{@{}llrrrr@{}}", r"\toprule",
             r"Contrast & Metric & Fold $\Delta$ [95\,\% CI] & Fold $p_{\mathrm{Holm}}$ & Ensemble $\Delta$ [95\,\% CI] & Ens. $p_{\mathrm{Holm}}$ \\",
             r"\midrule"]
    for c in abl["contrasts"]:
        for i, (m, label) in enumerate(metrics):
            f, e = c["fold"][m], c["ensemble"][m]
            first = names.get(c["contrast"], c["contrast"]) if i == 0 else ""
            lines.append(f"{first} & {label} & {signed(f['est'])} [{signed(f['lo'])}, {signed(f['hi'])}] & {p_fmt(f['p_holm'])} & "
                         f"{signed(e['est'])} [{signed(e['lo'])}, {signed(e['hi'])}] & {p_fmt(e['p_holm'])} \\\\")
        lines.append(r"\midrule" if c is not abl["contrasts"][-1] else r"\bottomrule")
    lines += [r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines)


def extras_table(abl):
    """Table V: the recall-first threshold and each ensemble's calibration."""
    lines = [r"\begin{table}[t]", r"\centering",
             r"\caption{Recall-first threshold (best $F_2$ on the cross-validation predictions, applied once to the "
             r"hold-out set) and expected calibration error (ECE). Clean evaluation, \%.}",
             r"\label{tab:extras}", r"\footnotesize", r"\setlength{\tabcolsep}{4pt}",
             r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
             r" & & \multicolumn{2}{c}{Recall} & Specificity & \\", r"\cmidrule(lr){3-4}",
             r"ID & Threshold & at 0.5 & at threshold & at threshold & ECE \\", r"\midrule"]
    for r in abl["experiments"]:
        lines.append(f"{r['experiment']} & {r['cv_threshold']:.3f} & {pct(r['ens_recall'])} & "
                     f"{pct(r['recall_at_cv_threshold'])} & {pct(r['specificity_at_cv_threshold'])} & "
                     f"{r['ece']:.3f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def phase3b_table(p3b):
    """Table VI: the exploratory analyses of docs/phase3b_addendum.md in three groups (same-cell leakage, the YUV
    equivalence tests with their verdict in its own column, the patient-level rule)."""
    e1, e2, h = p3b["E1"], p3b["E2"], p3b["E3"]["holdout"]
    group = lambda title: rf"\multicolumn{{4}}{{@{{}}l}}{{\textit{{{title}}}}} \\"
    lines = [r"\begin{table}[t]", r"\centering",
             r"\caption{Exploratory analyses, fixed in a dated addendum before they were run. Clean evaluation. "
             r"The leakage rows score 1{,}095 hold-out and 17{,}591 cross-validation cells; H2 is A2 $-$ A1, the "
             r"control A3 $-$ A0.}", r"\label{tab:phase3b}", r"\footnotesize",
             r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}lrrc@{}}", r"\toprule",
             r" & & & Within \\",
             r"Analysis & Estimate & Interval & $\pm$1\,pp? \\", r"\midrule",
             group(r"Leakage on identical cells: A1 $-$ A0, MCC (pp), 95\,\% CI")]
    for key, name in [("holdout", "Ensembles"), ("oof", "Out-of-fold")]:
        b = e2[key]
        lines.append(f"\\quad {name}, {b['n_patients']} patients & {signed(b['mcc']['est'])} & "
                     f"[{signed(b['mcc']['lo'])}, {signed(b['mcc']['hi'])}] & \\\\")
    lines += [r"\addlinespace", group(r"YUV effect: MCC (pp), 90\,\% CI")]
    names = {"A2 vs A1": "H2", "A3 vs A0": "Control"}
    for r in e1["rows"]:
        if r["metric"] == "mcc" and "lo90" in r:
            lines.append(f"\\quad {names[r['contrast']]}, {'ensembles' if r['level'] == 'ensemble' else 'folds'} & "
                         f"{signed(r['est'])} & [{signed(r['lo90'])}, {signed(r['hi90'])}] & "
                         f"{'yes' if r['equivalent'] else 'no'} \\\\")
    lines += [r"\addlinespace", group(r"Patient level: 40 held-out patients, \%, exact 95\,\% CI")]
    for label, k, n, ci in [("Sensitivity", h["tp"], h["n_infected"], h["sens_ci"]),
                            ("Specificity", h["tn"], h["n_healthy"], h["spec_ci"])]:
        lines.append(f"\\quad {label}, {k}/{n} & {100 * k / n:.1f} & [{100 * ci[0]:.1f}, {100 * ci[1]:.1f}] & \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(REPO, "results"))
    ap.add_argument("--out", default=os.path.join(HERE, "tables.tex"))
    args = ap.parse_args()
    a0 = json.load(open(os.path.join(args.results, "A0_10fold_paper", "A0_10fold_summary.json")))
    abl = json.load(open(os.path.join(args.results, "ablation", "ablation_summary.json")))
    p3b = json.load(open(os.path.join(args.results, "phase3b", "phase3b_summary.json")))
    with open(args.out, "w") as fh:
        fh.write("% Generated by docs/ieee/make_tables.py from results/: do not edit by hand.\n")
        for t in [reproduction_table(a0), experiments_table(abl), contrasts_table(abl), extras_table(abl),
                  phase3b_table(p3b)]:
            fh.write(t + "\n\n")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
