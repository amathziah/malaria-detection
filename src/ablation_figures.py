"""Figures for the ablation, used by the notebook, the report and the slides (one style everywhere).

Colour encodes the split, marker shape encodes the preprocessing, and every mark is also labelled, so no
figure relies on colour alone. The two split colours pass the dataviz palette validator on white
(lightness band, chroma floor, CVD dE 15.3, normal-vision dE 27.6, contrast >= 3:1).
"""
import glob
import os

import numpy as np

import marques2022_exact as mx
from ablation_stats import METRICS, fold_values

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_COLOR = {"image": "#d9622b", "patient": "#00809a"}
PREP_MARKER = {"none": "o", "yuv": "D"}
PREP_NAME = {"none": "original RGB", "yuv": "YUV + hist-eq"}
INK, SECONDARY, MUTED = "#1f2a44", "#52514e", "#898781"
GRID, AXIS, CONTEXT = "#e1e0d9", "#c3c2b7", "#cfcdc6"
METRIC_NAME = dict(mcc="MCC", accuracy="Accuracy", recall="Recall (parasitized)",
                   specificity="Specificity (uninfected)", balanced_accuracy="Balanced accuracy", f2="F2",
                   auc="ROC-AUC")
CONTRAST_LABEL = {"A1 vs A0": "H1 · A1 − A0\npatient vs image split",
                  "A2 vs A1": "H2 · A2 − A1\nYUV on unseen patients",
                  "A3 vs A0": "Control · A3 − A0\nYUV, patients shared"}


def style():
    """The decks' look: Lato if available (outputs/fonts), navy titles, hairline solid grid, no top/right spines."""
    import matplotlib as mpl
    from matplotlib import font_manager
    for f in glob.glob(os.path.join(REPO, "outputs", "fonts", "*.ttf")):
        font_manager.fontManager.addfont(f)
    family = "Lato" if any(f.name == "Lato" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
    mpl.rcParams.update({
        "font.family": family, "font.size": 11, "text.color": INK, "axes.titlecolor": INK,
        "axes.titleweight": "bold", "axes.titlesize": 13, "axes.titlelocation": "left", "axes.titlepad": 12,
        "axes.edgecolor": AXIS, "axes.labelcolor": SECONDARY, "xtick.color": SECONDARY, "ytick.color": SECONDARY,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-", "xtick.major.size": 0,
        "ytick.major.size": 0, "legend.frameon": False, "figure.facecolor": "white", "savefig.facecolor": "white",
        "savefig.dpi": 160, "savefig.bbox": "tight", "axes.axisbelow": True})


def _pp(x):
    """Signed value with a true minus sign, as on the axes: +1.23 / −1.23."""
    return f"{x:+.2f}".replace("-", "\u2212")


def _save(fig, path):
    import matplotlib.pyplot as plt
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def _exp_style(exp):
    e = mx.EXPERIMENTS[exp]
    return SPLIT_COLOR[e["split"]], PREP_MARKER[e["preprocess"]]


def _legend_handles():
    from matplotlib.lines import Line2D
    dot = lambda **kw: Line2D([], [], linestyle="none", markersize=8, markeredgecolor="white", **kw)
    return [dot(marker="o", markerfacecolor=SPLIT_COLOR["image"], label="image split (paper): patients shared"),
            dot(marker="o", markerfacecolor=SPLIT_COLOR["patient"], label="patient split: unseen patients"),
            dot(marker="o", markerfacecolor=MUTED, label="original RGB"),
            dot(marker="D", markerfacecolor=MUTED, label="YUV + hist-eq")]


# ----------------------------------------------------------------------------- fold strip
STRIP_X = {"A0": 0.0, "A3": 1.0, "A1": 2.6, "A2": 3.6}  # grouped by split; pairs side by side


def fold_strip(found, metric="mcc", protocol="clean", path=None):
    """Each fold's test-part score per experiment; grey lines join the same fold across a paired change."""
    import matplotlib.pyplot as plt
    style()
    fig, ax = plt.subplots(figsize=(10, 5.2))
    offsets = np.linspace(-0.2, 0.2, 10)
    vals = {exp: 100 * fold_values(found[exp], metric, protocol) for exp in STRIP_X if exp in found}
    for a, b in [("A0", "A3"), ("A1", "A2")]:
        if a in vals and b in vals:
            for k in range(len(vals[a])):
                ax.plot([STRIP_X[a] + offsets[k], STRIP_X[b] + offsets[k]], [vals[a][k], vals[b][k]],
                        color=CONTEXT, lw=0.8, zorder=1)
    for exp, v in vals.items():
        color, marker = _exp_style(exp)
        x = STRIP_X[exp]
        ax.scatter(x + offsets[:len(v)], v, s=46, marker=marker, facecolor=color, edgecolor="white", linewidth=1.2,
                   zorder=3)
        ax.hlines(v.mean(), x - 0.32, x + 0.32, color=INK, lw=2, zorder=4)
        ax.annotate(f"{v.mean():.2f} ± {v.std(ddof=1):.2f}", (x, v.max()), xytext=(0, 9), textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, color=SECONDARY)
    ax.set_xticks([STRIP_X[e] for e in vals],
                  [f"{e}\n{PREP_NAME[mx.EXPERIMENTS[e]['preprocess']]}" for e in vals])
    ax.set_xlim(-0.6, 4.2)
    lo, hi = min(v.min() for v in vals.values()), max(v.max() for v in vals.values())
    ax.set_ylim(lo - 0.12 * (hi - lo + 1e-9), hi + 0.22 * (hi - lo + 1e-9))
    for xs, text in [((0.0, 1.0), "image split (paper): a patient's cells on both sides"),
                     ((2.6, 3.6), "patient split: test patients never seen in training")]:
        ax.annotate(text, (np.mean(xs), 0), xycoords=("data", "axes fraction"), xytext=(0, -42),
                    textcoords="offset points", ha="center", va="top", fontsize=10, color=SECONDARY)
    ax.set_title(f"{METRIC_NAME[metric]} (%) on each fold's test part · {protocol} evaluation · "
                 "bar = mean, label = mean ± SD", pad=30)
    ax.legend(handles=_legend_handles(), loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4, fontsize=9,
              handletextpad=0.3, columnspacing=1.2)
    return _save(fig, path) if path else fig


# ----------------------------------------------------------------------------- contrasts
def contrast_forest(contrasts, metrics=("mcc", "recall", "specificity", "auc"), level="ensemble", path=None):
    """Difference (pp) with its 95 % patient-bootstrap CI, one panel per metric; filled = Holm p < 0.05."""
    import matplotlib.pyplot as plt
    style()
    rows = [c for name in CONTRAST_LABEL for c in contrasts if c["contrast"] == name]
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.6 * len(metrics) + 1.6, 1.0 + 0.95 * len(rows)),
                             sharey=True)
    axes = np.atleast_1d(axes)
    ys = np.arange(len(rows))[::-1]
    for ax, m in zip(axes, metrics):
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        ax.axvline(0, color=AXIS, lw=1.2, zorder=1)
        for y, c in zip(ys, rows):
            r = c[level][m]
            est, lo, hi = 100 * r["est"], 100 * r["lo"], 100 * r["hi"]
            sig = r.get("p_holm", r["p"]) < 0.05
            ax.plot([lo, hi], [y, y], color=SPLIT_COLOR["patient"], lw=2, solid_capstyle="round", zorder=2)
            ax.scatter([est], [y], s=60, zorder=3, edgecolor=SPLIT_COLOR["patient"], linewidth=2,
                       facecolor=SPLIT_COLOR["patient"] if sig else "white")
            ax.annotate(f"{_pp(est)} [{_pp(lo)}, {_pp(hi)}]", (est, y), xytext=(0, 9), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9, color=SECONDARY)
        span = max(abs(100 * c[level][m][k]) for c in rows for k in ("lo", "hi"))
        ax.set_xlim(-1.7 * span - 0.05, 1.7 * span + 0.05)  # room for the centred labels
        ax.set_title(METRIC_NAME[m], fontsize=11)
        ax.set_xlabel("difference (pp)")
        ax.set_ylim(-0.6, len(rows) - 0.3)
    axes[0].set_yticks(ys, [CONTRAST_LABEL[c["contrast"]] for c in rows])
    fig.suptitle("Ensemble on the hold-out set: new − reference, with 95 % patient-bootstrap CI · "
                 "filled marker = Holm-adjusted p < 0.05" if level == "ensemble" else
                 "Mean over the 10 folds: new − reference, with 95 % CI (corrected t when paired) · "
                 "filled marker = Holm-adjusted p < 0.05",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout()
    return _save(fig, path) if path else fig


# ----------------------------------------------------------------------------- per patient
def per_patient(found, a="A1", b="A2", protocol="clean", path=None):
    """Hold-out accuracy per patient for two experiments on the same patients (a dumbbell per patient)."""
    import matplotlib.pyplot as plt
    style()
    ea, eb = found[a], found[b]
    if not np.array_equal(ea["val_files"], eb["val_files"]):
        raise ValueError(f"{a} and {b} have different hold-out sets")
    y, g = ea["val_true"], ea["val_groups"]
    # worst patient for `a` at the top (matplotlib's y grows upwards, so sort best-first)
    pts = sorted(set(g), key=lambda p: (-np.mean((y[g == p] == 0) == (ea[f"ens_{protocol}"][g == p] >= 0.5)),
                                        -int(p[1:])))
    acc = lambda e, p: 100 * np.mean((y[g == p] == 0) == (e[f"ens_{protocol}"][g == p] >= 0.5))
    fig, ax = plt.subplots(figsize=(9, 0.26 * len(pts) + 1.6))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    for i, p in enumerate(pts):
        va, vb = acc(ea, p), acc(eb, p)
        ax.plot([va, vb], [i, i], color=CONTEXT, lw=1.6, zorder=1)
        for v, exp in [(va, a), (vb, b)]:
            color, marker = _exp_style(exp)
            ax.scatter([v], [i], marker=marker, s=34, facecolor=color if exp == b else "white", edgecolor=color,
                       linewidth=1.5, zorder=3)
    labels = [f"{p} · {int((g == p).sum())} cells, {100 * np.mean(y[g == p] == 0):.0f} % parasitized" for p in pts]
    ax.set_yticks(range(len(pts)), labels, fontsize=8)
    ax.set_xlabel(f"ensemble accuracy on the patient's cells (%) · {protocol} evaluation")
    ax.set_ylim(-0.8, len(pts) - 0.2)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], linestyle="none", marker=PREP_MARKER[mx.EXPERIMENTS[e]["preprocess"]],
                              markersize=7, markerfacecolor=SPLIT_COLOR["patient"] if e == b else "white",
                              markeredgecolor=SPLIT_COLOR["patient"], label=f"{e} · {PREP_NAME[mx.EXPERIMENTS[e]['preprocess']]}")
                       for e in (a, b)], loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=9)
    ax.set_title(f"Each held-out patient: {a} vs {b} (worst for {a} at the top)", pad=28)
    return _save(fig, path) if path else fig


# ----------------------------------------------------------------------------- one experiment
def experiment_panels(agg, exp, path=None, protocol="clean"):
    """Training curves of the 10 folds (grey) with their mean, the ensemble's confusion matrix and ROC."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    style()
    color, _ = _exp_style(exp)
    recs = agg["records"]
    fig, axes = plt.subplots(1, 4, figsize=(20, 4.6), gridspec_kw=dict(width_ratios=[1.2, 1.2, 0.8, 1.0]))
    for ax, key, title, scale in [(axes[0], "val_accuracy", "Accuracy (%) on the fold's test part (augmented)", 100),
                                  (axes[1], "val_loss", "val_loss (drives LR schedule + checkpoint)", 1)]:
        curves = [scale * np.asarray(r["history"][key], float) for r in recs]
        n = min(len(c) for c in curves)
        for c in curves:
            ax.plot(range(1, len(c) + 1), c, color=CONTEXT, lw=1, zorder=1)
        ax.plot(range(1, n + 1), np.mean([c[:n] for c in curves], 0), color=color, lw=2.2, zorder=2,
                label="mean of the 10 folds")
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("epoch")
        ax.legend(fontsize=9, loc="best")
    y, s = np.asarray(agg["val_true"]), np.asarray(agg["ens_probs"][protocol])[:, 0]
    pos, pred = y == 0, s >= 0.5
    cm = np.array([[np.sum(pos & pred), np.sum(pos & ~pred)], [np.sum(~pos & pred), np.sum(~pos & ~pred)]])
    cmap = LinearSegmentedColormap.from_list("seq", ["#f2f8f9", SPLIT_COLOR["patient"]])
    axes[2].imshow(cm, cmap=cmap, vmin=0)
    axes[2].grid(False)
    for (i, j), v in np.ndenumerate(cm):
        axes[2].text(j, i, f"{v:,}", ha="center", va="center", fontsize=14,
                     color="white" if v > cm.max() / 2 else INK)
    axes[2].set_xticks([0, 1], mx.TIPOS)
    axes[2].set_yticks([0, 1], mx.TIPOS)
    axes[2].set_xlabel("predicted")
    axes[2].set_ylabel("true")
    axes[2].set_title(f"Ensemble, hold-out set ({protocol})", fontsize=11)
    from sklearn.metrics import roc_curve
    key = "val_clean" if protocol == "clean" else "val_aug"
    for r in recs:
        fpr, tpr, _ = roc_curve(pos, np.asarray(r["npz"][key])[:, 0])
        axes[3].plot(fpr, tpr, color=CONTEXT, lw=1, zorder=1)
    fpr, tpr, _ = roc_curve(pos, s)
    auc = 100 * METRICS["auc"](y, s, np.ones(len(y)))
    axes[3].plot(fpr, tpr, color=color, lw=2.2, zorder=2, label=f"ensemble · AUC {auc:.2f} %")
    axes[3].plot([], [], color=CONTEXT, lw=1, label="single fold models")
    lim = 0.25  # A0's view: FPR up to 25 %, TPR from 0.7 (lower if the ensemble needs it)
    floor = max(0.0, min(0.7, np.floor(10 * (np.interp(0.01, fpr, tpr) - 0.1)) / 10))
    axes[3].set_xlim(0, lim)
    axes[3].set_ylim(floor, 1.005)
    axes[3].set_xlabel("false-positive rate (zoomed: ≤ 25 %)")
    axes[3].set_ylabel("true-positive rate")
    axes[3].set_title("ROC on the hold-out set", fontsize=11)
    axes[3].legend(fontsize=9, loc="lower right")
    axes[3].grid(axis="x", visible=True)
    e = mx.EXPERIMENTS[exp]
    fig.suptitle(f"{exp} · {e['split']} split · {PREP_NAME[e['preprocess']]} · 10 folds", x=0.01, ha="left",
                 fontsize=14, fontweight="bold", color=INK)
    fig.tight_layout()
    return _save(fig, path) if path else fig
