#!/usr/bin/env python3
"""Figures drawn only for the final deck, from saved predictions; no statistic is recomputed or written.

- results/phase3b/deck_errors_per_patient.png: the A1 ensemble's errors on the 40 held-out patients, one bar per
  patient, sorted, with the few patients that hold half of all errors highlighted (deck slide 14, failure analysis).

    python src/deck_figures.py
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ablation_figures as figs  # noqa: E402
import ablation_stats as st  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAL = figs.SPLIT_COLOR["patient"]
TEAL_SOFT = "#9fcbd4"


def patient_errors(e, threshold=0.5):
    """Per held-out patient: (patient, cells, errors), sorted by errors, most first. y = 0 is parasitized."""
    y, s, groups = e["val_true"], e["ens_clean"], e["val_groups"]
    wrong = (s >= threshold) != (y == 0)
    rows = [(g, int((groups == g).sum()), int(wrong[groups == g].sum())) for g in np.unique(groups)]
    return sorted(rows, key=lambda r: (-r[2], -r[1], r[0]))


def errors_per_patient(e, path):
    rows = patient_errors(e)
    errs = np.array([r[2] for r in rows])
    total, n = int(errs.sum()), len(rows)
    k = int(np.searchsorted(np.cumsum(errs), total / 2) + 1)  # fewest patients holding at least half the errors
    top, zeros = int(errs[:k].sum()), int((errs == 0).sum())
    figs.style()
    fig, ax = plt.subplots(figsize=(9.0, 4.3))
    x = np.arange(n)
    ax.bar(x[:k], errs[:k], width=0.78, color=TEAL, zorder=3)
    ax.bar(x[k:], errs[k:], width=0.78, color=TEAL_SOFT, zorder=3)
    ax.scatter(x[errs == 0], np.zeros(zeros) + 0.25, s=10, color=figs.MUTED, zorder=3)
    ax.set_ylim(0, errs.max() + 3.8)
    ax.set_yticks(range(0, int(errs.max()) + 4, 5))
    ax.set_xlim(-0.8, n - 0.2)
    for i in range(k):  # patient IDs under the highlighted bars
        ax.text(i, -0.35, rows[i][0], rotation=90, ha="center", va="top", fontsize=8.5, color=figs.SECONDARY)
    y_br = errs[0] + 1.3
    ax.plot([-0.4, -0.4, k - 0.6, k - 0.6], [y_br - 0.35, y_br, y_br, y_br - 0.35], color=figs.INK, lw=1.1)
    ax.text(-0.4, y_br + 0.45, f"{k} patients hold {top} of the {total} errors ({100 * top / total:.0f} %)",
            fontsize=11.5, fontweight="bold", color=figs.INK, va="bottom")
    z0 = n - zeros
    y_z = 2.2
    ax.plot([z0 - 0.4, z0 - 0.4, n - 0.6, n - 0.6], [y_z - 0.35, y_z, y_z, y_z - 0.35], color=figs.INK, lw=1.1)
    ax.text((z0 + n - 1) / 2, y_z + 0.45, f"{zeros} patients: every cell correct", ha="center", va="bottom",
            fontsize=11, fontweight="bold", color=figs.INK)
    ax.set_xticks([])
    ax.set_ylabel("errors (misses + false alarms)")
    ax.set_xlabel(f"the {n} unseen patients, sorted by errors", labelpad=40 if k else 8)
    ax.set_title(f"The {total} errors on {len(e['val_true']):,} cells of {n} unseen patients, by patient (A1 ensemble)")
    fig.savefig(path)
    plt.close(fig)
    return path


def main(results=os.path.join(REPO, "results")):
    e = st.load_experiment(results, "A1")
    out = errors_per_patient(e, os.path.join(results, "phase3b", "deck_errors_per_patient.png"))
    print("Saved", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
