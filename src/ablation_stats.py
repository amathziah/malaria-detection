"""Statistics for the ablation: do the numbers support H1 (patient leakage) and H2 (YUV normalisation)?

Usage:
    python src/ablation_stats.py                       # reads results/<A0-A3>/folds, writes results/ablation/
    python src/ablation_stats.py --n-boot 2000         # quicker, wider-grained intervals

Design (fixed before the A1-A3 runs):
  * Unit of independence = patient. Cells of one patient share stain, light and the patient's blood, so
    every confidence interval resamples whole patients (cluster bootstrap), never single cells.
  * Primary protocol = clean (un-augmented) evaluation; the paper protocol (augmented) is reported as well.
    Primary metric = MCC; also accuracy, recall, specificity, balanced accuracy, F2 and ROC-AUC.
  * Paired contrasts (same cells in both arms: A2 vs A1, A3 vs A0):
      - 10 folds: Nadeau-Bengio corrected resampled t-test on the per-fold differences (the folds'
        training sets overlap by ~89 %, so a plain paired t-test is too optimistic);
      - 10-model ensemble on the hold-out set: paired patient bootstrap of the difference.
  * Unpaired contrast (different hold-out sets: A1 vs A0): independent patient bootstraps per arm.
  * Holm correction over the three contrasts, separately for each metric and level.
  * The deck's pre-registered rules are reported next to the tests (slide 28 of the long deck):
      H1 is rejected if grouped and random splits score the same;
      H2 is rejected if its gain over A1 is smaller than A1's fold-to-fold SD.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats as sps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marques2022_exact as mx  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMARY = "clean"
PROTOCOLS = {"clean": ("test_clean", "val_clean"), "paper": ("test_aug", "val_aug")}
METRIC_ORDER = ["mcc", "accuracy", "recall", "specificity", "balanced_accuracy", "f2", "auc"]
# (new arm, reference arm, paired?, question): difference = new - reference
CONTRASTS = [
    ("A1", "A0", False, "H1: patient-level split vs the paper's image split (leakage)"),
    ("A2", "A1", True, "H2: YUV stain normalisation on unseen patients"),
    ("A3", "A0", True, "Control: YUV stain normalisation when patients are shared"),
]


# ----------------------------------------------------------------------------- weighted metrics
# y: 0 = parasitized, 1 = uninfected (mx.TIPOS order); s: P(parasitized); w: cell weights (bootstrap counts).
# A cell is called parasitized when s >= threshold; at 0.5 that is the softmax argmax (ties go to class 0).
def _confusion(y, s, w, threshold=0.5):
    pos, pred = y == 0, s >= threshold
    return (w[pos & pred].sum(), w[pos & ~pred].sum(), w[~pos & pred].sum(), w[~pos & ~pred].sum())


def _ratio(a, b):
    return float(a / b) if b else float("nan")


def _accuracy(y, s, w, threshold=0.5):
    tp, fn, fp, tn = _confusion(y, s, w, threshold)
    return _ratio(tp + tn, tp + fn + fp + tn)


def _recall(y, s, w, threshold=0.5):
    tp, fn, _, _ = _confusion(y, s, w, threshold)
    return _ratio(tp, tp + fn)


def _specificity(y, s, w, threshold=0.5):
    _, _, fp, tn = _confusion(y, s, w, threshold)
    return _ratio(tn, tn + fp)


def _balanced_accuracy(y, s, w, threshold=0.5):
    return (_recall(y, s, w, threshold) + _specificity(y, s, w, threshold)) / 2


def _mcc(y, s, w, threshold=0.5):
    tp, fn, fp, tn = _confusion(y, s, w, threshold)
    den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return float((tp * tn - fp * fn) / den) if den else 0.0


def _f2(y, s, w, threshold=0.5):
    tp, fn, fp, _ = _confusion(y, s, w, threshold)
    return _ratio(5 * tp, 5 * tp + 4 * fn + fp)


def _auc(y, s, w, threshold=None):
    """Weighted ROC-AUC (ties count 1/2, as sklearn's roc_auc_score), in O(n) per call."""
    uniq, inv = np.unique(s, return_inverse=True)
    pos_w = np.bincount(inv, weights=w * (y == 0), minlength=len(uniq))
    neg_w = np.bincount(inv, weights=w * (y != 0), minlength=len(uniq))
    total_pos, total_neg = pos_w.sum(), neg_w.sum()
    if not total_pos or not total_neg:
        return float("nan")
    neg_below = np.cumsum(neg_w) - neg_w
    return float((pos_w * (neg_below + 0.5 * neg_w)).sum() / (total_pos * total_neg))


METRICS = dict(mcc=_mcc, accuracy=_accuracy, recall=_recall, specificity=_specificity,
               balanced_accuracy=_balanced_accuracy, f2=_f2, auc=_auc)


# ----------------------------------------------------------------------------- tests
def corrected_resampled_ttest(diffs, n_train, n_test):
    """Nadeau & Bengio (2003): t = mean(d) / sqrt((1/k + n_test/n_train) * var(d)), df = k - 1. Two-sided p."""
    d = np.asarray(diffs, float)
    k, var = len(d), d.var(ddof=1)
    if not var > 0:
        raise ValueError("the per-fold differences are all equal: the t statistic is undefined")
    t = d.mean() / np.sqrt((1 / k + n_test / n_train) * var)
    return float(t), float(2 * sps.t.sf(abs(t), df=k - 1))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, in the input order (NaN stays NaN)."""
    p = np.asarray(pvals, float)
    out = np.full(len(p), np.nan)
    ok = np.flatnonzero(~np.isnan(p))
    order = ok[np.argsort(p[ok])]
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(order) - rank) * p[i])
        out[i] = min(1.0, running)
    return out


def _patient_weights(groups, n_boot, rng):
    """Cell weights for each bootstrap resample: how often the cell's patient was drawn."""
    _, inv = np.unique(np.asarray(groups), return_inverse=True)
    n_groups = inv.max() + 1
    for _ in range(n_boot):
        yield np.bincount(rng.integers(0, n_groups, n_groups), minlength=n_groups)[inv].astype(float)


def _interval(est, boot):
    boot = np.asarray(boot, float)
    boot = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return dict(est=est, lo=float(lo), hi=float(hi), boot=boot)


def _p_from_boot(est, boot, n_boot):
    """Two-sided percentile-bootstrap p for 'difference = 0' (floored at 1 / n_boot when every resample agrees)."""
    if est == 0 and not np.any(boot):
        return 1.0
    p = 2 * min(np.mean(boot <= 0), np.mean(boot >= 0))
    return float(min(1.0, max(p, 1 / n_boot)))


def cluster_bootstrap(y, s, groups, metric, n_boot=10_000, seed=0):
    """Metric with a 95 % patient-bootstrap interval."""
    f, ones = METRICS[metric], np.ones(len(y))
    boot = [f(y, s, w) for w in _patient_weights(groups, n_boot, np.random.default_rng(seed))]
    return _interval(f(y, s, ones), boot)


def paired_cluster_bootstrap(y, s_a, s_b, groups, metric, n_boot=10_000, seed=0):
    """metric(B) - metric(A) on the same cells; both arms see the same patient resample."""
    f, ones = METRICS[metric], np.ones(len(y))
    est = f(y, s_b, ones) - f(y, s_a, ones)
    boot = np.array([f(y, s_b, w) - f(y, s_a, w)
                     for w in _patient_weights(groups, n_boot, np.random.default_rng(seed))])
    out = _interval(est, boot)
    out["p"] = _p_from_boot(est, out["boot"], n_boot)
    return out


def unpaired_cluster_bootstrap(y_a, s_a, g_a, y_b, s_b, g_b, metric, n_boot=10_000, seed=0):
    """metric(B) - metric(A) on different cells; each arm resamples its own patients."""
    f = METRICS[metric]
    est = f(y_b, s_b, np.ones(len(y_b))) - f(y_a, s_a, np.ones(len(y_a)))
    rng = np.random.default_rng(seed)
    boot = np.array([f(y_b, s_b, wb) - f(y_a, s_a, wa)
                     for wa, wb in zip(_patient_weights(g_a, n_boot, rng), _patient_weights(g_b, n_boot, rng))])
    out = _interval(est, boot)
    out["p"] = _p_from_boot(est, out["boot"], n_boot)
    return out


# ----------------------------------------------------------------------------- calibration and threshold
def expected_calibration_error(y, s, bins=15):
    """Binary ECE on P(parasitized): sum over equal-width bins of (share of cells) x |observed - predicted|."""
    y, s = np.asarray(y), np.asarray(s, float)
    idx = np.minimum((s * bins).astype(int), bins - 1)
    ece = 0.0
    for b in np.unique(idx):
        m = idx == b
        ece += m.mean() * abs(np.mean(y[m] == 0) - s[m].mean())
    return float(ece)


def threshold_from_cv(y, s):
    """The decision threshold with the highest F2 on out-of-fold predictions (ties: the highest threshold)."""
    ones = np.ones(len(y))
    candidates = np.unique(s)[::-1]
    scores = [_f2(y, s, ones, t) for t in candidates]
    return float(candidates[int(np.nanargmax(scores))])


# ----------------------------------------------------------------------------- experiments
def load_experiment(results_root, exp, n_folds=mx.PAPER["KFOLD"]):
    """Saved predictions of one experiment, or None when not all of its folds are there yet."""
    folds_dir = os.path.join(results_root, mx.EXPERIMENTS[exp]["folder"], "folds")
    if len(glob.glob(os.path.join(folds_dir, "fold_*", "fold_*.json"))) < n_folds:
        return None
    agg = mx.aggregate(folds_dir, n_folds)
    if agg["experiment"] != exp:
        raise ValueError(f"{folds_dir} holds {agg['experiment']} folds, not {exp}")
    recs = agg["records"]
    out = dict(exp=exp, agg=agg, val_true=np.asarray(agg["val_true"]), val_files=np.asarray(agg["val_files"]),
               n_train=float(np.mean([r.get("n_train", len(r["npz"]["test_files"]) * (n_folds - 1)) for r in recs])),
               n_test=float(np.mean([len(r["npz"]["test_files"]) for r in recs])),
               fold_files=[np.asarray(r["npz"]["test_files"]) for r in recs],
               fold_true=[np.asarray(r["npz"]["test_true"]) for r in recs])
    out["val_groups"] = np.array([mx.patient_id(f) for f in out["val_files"]])
    for proto, (test_key, val_key) in PROTOCOLS.items():
        out[f"fold_scores_{proto}"] = [np.asarray(r["npz"][test_key])[:, 0] for r in recs]
        out[f"ens_{proto}"] = np.asarray(agg["ens_probs"][proto])[:, 0]
    return out


def fold_values(e, metric, protocol=PRIMARY):
    ones = lambda n: np.ones(n)
    return np.array([METRICS[metric](t, s, ones(len(t)))
                     for t, s in zip(e["fold_true"], e[f"fold_scores_{protocol}"])])


def compare(a, b, paired, n_boot=10_000, seed=0, protocol=PRIMARY):
    """B - A on the folds and on the 10-model ensemble's hold-out predictions."""
    if paired:
        if not np.array_equal(a["val_files"], b["val_files"]):
            raise ValueError(f"{a['exp']} and {b['exp']} have different hold-out sets: they can't be paired")
        if not all(np.array_equal(fa, fb) for fa, fb in zip(a["fold_files"], b["fold_files"])):
            raise ValueError(f"{a['exp']} and {b['exp']} have different folds: they can't be paired")
    out = dict(contrast=f"{b['exp']} vs {a['exp']}", new=b["exp"], reference=a["exp"], paired=paired,
               protocol=protocol, fold={}, ensemble={})
    for m in METRIC_ORDER:
        va, vb = fold_values(a, m, protocol), fold_values(b, m, protocol)
        row = dict(ref_mean=float(va.mean()), ref_sd=float(va.std(ddof=1)), new_mean=float(vb.mean()),
                   new_sd=float(vb.std(ddof=1)), diff=float(vb.mean() - va.mean()))
        k = len(va)
        if paired:
            d = vb - va
            se = np.sqrt((1 / k + b["n_test"] / b["n_train"]) * d.var(ddof=1))
            half = sps.t.ppf(0.975, k - 1) * se
            try:
                row["t"], row["p"] = corrected_resampled_ttest(d, b["n_train"], b["n_test"])
                row["test"] = "corrected resampled t-test (paired folds)"
            except ValueError:
                row["t"], row["p"], row["test"] = float("nan"), float("nan"), "undefined (identical differences)"
        else:  # different splits: folds are not paired; Welch's t on the fold scores, descriptive only
            row["t"], row["p"] = map(float, sps.ttest_ind(vb, va, equal_var=False))
            row["test"] = "Welch t-test on fold scores (unpaired, descriptive)"
            se2a, se2b = va.var(ddof=1) / k, vb.var(ddof=1) / k
            dof = (se2a + se2b) ** 2 / (se2a ** 2 / (k - 1) + se2b ** 2 / (k - 1)) if se2a + se2b else k - 1
            half = sps.t.ppf(0.975, dof) * np.sqrt(se2a + se2b)
        row.update(est=row["diff"], lo=float(row["diff"] - half), hi=float(row["diff"] + half))
        out["fold"][m] = row

        sa, sb = a[f"ens_{protocol}"], b[f"ens_{protocol}"]
        if paired:
            r = paired_cluster_bootstrap(a["val_true"], sa, sb, a["val_groups"], m, n_boot, seed)
        else:
            r = unpaired_cluster_bootstrap(a["val_true"], sa, a["val_groups"], b["val_true"], sb, b["val_groups"],
                                           m, n_boot, seed)
        ones_a, ones_b = np.ones(len(sa)), np.ones(len(sb))
        out["ensemble"][m] = dict(ref=METRICS[m](a["val_true"], sa, ones_a), new=METRICS[m](b["val_true"], sb, ones_b),
                                  est=r["est"], lo=r["lo"], hi=r["hi"], p=r["p"],
                                  test="paired patient bootstrap" if paired else "unpaired patient bootstrap")
    return out


def experiment_row(e, n_boot=10_000, seed=0, protocol=PRIMARY):
    """One line of the experiments table: fold mean +- SD, ensemble with patient-bootstrap CIs, extras."""
    s, y = e[f"ens_{protocol}"], e["val_true"]
    row = dict(experiment=e["exp"], split=mx.EXPERIMENTS[e["exp"]]["split"],
               preprocess=mx.EXPERIMENTS[e["exp"]]["preprocess"], protocol=protocol,
               holdout_cells=len(y), holdout_patients=len(set(e["val_groups"])))
    for m in METRIC_ORDER:
        v = fold_values(e, m, protocol)
        row[f"fold_{m}_mean"], row[f"fold_{m}_sd"] = float(v.mean()), float(v.std(ddof=1))
        r = cluster_bootstrap(y, s, e["val_groups"], m, n_boot, seed)
        row[f"ens_{m}"], row[f"ens_{m}_lo"], row[f"ens_{m}_hi"] = r["est"], r["lo"], r["hi"]
    tp, fn, fp, tn = _confusion(y, s, np.ones(len(y)))
    row.update(missed=int(fn), flagged=int(fp), ece=expected_calibration_error(y, s))
    # Threshold chosen for recall (F2) on the pooled out-of-fold CV predictions, then applied to the hold-out set
    t = threshold_from_cv(np.concatenate(e["fold_true"]), np.concatenate(e[f"fold_scores_{protocol}"]))
    ones = np.ones(len(y))
    row.update(cv_threshold=t, recall_at_cv_threshold=_recall(y, s, ones, t),
               specificity_at_cv_threshold=_specificity(y, s, ones, t))
    return row


def per_patient(e, protocol=PRIMARY):
    s, y, g = e[f"ens_{protocol}"], e["val_true"], e["val_groups"]
    rows = []
    for p in sorted(set(g), key=lambda x: int(x[1:])):
        m = g == p
        pos, pred = y[m] == 0, s[m] >= 0.5
        rows.append(dict(experiment=e["exp"], patient=p, cells=int(m.sum()), parasitized=int(pos.sum()),
                         accuracy=float(np.mean(pos == pred)), missed=int((pos & ~pred).sum()),
                         flagged=int((~pos & pred).sum())))
    return rows


# ----------------------------------------------------------------------------- report
def _pct(x):
    return f"{100 * x:.2f}"


def _verdicts(contrasts):
    by = {c["contrast"]: c for c in contrasts}
    lines = []
    c = by.get("A1 vs A0")
    if c:
        e, f = c["ensemble"], c["fold"]
        drop = e["mcc"]["hi"] < 0 and e["mcc"]["p_holm"] < 0.05
        lines.append(f"- **H1 (leakage)**: ensemble MCC {_pct(e['mcc']['ref'])} → {_pct(e['mcc']['new'])} "
                     f"(Δ {100 * e['mcc']['est']:+.2f} pp, 95 % CI {100 * e['mcc']['lo']:+.2f} to {100 * e['mcc']['hi']:+.2f}, "
                     f"Holm p = {e['mcc']['p_holm']:.3g}); accuracy Δ {100 * e['accuracy']['est']:+.2f} pp. "
                     f"Fold SD of accuracy {100 * f['accuracy']['ref_sd']:.2f} → {100 * f['accuracy']['new_sd']:.2f} pp. "
                     + ("**Supported**: the patient-level split scores lower." if drop else
                        "**Not supported** at the 5 % level: the patient-level split does not score clearly lower."))
    c = by.get("A2 vs A1")
    if c:
        e, f = c["ensemble"], c["fold"]
        gain, sd = f["mcc"]["diff"], f["mcc"]["ref_sd"]
        prereg_reject = gain < sd
        test_support = e["mcc"]["lo"] > 0 and e["mcc"]["p_holm"] < 0.05
        hurts = e["mcc"]["hi"] < 0 and e["mcc"]["p_holm"] < 0.05
        lines.append(f"- **H2 (YUV on unseen patients)**: mean fold MCC gain {100 * gain:+.2f} pp vs A1's fold SD "
                     f"{100 * sd:.2f} pp → pre-registered rule: **{'reject' if prereg_reject else 'keep'} H2**. "
                     f"Ensemble MCC Δ {100 * e['mcc']['est']:+.2f} pp (95 % CI {100 * e['mcc']['lo']:+.2f} to "
                     f"{100 * e['mcc']['hi']:+.2f}, Holm p = {e['mcc']['p_holm']:.3g}); recall Δ "
                     f"{100 * e['recall']['est']:+.2f} pp; fold t-test p = {f['mcc']['p']:.3g}. "
                     + ("Both the rule and the test support H2." if (test_support and not prereg_reject) else
                        "YUV makes the model significantly worse on unseen patients: H2 is rejected." if hurts else
                        "H2 is not supported." if (prereg_reject and not test_support) else
                        "The rule and the test disagree: report H2 as inconclusive."))
    c = by.get("A3 vs A0")
    if c:
        e, f = c["ensemble"], c["fold"]
        small = abs(f["mcc"]["diff"]) < f["mcc"]["ref_sd"]
        lines.append(f"- **Control (YUV, shared patients)**: mean fold MCC Δ {100 * f['mcc']['diff']:+.2f} pp "
                     f"(A0 fold SD {100 * f['mcc']['ref_sd']:.2f} pp); ensemble MCC Δ {100 * e['mcc']['est']:+.2f} pp "
                     f"(95 % CI {100 * e['mcc']['lo']:+.2f} to {100 * e['mcc']['hi']:+.2f}). "
                     + ("As expected, YUV changes little when patients are shared." if small else
                        "YUV changes the score even when patients are shared: an H2 gain would not be specific to "
                        "unseen patients."))
    return lines


def render(rows, contrasts, missing, protocol, n_boot):
    md = ["# Ablation A0–A3: results and hypothesis tests", "",
          f"Primary protocol: **{protocol}** evaluation. Intervals: 95 % patient-cluster bootstrap "
          f"({n_boot:,} resamples). Metrics in %; MCC × 100.", ""]
    if missing:
        md += [f"Not run yet: {', '.join(missing)}.", ""]
    md += ["## Experiments", "",
           "| ID | Split | Preproc. | Hold-out cells / patients | Fold MCC (mean ± SD) | Fold acc. (mean ± SD) | "
           "Ens. acc. [95 % CI] | Ens. MCC [95 % CI] | Ens. recall [95 % CI] | Ens. AUC | Missed / flagged | ECE |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ci = lambda m: f"{_pct(r[f'ens_{m}'])} [{_pct(r[f'ens_{m}_lo'])}, {_pct(r[f'ens_{m}_hi'])}]"
        md.append(f"| {r['experiment']} | {r['split']} | {r['preprocess']} | {r['holdout_cells']:,} / "
                  f"{r['holdout_patients']} | {_pct(r['fold_mcc_mean'])} ± {_pct(r['fold_mcc_sd'])} | "
                  f"{_pct(r['fold_accuracy_mean'])} ± {_pct(r['fold_accuracy_sd'])} | {ci('accuracy')} | {ci('mcc')} | "
                  f"{ci('recall')} | {_pct(r['ens_auc'])} | {r['missed']} / {r['flagged']} | {r['ece']:.3f} |")
    if contrasts:
        md += ["", "## Contrasts (difference = new − reference, in pp)", "",
               "Fold level: Nadeau–Bengio corrected resampled t-test when the folds are paired; Welch t-test "
               "(descriptive) when they are not. Ensemble level: patient bootstrap. Holm correction over the three "
               "contrasts, per metric.", ""]
        for c in contrasts:
            md += [f"### {c['contrast']}: {c['question']}", "",
                   "| Metric | Fold Δ | Fold p | Fold p (Holm) | Ensemble Δ [95 % CI] | Ensemble p | Ensemble p (Holm) |",
                   "|---|---|---|---|---|---|---|"]
            for m in METRIC_ORDER:
                f, e = c["fold"][m], c["ensemble"][m]
                md.append(f"| {m} | {100 * f['diff']:+.2f} | {f['p']:.3g} | {f['p_holm']:.3g} | "
                          f"{100 * e['est']:+.2f} [{100 * e['lo']:+.2f}, {100 * e['hi']:+.2f}] | {e['p']:.3g} | "
                          f"{e['p_holm']:.3g} |")
            md.append("")
        md += ["## Verdicts", ""] + _verdicts(contrasts)
    md += ["", "## Extras on the same predictions", "",
           "| ID | CV-chosen threshold (max F2) | Hold-out recall at it | Specificity at it |", "|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['experiment']} | {r['cv_threshold']:.3f} | {_pct(r['recall_at_cv_threshold'])} | "
                  f"{_pct(r['specificity_at_cv_threshold'])} |")
    return "\n".join(md) + "\n"


def analyse(results_root=os.path.join(REPO, "results"), out_dir=None, n_boot=10_000, seed=0, protocol=PRIMARY):
    """Load every finished experiment, run the contrasts that are possible, write the report files."""
    out_dir = out_dir or os.path.join(results_root, "ablation")
    found = {exp: load_experiment(results_root, exp) for exp in ["A0", "A1", "A2", "A3"]}
    missing = [exp for exp, e in found.items() if e is None]
    found = {exp: e for exp, e in found.items() if e is not None}
    rows = [experiment_row(e, n_boot, seed, protocol) for e in found.values()]
    contrasts = []
    for new, ref, paired, question in CONTRASTS:
        if new in found and ref in found:
            c = compare(found[ref], found[new], paired, n_boot, seed, protocol)
            c["question"] = question
            contrasts.append(c)
    for level in ["fold", "ensemble"]:
        for m in METRIC_ORDER:
            adj = holm([c[level][m]["p"] for c in contrasts])
            for c, p in zip(contrasts, adj):
                c[level][m]["p_holm"] = float(p)

    os.makedirs(out_dir, exist_ok=True)
    text = render(rows, contrasts, missing, protocol, n_boot)
    with open(os.path.join(out_dir, "ablation_summary.md"), "w") as fh:
        fh.write(text)
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, "ablation_experiments.csv"), index=False)
    long = [dict(contrast=c["contrast"], level=level, metric=m, **{k: v for k, v in c[level][m].items()})
            for c in contrasts for level in ["fold", "ensemble"] for m in METRIC_ORDER]
    pd.DataFrame(long).to_csv(os.path.join(out_dir, "ablation_summary.csv"), index=False)
    pd.DataFrame([r for e in found.values() for r in per_patient(e, protocol)]).to_csv(
        os.path.join(out_dir, "ablation_per_patient.csv"), index=False)
    with open(os.path.join(out_dir, "ablation_summary.json"), "w") as fh:
        json.dump(dict(protocol=protocol, n_boot=n_boot, seed=seed, missing=missing, experiments=rows,
                       contrasts=[{k: v for k, v in c.items()} for c in contrasts]), fh, indent=1, default=float)
    return dict(experiments=rows, contrasts=contrasts, missing=missing, text=text, found=found)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=os.path.join(REPO, "results"))
    ap.add_argument("--out", default=None, help="default: <results>/ablation")
    ap.add_argument("--n-boot", type=int, default=10_000)
    ap.add_argument("--protocol", choices=sorted(PROTOCOLS), default=PRIMARY)
    args = ap.parse_args()
    print(analyse(args.results, args.out, args.n_boot, protocol=args.protocol)["text"])


if __name__ == "__main__":
    main()
