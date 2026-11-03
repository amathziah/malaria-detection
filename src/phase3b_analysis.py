"""Phase 3b: the exploratory analyses fixed in docs/phase3b_addendum.md, on saved predictions only (no training).

Usage:
    python src/phase3b_analysis.py                  # reads results/<A0-A3>, writes results/phase3b/
    python src/phase3b_analysis.py --n-boot 2000    # quicker, coarser intervals

E1  equivalence (two one-sided tests, +-1 pp MCC) and minimum detectable effects; design effect of patient clustering
E2  leakage on identical cells: A1 - A0 on A0's hold-out cells of A1's 40 held-out patients (ensembles) and on the
    out-of-fold cells both cross-validations share (single models)
E3  patient-level diagnosis: a count rule chosen on the 160 CV patients, applied once to the 40 held-out patients
E4  error audit: false alarms by patient status, error clustering, candidate label errors, verdict robustness,
    blinded gallery, reliability diagram

Conventions, as in ablation_stats: y 0 = parasitized, 1 = uninfected; s = P(parasitized); parasitized if s >= t.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats as sps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ablation_stats as st  # noqa: E402
import marques2022_exact as mx  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARGIN = 0.01                                  # +-1 pp MCC (addendum E1)
LEAK_METRICS = ("mcc", "accuracy", "recall", "specificity")
RULE_T = (None, 0.5, 0.8, 0.95, 0.99)          # None = A1's CV-chosen F2 threshold
RULE_TAU = (1, 2, 3, 4, 5, 6, 8, 10, 12, 15)
MIN_SPEC = 0.95
DILUTION_M = (1, 2, 3, 5)
DISCLOSURE = ("NIH kept about 68 uninfected crops per patient but curated the parasitized cells, so per-patient "
              "parasite counts are not natural parasitaemia; only 12 held-out patients are healthy; there are no "
              "parasite densities. This is exploratory aggregation on curated crops, not a diagnostic accuracy study.")


# ----------------------------------------------------------------------------- E1: equivalence, detectable effects
def tost_from_boot(boot, margin=MARGIN):
    """Two one-sided tests on bootstrap replicates of a difference: equivalent if the 90 % interval is inside +-margin."""
    boot = np.asarray(boot, float)
    boot = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot, [5, 95])
    p = max(np.mean(boot <= -margin), np.mean(boot >= margin))
    return dict(lo90=float(lo), hi90=float(hi), equivalent=bool(-margin < lo and hi < margin),
                p_tost=float(max(p, 1 / len(boot))), smallest_margin=float(max(abs(lo), abs(hi))))


def tost_from_t(diff, se, df, margin=MARGIN):
    """Two one-sided t-tests for a mean difference with standard error se."""
    q = sps.t.ppf(0.95, df)
    lo, hi = diff - q * se, diff + q * se
    p_lower = sps.t.sf((diff + margin) / se, df)     # H0: difference <= -margin
    p_upper = sps.t.cdf((diff - margin) / se, df)    # H0: difference >= +margin
    return dict(lo90=float(lo), hi90=float(hi), equivalent=bool(-margin < lo and hi < margin),
                p_tost=float(max(p_lower, p_upper)), smallest_margin=float(max(abs(lo), abs(hi))))


def mde(se, df=None, alpha=0.05, power=0.80):
    """Smallest true difference detected with the given power by a two-sided test at alpha, given its standard error."""
    dist = sps.norm if df is None else sps.t(df)
    return float((dist.ppf(1 - alpha / 2) + dist.ppf(power)) * se)


def design_effect(y, s, groups, metric, n_boot=10_000, seed=0):
    """Variance of the metric when whole patients are resampled, over its variance when single cells are."""
    f, rng, n = st.METRICS[metric], np.random.default_rng(seed), len(y)
    patient = np.array([f(y, s, w) for w in st._patient_weights(groups, n_boot, rng)])
    cell = np.array([f(y, s, np.bincount(rng.integers(0, n, n), minlength=n).astype(float)) for _ in range(n_boot)])
    vp, vc = np.nanvar(patient, ddof=1), np.nanvar(cell, ddof=1)
    return dict(var_patient=float(vp), var_cell=float(vc), deff=float(vp / vc))


def _fold_paired(ref, new, metric, protocol):
    d = st.fold_values(new, metric, protocol) - st.fold_values(ref, metric, protocol)
    k = len(d)
    return float(d.mean()), float(np.sqrt((1 / k + new["n_test"] / new["n_train"]) * d.var(ddof=1))), k - 1


def equivalence(found, n_boot=10_000, seed=0, protocol="clean"):
    """E1: TOST and MDE for the YUV contrasts, MDE for the H1 contrast, design effect of A1's hold-out."""
    rows = []
    for new, ref in [("A2", "A1"), ("A3", "A0")]:
        a, b = found[ref], found[new]
        for m in ["mcc", "accuracy"]:
            r = st.paired_cluster_bootstrap(a["val_true"], a[f"ens_{protocol}"], b[f"ens_{protocol}"], a["val_groups"],
                                            m, n_boot, seed)
            se = float(np.nanstd(r["boot"], ddof=1))
            rows.append(dict(contrast=f"{new} vs {ref}", level="ensemble", metric=m, est=r["est"], se=se,
                             mde=mde(se), **tost_from_boot(r["boot"])))
            diff, se, df = _fold_paired(a, b, m, protocol)
            rows.append(dict(contrast=f"{new} vs {ref}", level="fold", metric=m, est=diff, se=se, mde=mde(se, df),
                             **tost_from_t(diff, se, df)))
    a, b = found["A0"], found["A1"]
    for m in ["mcc", "accuracy"]:
        r = st.unpaired_cluster_bootstrap(a["val_true"], a[f"ens_{protocol}"], a["val_groups"], b["val_true"],
                                          b[f"ens_{protocol}"], b["val_groups"], m, n_boot, seed)
        se = float(np.nanstd(r["boot"], ddof=1))
        rows.append(dict(contrast="A1 vs A0", level="ensemble (different cells)", metric=m, est=r["est"], se=se,
                         mde=mde(se)))
        va, vb = st.fold_values(a, m, protocol), st.fold_values(b, m, protocol)
        t = st.corrected_unpaired_ttest(va, vb, a["n_test"] / a["n_train"], b["n_test"] / b["n_train"])
        rows.append(dict(contrast="A1 vs A0", level="fold (corrected, unpaired)", metric=m, est=float(vb.mean() - va.mean()),
                         se=t["se"], mde=mde(t["se"], t["df"])))
    e1 = found["A1"]
    deff = {m: design_effect(e1["val_true"], e1[f"ens_{protocol}"], e1["val_groups"], m, n_boot, seed)
            for m in ["mcc", "accuracy"]}
    return dict(margin=MARGIN, rows=rows, design_effect=deff)


# ----------------------------------------------------------------------------- E2: leakage on identical cells
def align(files_a, files_b):
    """Indices of the files both arrays hold, in the first array's order."""
    pos_b = {f: i for i, f in enumerate(files_b)}
    ia = [i for i, f in enumerate(files_a) if f in pos_b]
    return np.array(ia, int), np.array([pos_b[files_a[i]] for i in ia], int)


def oof(e, protocol="clean"):
    """Out-of-fold predictions of one experiment: files, labels, P(parasitized), fold index."""
    folds = np.concatenate([np.full(len(f), k) for k, f in enumerate(e["fold_files"])])
    return (np.concatenate(e["fold_files"]), np.concatenate(e["fold_true"]),
            np.concatenate(e[f"fold_scores_{protocol}"]), folds)


def leakage_reading(r, margin=MARGIN):
    """The addendum's three readings of an A1 - A0 difference on identical cells."""
    if r["hi"] < 0:
        return "leakage detected"
    if -margin < r["lo90"] and r["hi90"] < margin:
        return "equivalent within ±1 pp"
    return "inconclusive"


def _paired_block(y, s_ref, s_new, groups, n_boot, seed):
    out = dict(n_cells=int(len(y)), n_patients=int(len(set(groups))))
    if len(y) == 0:
        out["reading"] = "no shared cells"
        return out
    for m in LEAK_METRICS:
        r = st.paired_cluster_bootstrap(y, s_ref, s_new, groups, m, n_boot, seed)
        boot = r.pop("boot")
        se = float(np.nanstd(boot, ddof=1)) if len(boot) > 1 else 0.0
        out[m] = dict(est=float(r["est"]), lo=float(r["lo"]), hi=float(r["hi"]), p=float(r["p"]), se=se, mde=mde(se),
                      **tost_from_boot(boot))
    out["reading"] = leakage_reading(out["mcc"])
    return out


def same_cell_leakage(e0, e1, n_boot=10_000, seed=0, protocol="clean"):
    """E2: metric(A1) - metric(A0) on identical cells; H1 predicts a negative difference."""
    i0, i1 = align(e0["val_files"], e1["val_files"])
    if not np.array_equal(e0["val_true"][i0], e1["val_true"][i1]):
        raise ValueError("the shared hold-out cells carry different labels in the two experiments")
    hold = _paired_block(e0["val_true"][i0], e0[f"ens_{protocol}"][i0], e1[f"ens_{protocol}"][i1],
                         e0["val_groups"][i0], n_boot, seed)
    f0, y0, s0, _ = oof(e0, protocol)
    f1, y1, s1, _ = oof(e1, protocol)
    j0, j1 = align(f0, f1)
    if not np.array_equal(y0[j0], y1[j1]):
        raise ValueError("the shared out-of-fold cells carry different labels in the two experiments")
    groups = np.array([mx.patient_id(f) for f in f0[j0]])
    return dict(holdout=hold, oof=_paired_block(y0[j0], s0[j0], s1[j1], groups, n_boot, seed))


# ----------------------------------------------------------------------------- E3: patient-level diagnosis
def _per_patient_counts(groups, mask):
    keys, inv = np.unique(np.asarray(groups), return_inverse=True)
    return keys, np.bincount(inv, weights=np.asarray(mask, float), minlength=len(keys))


def patient_truth(groups, y):
    """Infected if the patient has at least one cell labelled parasitized."""
    keys, n_par = _per_patient_counts(groups, np.asarray(y) == 0)
    return {k: bool(n > 0) for k, n in zip(keys, n_par)}


def patient_calls(groups, s, t, tau):
    """Positive if at least tau of the patient's cells have P(parasitized) >= t (labels are not used)."""
    keys, n_pos = _per_patient_counts(groups, np.asarray(s) >= t)
    return {k: bool(n >= tau) for k, n in zip(keys, n_pos)}


def sens_spec(truth, calls):
    infected = [p for p, v in truth.items() if v]
    healthy = [p for p, v in truth.items() if not v]
    tp, tn = sum(calls[p] for p in infected), sum(not calls[p] for p in healthy)
    sens = tp / len(infected) if infected else float("nan")
    spec = tn / len(healthy) if healthy else float("nan")
    return dict(sens=sens, spec=spec, j=sens + spec - 1, tp=int(tp), tn=int(tn), n_infected=len(infected),
                n_healthy=len(healthy))


def select_rule(groups, y, s, ts, taus, min_spec=MIN_SPEC):
    """Highest Youden J among rules with specificity >= min_spec (else among all); ties: higher specificity,
    then smaller tau, then smaller t."""
    truth = patient_truth(groups, y)
    grid = [dict(t=float(t), tau=int(tau), **sens_spec(truth, patient_calls(groups, s, t, tau)))
            for t in ts for tau in taus]
    ok = [r for r in grid if r["spec"] >= min_spec]
    best = max(ok or grid, key=lambda r: (round(r["j"], 12), round(r["spec"], 12), -r["tau"], -r["t"]))
    return dict(best, meets_min_spec=bool(ok), grid=grid)


def nested_rule_selection(groups, y, s, folds, ts, taus, min_spec=MIN_SPEC):
    """Leave one fold out: choose the rule on the other folds' patients, score it on the left-out fold's, pool."""
    groups, y, s, folds = map(np.asarray, (groups, y, s, folds))
    truth, calls, rules = {}, {}, []
    for k in np.unique(folds):
        train, test = folds != k, folds == k
        r = select_rule(groups[train], y[train], s[train], ts, taus, min_spec)
        rules.append(dict(fold=int(k), t=r["t"], tau=r["tau"]))
        truth.update(patient_truth(groups[test], y[test]))
        calls.update(patient_calls(groups[test], s[test], r["t"], r["tau"]))
    return dict(sens_spec(truth, calls), rules=rules)


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial confidence interval for k successes out of n."""
    lo = 0.0 if k == 0 else sps.beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else sps.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def dilution_sensitivity(groups, y, s, t, tau, m, n_draws=1000, seed=0):
    """Mean sensitivity when each infected patient keeps only m random parasitized cells (all uninfected ones stay)."""
    groups, y, s = map(np.asarray, (groups, y, s))
    rng = np.random.default_rng(seed)
    infected = [p for p, v in patient_truth(groups, y).items() if v]
    hits = 0
    for p in infected:
        mine = groups == p
        par = s[mine][y[mine] == 0]
        extra = int(np.sum(s[mine][y[mine] == 1] >= t))  # false alarms on the patient's uninfected cells still count
        keep = min(m, len(par))
        for _ in range(n_draws):
            hits += int(np.sum(rng.choice(par, size=keep, replace=False) >= t) + extra >= tau)
    return hits / (len(infected) * n_draws)


def patient_level(e1, n_draws=1000, seed=0, protocol="clean"):
    """E3 on A1: rule chosen on the out-of-fold predictions of the CV patients, applied once to the hold-out set."""
    files, y, s, folds = oof(e1, protocol)
    groups = np.array([mx.patient_id(f) for f in files])
    ts = [st.threshold_from_cv(y, s) if t is None else t for t in RULE_T]
    chosen = select_rule(groups, y, s, ts, RULE_TAU)
    nested = nested_rule_selection(groups, y, s, folds, ts, RULE_TAU)
    t, tau = chosen["t"], chosen["tau"]

    vy, vs, vg = e1["val_true"], e1[f"ens_{protocol}"], e1["val_groups"]
    truth, calls = patient_truth(vg, vy), patient_calls(vg, vs, t, tau)
    hold = sens_spec(truth, calls)
    hold["sens_ci"] = clopper_pearson(hold["tp"], hold["n_infected"])
    hold["spec_ci"] = clopper_pearson(hold["tn"], hold["n_healthy"])
    hold["misclassified"] = sorted([p for p in truth if truth[p] != calls[p]], key=lambda p: int(p[1:]))
    per_model = []
    for r in e1["agg"]["records"]:
        if not np.array_equal(r["npz"]["val_files"], e1["val_files"]):
            raise ValueError("a fold model scored a different hold-out set")
        x = sens_spec(truth, patient_calls(vg, np.asarray(r["npz"][f"val_{protocol}"])[:, 0], t, tau))
        per_model.append(dict(fold=int(r["fold"]), sens=x["sens"], spec=x["spec"]))
    keys, n_pos = _per_patient_counts(vg, vs >= t)
    _, n_cells = _per_patient_counts(vg, np.ones(len(vg)))
    _, n_par = _per_patient_counts(vg, vy == 0)
    table = [dict(patient=k, infected=truth[k], cells=int(c), parasitized=int(p), cells_at_or_above_t=int(n),
                  call=calls[k]) for k, c, p, n in zip(keys, n_cells, n_par, n_pos)]
    dilution = {int(m): dilution_sensitivity(vg, vy, vs, t, tau, m, n_draws, seed) for m in DILUTION_M}
    return dict(ts=ts, taus=list(RULE_TAU), min_spec=MIN_SPEC,
                selected={k: chosen[k] for k in ["t", "tau", "sens", "spec", "j", "meets_min_spec", "n_infected",
                                                 "n_healthy"]},
                cv_grid=chosen["grid"], nested=nested, holdout=hold, holdout_per_model=per_model,
                holdout_patients=table, dilution=dilution, disclosure=DISCLOSURE)


# ----------------------------------------------------------------------------- E4: error audit
def _boot_rate(groups, flags, n_boot, rng):
    flags = np.asarray(flags, float)
    return np.array([np.sum(w * flags) / np.sum(w) for w in st._patient_weights(groups, n_boot, rng)])


def false_alarm_by_status(groups, y, s, threshold=0.5, n_boot=10_000, seed=0):
    """Uninfected-labelled cells flagged as parasitized, in infected vs healthy patients' smears (patient bootstrap)."""
    groups, y, s = map(np.asarray, (groups, y, s))
    truth = patient_truth(groups, y)
    infected = np.array([truth[g] for g in groups], bool)
    flag, rng, out, boots = s >= threshold, np.random.default_rng(seed), {}, {}
    for name, status in [("infected", infected), ("healthy", ~infected)]:
        m = (y == 1) & status
        out[name] = dict(flagged=int(flag[m].sum()), cells=int(m.sum()), patients=int(len(set(groups[m]))),
                         rate=float(flag[m].mean()) if m.any() else float("nan"))
        if m.any():
            boots[name] = _boot_rate(groups[m], flag[m], n_boot, rng)
            out[name]["lo"], out[name]["hi"] = map(float, np.percentile(boots[name], [2.5, 97.5]))
    if len(boots) == 2:
        d = boots["infected"] - boots["healthy"]
        lo, hi = np.percentile(d, [2.5, 97.5])
        out["difference"] = dict(est=out["infected"]["rate"] - out["healthy"]["rate"], lo=float(lo), hi=float(hi))
    return out


def error_dispersion_test(groups, y, s, threshold=0.5, n_perm=10_000, seed=0):
    """Do errors pile up on some patients? Chi-square dispersion of per-patient error counts against each label
    class's error rate; permutation null shuffles the error flags among cells of the same label."""
    groups, y, s = map(np.asarray, (groups, y, s))
    err = (s >= threshold) != (y == 0)
    keys, inv = np.unique(groups, return_inverse=True)
    rate = np.zeros(len(y))
    for cls in (0, 1):
        if np.any(y == cls):
            rate[y == cls] = err[y == cls].mean()
    expected = np.bincount(inv, weights=rate, minlength=len(keys))
    ok = expected > 0

    def stat(e):
        observed = np.bincount(inv, weights=e.astype(float), minlength=len(keys))
        return float(np.sum((observed[ok] - expected[ok]) ** 2 / expected[ok]))

    observed_stat, rng, perm, count = stat(err), np.random.default_rng(seed), err.copy(), 0
    for _ in range(n_perm):
        for cls in (0, 1):
            m = y == cls
            perm[m] = rng.permutation(err[m])
        count += stat(perm) >= observed_stat - 1e-9
    return dict(stat=observed_stat, p=(1 + count) / (1 + n_perm), n_errors=int(err.sum()), n_patients=len(keys))


def confident_learning_candidates(y, s):
    """Confident learning (Northcutt et al. 2021), two classes: a cell is a candidate label error when the other
    class's probability reaches that class's mean probability among the cells labelled with it (and wins the argmax)."""
    y, s = np.asarray(y), np.asarray(s, float)
    p_par, p_un = s, 1 - s
    t_par, t_un = p_par[y == 0].mean(), p_un[y == 1].mean()
    cand = np.where(y == 0, (p_un >= t_un) & ((p_par < t_par) | (p_un > p_par)),
                    (p_par >= t_par) & ((p_un < t_un) | (p_par > p_un)))
    return cand, dict(parasitized=float(t_par), uninfected=float(t_un))


def _candidate_table(files, y, s, mask):
    files, y, s = np.asarray(files), np.asarray(y), np.asarray(s, float)
    given = np.where(y == 0, s, 1 - s)
    t = pd.DataFrame(dict(file=files[mask], patient=[mx.patient_id(f) for f in files[mask]],
                          label=np.where(y[mask] == 0, "parasitized", "uninfected"), p_parasitized=s[mask].round(4),
                          p_given_label=given[mask].round(4)))
    return t.sort_values("p_given_label").reset_index(drop=True)


def verdict_robustness(found, n_boot=10_000, seed=0, protocol="clean"):
    """E4d: the YUV contrasts again, without the hold-out cells either arm flags as a candidate label error."""
    rows = []
    for new, ref in [("A2", "A1"), ("A3", "A0")]:
        a, b = found[ref], found[new]
        y, g = a["val_true"], a["val_groups"]
        flagged = (confident_learning_candidates(y, a[f"ens_{protocol}"])[0]
                   | confident_learning_candidates(y, b[f"ens_{protocol}"])[0])
        for name, keep in [("all cells", np.ones(len(y), bool)), ("without flagged cells", ~flagged)]:
            r = st.paired_cluster_bootstrap(y[keep], a[f"ens_{protocol}"][keep], b[f"ens_{protocol}"][keep], g[keep],
                                            "mcc", n_boot, seed)
            rows.append(dict(contrast=f"{new} vs {ref}", cells=name, n_cells=int(keep.sum()),
                             n_flagged=int(flagged.sum()), est=float(r["est"]), lo=float(r["lo"]), hi=float(r["hi"]),
                             p=float(r["p"])))
    return rows


def blinded_gallery(files, y, s, image_dir, out_png, out_key, threshold=0.5, seed=0, tile=72):
    """Every misclassified cell plus as many correctly classified cells of the same labels, shuffled and numbered.
    The picture shows numbers only; the key (label, model call) is a separate file for after the triage."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    files, y, s = map(np.asarray, (files, y, s))
    err = np.where(s >= threshold, 0, 1) != y
    rng = np.random.default_rng(seed)
    controls = []
    for cls in (0, 1):
        pool = np.flatnonzero(~err & (y == cls))
        controls += list(rng.choice(pool, size=min(int(np.sum(err & (y == cls))), len(pool)), replace=False))
    idx = np.concatenate([np.flatnonzero(err), np.array(controls, int)])
    idx = idx[rng.permutation(len(idx))]
    key = pd.DataFrame(dict(id=np.arange(1, len(idx) + 1), file=files[idx],
                            label=np.where(y[idx] == 0, "parasitized", "uninfected"), p_parasitized=s[idx].round(4),
                            model_call=np.where(s[idx] >= threshold, "parasitized", "uninfected"), error=err[idx]))
    key.to_csv(out_key, index=False)
    cols = int(np.ceil(np.sqrt(len(idx) * 1.4)))
    rows = int(np.ceil(len(idx) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 0.85, rows * 0.95), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, i, f, label in zip(axes.flat, key["id"], key["file"], y[idx]):
        img = Image.open(os.path.join(image_dir, "Parasitized" if label == 0 else "Uninfected", f)).convert("RGB")
        ax.imshow(img.resize((tile, tile)))
        ax.set_title(str(i), fontsize=6, pad=1.5, color="#52514e")
    fig.subplots_adjust(wspace=0.08, hspace=0.25)
    fig.savefig(out_png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return key


def error_audit(found, n_boot=10_000, n_perm=10_000, seed=0, protocol="clean", image_dir=None, out_dir="."):
    e1 = found["A1"]
    files, y, s, _ = oof(e1, protocol)
    groups = np.array([mx.patient_id(f) for f in files])
    vy, vs, vg, vf = e1["val_true"], e1[f"ens_{protocol}"], e1["val_groups"], e1["val_files"]
    out = dict(false_alarms=dict(holdout=false_alarm_by_status(vg, vy, vs, n_boot=n_boot, seed=seed),
                                 oof=false_alarm_by_status(groups, y, s, n_boot=n_boot, seed=seed)),
               clustering=dict(holdout=error_dispersion_test(vg, vy, vs, n_perm=n_perm, seed=seed),
                               oof=error_dispersion_test(groups, y, s, n_perm=n_perm, seed=seed)))
    cands = {}
    for name, (f, yy, ss) in {"holdout": (vf, vy, vs), "oof": (files, y, s)}.items():
        mask, thr = confident_learning_candidates(yy, ss)
        err = (ss >= 0.5) != (yy == 0)
        cands[name] = dict(n_cells=int(len(yy)), n_errors=int(err.sum()), n_candidates=int(mask.sum()),
                           labelled_parasitized=int((mask & (yy == 0)).sum()),
                           labelled_uninfected=int((mask & (yy == 1)).sum()),
                           candidates_that_are_errors=int((mask & err).sum()), thresholds=thr)
        _candidate_table(f, yy, ss, mask).to_csv(os.path.join(out_dir, f"phase3b_candidates_{name}.csv"), index=False)
    out["candidates"] = cands
    out["robustness"] = verdict_robustness(found, n_boot, seed, protocol)
    out["ece"] = st.expected_calibration_error(vy, vs)
    if image_dir:
        key = blinded_gallery(vf, vy, vs, image_dir, os.path.join(out_dir, "phase3b_error_gallery.png"),
                              os.path.join(out_dir, "phase3b_error_gallery_KEY.csv"), seed=seed)
        pd.DataFrame(dict(id=key["id"], parasite_visible="", category="", notes="")).to_csv(
            os.path.join(out_dir, "phase3b_error_gallery_triage_sheet.csv"), index=False)
        out["gallery"] = dict(tiles=int(len(key)), errors=int(key["error"].sum()))
    return out


# ----------------------------------------------------------------------------- figures
def _style():
    import matplotlib
    matplotlib.use("Agg")
    import ablation_figures as figs
    figs.style()
    return figs


def _value_column(ax, texts, fontsize, color):
    """Row i's numbers in a column right of the plot, clear of the grid, the band and the intervals."""
    import matplotlib.transforms as mtransforms
    tr = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for i, text in enumerate(texts):
        ax.text(1.02, i, text, transform=tr, ha="left", va="center", fontsize=fontsize, color=color)


def leakage_figure(abl, e2, path):
    """A1 - A0 in MCC, four ways: the pre-registered hold-out comparison, the CV folds, and the two same-cell tests.

    Drawn at the size the paper prints it, with the numbers in their own column right of the plot."""
    import matplotlib.pyplot as plt
    figs = _style()
    c = {x["contrast"]: x for x in abl["contrasts"]}["A1 vs A0"]
    rows = [("Hold-out sets, different cells\n(pre-registered H1 test)", c["ensemble"]["mcc"], figs.MUTED),
            ("Cross-validation folds\n(corrected t)", c["fold"]["mcc"], figs.MUTED)]
    for key, label in [("holdout", "Same cells: hold-out ensembles\n({n:,} cells, {p} patients)"),
                       ("oof", "Same cells: out-of-fold models\n({n:,} cells, {p} patients)")]:
        if e2[key]["n_cells"]:
            rows.append((label.format(n=e2[key]["n_cells"], p=e2[key]["n_patients"]), e2[key]["mcc"],
                         figs.SPLIT_COLOR["patient"]))
    fig, ax = plt.subplots(figsize=(5.0, 0.55 * len(rows) + 1.0))
    ax.tick_params(labelsize=8)
    ax.axvspan(-100 * MARGIN, 100 * MARGIN, color="#e8f3f4", zorder=0, lw=0)
    ax.axvline(0, color=figs.AXIS, lw=1)
    texts = []
    for i, (label, r, color) in enumerate(rows[::-1]):
        est, lo, hi = 100 * r.get("est", r.get("diff")), 100 * r["lo"], 100 * r["hi"]
        ax.plot([lo, hi], [i, i], color=color, lw=1.8, solid_capstyle="round")
        ax.plot(est, i, "o", color=color, ms=6, mec="white", mew=1.2)
        texts.append(f"{figs._pp(est)}  [{figs._pp(lo)}, {figs._pp(hi)}]")
    _value_column(ax, texts, 8, figs.SECONDARY)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=8)
    ax.set_ylim(-0.5, len(rows) - 0.5)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("A1 − A0, MCC (pp): negative = unseen patients score lower (95 % CI); band = ±1 pp", fontsize=8)
    ax.set_title("Patient leakage, measured four ways", fontsize=10)
    lo_all = min(100 * r[1]["lo"] for r in rows)
    hi_all = max(100 * r[1]["hi"] for r in rows)
    ax.set_xlim(min(lo_all, -1.5) - 0.4, max(hi_all, 1.5) + 0.4)
    return figs._save(fig, path)


def equivalence_figure(e1, path):
    """90 % intervals of the YUV contrasts against the +-1 pp equivalence margin."""
    import matplotlib.pyplot as plt
    figs = _style()
    rows = [r for r in e1["rows"] if r["metric"] == "mcc" and "lo90" in r]
    names = {"A2 vs A1": "H2 · A2 − A1, unseen patients", "A3 vs A0": "Control · A3 − A0, patients shared"}
    fig, ax = plt.subplots(figsize=(5.0, 0.5 * len(rows) + 1.0))
    ax.tick_params(labelsize=8)
    ax.axvspan(-100 * MARGIN, 100 * MARGIN, color="#e8f3f4", zorder=0, lw=0)
    ax.axvline(0, color=figs.AXIS, lw=1)
    texts = []
    for i, r in enumerate(rows[::-1]):
        color = figs.SPLIT_COLOR["patient" if r["contrast"] == "A2 vs A1" else "image"]
        ax.plot([100 * r["lo90"], 100 * r["hi90"]], [i, i], color=color, lw=1.8, solid_capstyle="round")
        ax.plot(100 * r["est"], i, "D", color=color, ms=5.5, mec="white", mew=1.2)
        verdict = "equivalent" if r["equivalent"] else "not established"
        texts.append(f"{figs._pp(100 * r['est'])}  [{figs._pp(100 * r['lo90'])}, {figs._pp(100 * r['hi90'])}]  "
                     f"{verdict}")
    _value_column(ax, texts, 8, figs.SECONDARY)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{names[r['contrast']]}\n{r['level']}" for r in rows[::-1]], fontsize=8)
    ax.set_ylim(-0.5, len(rows) - 0.5)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("MCC difference (pp), 90 % CI; shaded = ±1 pp equivalence margin", fontsize=8)
    ax.set_title("How large could the YUV effect be? 90 % intervals vs a ±1 pp margin", fontsize=10)
    ax.set_xlim(-2.2, 2.2)
    return figs._save(fig, path)


def patient_level_figure(e3, path):
    """Cells at or above the chosen threshold, per held-out patient, against the chosen count tau."""
    import matplotlib.pyplot as plt
    figs = _style()
    t = pd.DataFrame(e3["holdout_patients"]).sort_values(["infected", "cells_at_or_above_t"], ascending=[True, True])
    tau, thr = e3["selected"]["tau"], e3["selected"]["t"]
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    colors = [figs.SPLIT_COLOR["patient"] if inf else figs.SPLIT_COLOR["image"] for inf in t["infected"]]
    x, n = np.arange(len(t)), t["cells_at_or_above_t"].to_numpy()
    ax.bar(x, n, color=colors, width=0.7)
    ax.scatter(x[n == 0], np.zeros(int((n == 0).sum())), s=14, color=np.array(colors)[n == 0], zorder=3, clip_on=False)
    ax.set_yscale("symlog", linthresh=1)  # linear below 1, so a patient with no flagged cell sits at 0
    ax.set_ylim(0, max(2 * n.max(), 4))
    ticks = [v for v in [0, 1, 3, 10, 30, 100, 300, 1000] if v <= max(2 * n.max(), 4)]
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels([str(v) for v in ticks])
    ax.axhline(tau - 0.5, color=figs.INK, lw=1, ls="--")
    ax.annotate(f"positive from {tau} cell{'s' if tau > 1 else ''} up", (-0.4, tau - 0.5), xytext=(0, 5),
                textcoords="offset points", ha="left", fontsize=9, color=figs.INK)
    ax.set_xticks(x)
    ax.set_xticklabels(t["patient"], rotation=90, fontsize=6.5)
    ax.set_ylabel(f"cells with P(parasitized) ≥ {thr:.2f}")
    n_h, n_i = int((~t["infected"]).sum()), int(t["infected"].sum())
    dot = lambda c, lab: Line2D([], [], marker="s", linestyle="none", markersize=8, color=c, label=lab)
    ax.legend(handles=[dot(figs.SPLIT_COLOR["image"], f"healthy ({n_h})"), dot(figs.SPLIT_COLOR["patient"],
                                                                               f"infected ({n_i})")],
              loc="upper left", bbox_to_anchor=(0, 0.92), fontsize=9)
    ax.set_title("The 40 held-out patients under the rule chosen on the other 160")
    return figs._save(fig, path)


def reliability_figure(y, s, path, bins=10):
    import matplotlib.pyplot as plt
    figs = _style()
    y, s = np.asarray(y), np.asarray(s, float)
    idx = np.minimum((s * bins).astype(int), bins - 1)
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.plot([0, 1], [0, 1], color=figs.AXIS, lw=1)
    xs, ys, ns = [], [], []
    for b in np.unique(idx):
        m = idx == b
        xs.append(s[m].mean())
        ys.append(np.mean(y[m] == 0))
        ns.append(m.sum())
    ax.plot(xs, ys, "-o", color=figs.SPLIT_COLOR["patient"], ms=5, mec="white")
    ax.set_xlabel("predicted P(parasitized)")
    ax.set_ylabel("observed share parasitized")
    ax.set_title(f"A1 hold-out ensemble · ECE {st.expected_calibration_error(y, s):.3f}")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return figs._save(fig, path)


# ----------------------------------------------------------------------------- report
def _pp(x):
    return f"{100 * x:+.2f}"


def render(res, abl):
    e1, e2, e3, e4 = res["E1"], res["E2"], res["E3"], res["E4"]
    md = ["# Phase 3b: exploratory analyses (docs/phase3b_addendum.md)", "",
          "Saved predictions only; clean protocol; 95 % intervals resample whole patients unless stated. Differences "
          "are new − reference in percentage points (pp); MCC × 100. Exploratory: fixed in the addendum before running, "
          "after the A1–A3 results were known.", ""]
    md += ["## E1 · Equivalence (±1 pp MCC) and minimum detectable effects", "",
           "| Contrast | Level | Metric | Δ | 90 % CI | Equivalent at ±1 pp? | TOST p | Smallest margin passed | MDE (80 % power) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in e1["rows"]:
        if "lo90" in r:
            md.append(f"| {r['contrast']} | {r['level']} | {r['metric']} | {_pp(r['est'])} | [{_pp(r['lo90'])}, "
                      f"{_pp(r['hi90'])}] | {'yes' if r['equivalent'] else 'no'} | {r['p_tost']:.3g} | "
                      f"{100 * r['smallest_margin']:.2f} | {100 * r['mde']:.2f} |")
        else:
            md.append(f"| {r['contrast']} | {r['level']} | {r['metric']} | {_pp(r['est'])} | – | – | – | – | "
                      f"{100 * r['mde']:.2f} |")
    d = e1["design_effect"]
    md += ["", f"Design effect of patient clustering on A1's hold-out set: MCC {d['mcc']['deff']:.1f}, accuracy "
               f"{d['accuracy']['deff']:.1f} (variance under the patient bootstrap ÷ under a cell bootstrap).", ""]
    md += ["## E2 · Leakage on identical cells (A1 − A0; H1 predicts negative)", "",
           "| Cells | n cells / patients | Metric | Δ [95 % CI] | p | 90 % CI | MDE | Reading |", "|---|---|---|---|---|---|---|---|"]
    for key, name in [("holdout", "A0 hold-out cells of A1's held-out patients (ensembles)"),
                      ("oof", "out-of-fold cells shared by both CVs (single models)")]:
        b = e2[key]
        if not b["n_cells"]:
            md.append(f"| {name} | 0 | – | – | – | – | – | no shared cells |")
            continue
        for m in LEAK_METRICS:
            r = b[m]
            md.append(f"| {name} | {b['n_cells']:,} / {b['n_patients']} | {m} | {_pp(r['est'])} [{_pp(r['lo'])}, "
                      f"{_pp(r['hi'])}] | {r['p']:.3g} | [{_pp(r['lo90'])}, {_pp(r['hi90'])}] | {100 * r['mde']:.2f} | "
                      f"{b['reading'] if m == 'mcc' else ''} |")
    c = {x["contrast"]: x for x in abl["contrasts"]}.get("A1 vs A0")
    if c:
        md += ["", f"For comparison: the pre-registered hold-out comparison (different cells) gives MCC "
                   f"{_pp(c['ensemble']['mcc']['est'])} [{_pp(c['ensemble']['mcc']['lo'])}, {_pp(c['ensemble']['mcc']['hi'])}]; "
                   f"the cross-validation folds give {_pp(c['fold']['mcc']['diff'])} [{_pp(c['fold']['mcc']['lo'])}, "
                   f"{_pp(c['fold']['mcc']['hi'])}]."]
    s, h, n = e3["selected"], e3["holdout"], e3["nested"]
    md += ["", "## E3 · Patient-level diagnosis (A1)", "",
           f"**Disclosure.** {e3['disclosure']}", "",
           f"Rule chosen on the {s['n_infected'] + s['n_healthy']} CV patients' out-of-fold predictions "
           f"({s['n_infected']} infected, {s['n_healthy']} healthy): **positive if at least {s['tau']} cell"
           f"{'s' if s['tau'] > 1 else ''} have P(parasitized) ≥ {s['t']:.3f}** (CV sensitivity {100 * s['sens']:.1f} %, "
           f"specificity {100 * s['spec']:.1f} %{'' if s['meets_min_spec'] else '; no rule reached 95 % specificity'}).", "",
           "| Evaluation | Sensitivity | Specificity |", "|---|---|---|",
           f"| CV patients, rule chosen on them (optimistic) | {100 * s['sens']:.1f} % | {100 * s['spec']:.1f} % |",
           f"| CV patients, nested (rule chosen on the other 9 folds) | {n['tp']}/{n['n_infected']} = {100 * n['sens']:.1f} % | "
           f"{n['tn']}/{n['n_healthy']} = {100 * n['spec']:.1f} % |",
           f"| **40 held-out patients, A1 ensemble, applied once** | **{h['tp']}/{h['n_infected']} = {100 * h['sens']:.1f} %** "
           f"[{100 * h['sens_ci'][0]:.1f}, {100 * h['sens_ci'][1]:.1f}] | **{h['tn']}/{h['n_healthy']} = "
           f"{100 * h['spec']:.1f} %** [{100 * h['spec_ci'][0]:.1f}, {100 * h['spec_ci'][1]:.1f}] |"]
    pm = e3["holdout_per_model"]
    md += ["", f"Exact 95 % CIs (Clopper–Pearson). Misclassified held-out patients: "
               f"{', '.join(h['misclassified']) if h['misclassified'] else 'none'}. With each A1 fold model alone: "
               f"sensitivity {100 * min(r['sens'] for r in pm):.1f}–{100 * max(r['sens'] for r in pm):.1f} %, specificity "
               f"{100 * min(r['spec'] for r in pm):.1f}–{100 * max(r['spec'] for r in pm):.1f} %. Nested rules per fold: "
               + ", ".join(f"(t {r['t']:.2f}, τ {r['tau']})" for r in n["rules"]) + ".", "",
           "Dilution stress test (each infected held-out patient keeps only m parasitized cells): " +
           ", ".join(f"m = {m}: sensitivity {100 * v:.1f} %" for m, v in e3["dilution"].items()) + "."]
    fa, cl, ca = e4["false_alarms"], e4["clustering"], e4["candidates"]
    md += ["", "## E4 · Error audit (A1)", "", "| Data | False alarms in infected patients' smears | In healthy patients' smears | Difference [95 % CI] |",
           "|---|---|---|---|"]
    for key in ["holdout", "oof"]:
        r = fa[key]
        if "difference" in r:
            md.append(f"| {key} | {r['infected']['flagged']}/{r['infected']['cells']} = {100 * r['infected']['rate']:.2f} % "
                      f"({r['infected']['patients']} patients) | {r['healthy']['flagged']}/{r['healthy']['cells']} = "
                      f"{100 * r['healthy']['rate']:.2f} % ({r['healthy']['patients']} patients) | "
                      f"{_pp(r['difference']['est'])} [{_pp(r['difference']['lo'])}, {_pp(r['difference']['hi'])}] |")
    md += ["", "Error clustering by patient (χ² dispersion, permutation within label): " +
           "; ".join(f"{k}: {v['n_errors']} errors over {v['n_patients']} patients, χ² = {v['stat']:.1f}, p = {v['p']:.3g}"
                     for k, v in cl.items()) + ".", "",
           "Candidate label errors (confident learning; candidates, not confirmed errors): " +
           "; ".join(f"{k}: {v['n_candidates']} of {v['n_cells']:,} cells ({v['labelled_parasitized']} labelled parasitized, "
                     f"{v['labelled_uninfected']} labelled uninfected; {v['candidates_that_are_errors']} of them among the "
                     f"model's {v['n_errors']} errors)" for k, v in ca.items()) + ".", "",
           "| Contrast | Cells | n | MCC Δ [95 % CI] |", "|---|---|---|---|"]
    for r in e4["robustness"]:
        md.append(f"| {r['contrast']} | {r['cells']} | {r['n_cells']:,} | {_pp(r['est'])} [{_pp(r['lo'])}, {_pp(r['hi'])}] |")
    md += ["", f"A1 hold-out ensemble ECE: {e4['ece']:.3f} (reliability diagram: phase3b_reliability.png)."]
    if "gallery" in e4:
        md += ["", f"Blinded gallery: {e4['gallery']['tiles']} numbered cells ({e4['gallery']['errors']} model errors, the "
                   "rest correct cells with the same labels), phase3b_error_gallery.png. Triage it before opening "
                   "phase3b_error_gallery_KEY.csv."]
    return "\n".join(md) + "\n"


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def analyse(results_root=os.path.join(REPO, "results"), out_dir=None, n_boot=10_000, n_perm=10_000, n_draws=1000,
            seed=0, image_dir=os.path.join(REPO, "outputs", "data", "cell_images"), protocol="clean"):
    """Run E1-E4 on the four experiments' saved predictions and write results/phase3b/."""
    out_dir = out_dir or os.path.join(results_root, "phase3b")
    os.makedirs(out_dir, exist_ok=True)
    found = {exp: st.load_experiment(results_root, exp) for exp in ["A0", "A1", "A2", "A3"]}
    missing = [exp for exp, e in found.items() if e is None]
    if missing:
        raise FileNotFoundError(f"Phase 3b needs all four experiments; missing: {', '.join(missing)}")
    abl_path = os.path.join(results_root, "ablation", "ablation_summary.json")
    if os.path.exists(abl_path):
        abl = json.load(open(abl_path))
    else:  # e.g. a fresh results tree: the H1 rows of the leakage figure need the ablation contrasts
        import tempfile
        abl = st.analyse(results_root, out_dir=tempfile.mkdtemp(), n_boot=200, seed=seed, protocol=protocol)
    res = dict(E1=equivalence(found, n_boot, seed, protocol),
               E2=same_cell_leakage(found["A0"], found["A1"], n_boot, seed, protocol),
               E3=patient_level(found["A1"], n_draws, seed, protocol),
               E4=error_audit(found, n_boot, n_perm, seed, protocol, image_dir if image_dir and os.path.isdir(image_dir)
                              else None, out_dir))
    text = render(res, abl)
    with open(os.path.join(out_dir, "phase3b_summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(out_dir, "phase3b_summary.json"), "w") as fh:
        json.dump(_jsonable(dict(n_boot=n_boot, n_perm=n_perm, n_draws=n_draws, seed=seed, protocol=protocol, **res)),
                  fh, indent=1)
    pd.DataFrame(res["E1"]["rows"]).to_csv(os.path.join(out_dir, "phase3b_equivalence.csv"), index=False)
    pd.DataFrame(res["E3"]["cv_grid"]).to_csv(os.path.join(out_dir, "phase3b_patient_rules_cv.csv"), index=False)
    pd.DataFrame(res["E3"]["holdout_patients"]).to_csv(os.path.join(out_dir, "phase3b_patient_level_holdout.csv"),
                                                       index=False)
    leakage_figure(abl, res["E2"], os.path.join(out_dir, "phase3b_leakage.png"))
    equivalence_figure(res["E1"], os.path.join(out_dir, "phase3b_equivalence.png"))
    patient_level_figure(res["E3"], os.path.join(out_dir, "phase3b_patient_level.png"))
    reliability_figure(found["A1"]["val_true"], found["A1"][f"ens_{protocol}"],
                       os.path.join(out_dir, "phase3b_reliability.png"))
    return dict(res, text=text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=os.path.join(REPO, "results"))
    ap.add_argument("--out", default=None, help="default: <results>/phase3b")
    ap.add_argument("--n-boot", type=int, default=10_000)
    ap.add_argument("--n-perm", type=int, default=10_000)
    ap.add_argument("--images", default=os.path.join(REPO, "outputs", "data", "cell_images"))
    args = ap.parse_args()
    print(analyse(args.results, args.out, args.n_boot, args.n_perm, image_dir=args.images)["text"])


if __name__ == "__main__":
    main()
