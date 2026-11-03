#!/usr/bin/env python3
"""Draw docs/figures/architecture.png: the reproduced EfficientNet-B0 backbone and the paper's classifier head.

The figure is drawn at the size the IEEE paper prints it (the full text width), so its type sizes are the printed
sizes. The parameter counts are the ones tests/test_marques2022_exact.py checks against the paper's Table 2.

    python docs/figures/make_architecture.py
"""
import glob
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "architecture.png")

INK, SECONDARY = "#1f2a44", "#52514e"
TEAL, TEAL_TINT, ORANGE, ORANGE_TINT, ORANGE_DEEP = "#00809a", "#e2f0f3", "#c4531f", "#fbebe3", "#f6d2b8"
GREY_TINT = "#f3f5f7"

W, H = 7.1, 3.48       # inches: the paper's text width, so 1 pt here is 1 pt on paper
MARGIN = 0.05

# (lines, resolution in pixels) for the backbone, left to right; box height grows with the resolution
BACKBONE = [
    (["Input", "224×224×3", "uint8, ÷255"], 224),
    (["Stem", "3×3 conv, s2", "32 ch", "112×112"], 112),
    (["Stage 1", "MBConv1 3×3", "1 block", "16 ch, 112²"], 112),
    (["Stage 2", "MBConv6 3×3", "2 blocks", "24 ch, 56²"], 56),
    (["Stage 3", "MBConv6 5×5", "2 blocks", "40 ch, 28²"], 28),
    (["Stage 4", "MBConv6 3×3", "3 blocks", "80 ch, 14²"], 14),
    (["Stage 5", "MBConv6 5×5", "3 blocks", "112 ch, 14²"], 14),
    (["Stage 6", "MBConv6 5×5", "4 blocks", "192 ch, 7²"], 7),
    (["Stage 7", "MBConv6 3×3", "1 block", "320 ch, 7²"], 7),
    (["Top", "1×1 conv", "1280 ch", "7×7"], 7),
]
BOX_HEIGHT = {224: 1.30, 112: 1.14, 56: 0.98, 28: 0.86, 14: 0.76, 7: 0.70}
HEAD = [(["Global average", "pool → 1280"], ORANGE_TINT), (["Dense 128", "ReLU"], ORANGE_TINT),
        (["Dropout 0.3"], "white"), (["Dense 64", "ReLU"], ORANGE_TINT), (["Dropout 0.3"], "white"),
        (["Dense 32", "ReLU"], ORANGE_TINT), (["Dropout 0.3"], "white"), (["Dense 2", "softmax"], ORANGE_DEEP)]


def _font():
    """Lato, as in the other figures, when outputs/fonts holds it; DejaVu Sans otherwise."""
    for f in glob.glob(os.path.join(REPO, "outputs", "fonts", "*.ttf")):
        font_manager.fontManager.addfont(f)
    return "Lato" if any(f.name == "Lato" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"


def _box(ax, x, y_mid, w, h, lines, fill, size=6.6):
    """A rounded box centred on y_mid, its first line bold."""
    ax.add_patch(FancyBboxPatch((x, y_mid - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.045",
                                facecolor=fill, edgecolor=INK, linewidth=0.7))
    step = 0.118 * size / 6.6
    top = y_mid + step * (len(lines) - 1) / 2
    for i, line in enumerate(lines):
        ax.text(x + w / 2, top - i * step, line, ha="center", va="center", fontsize=size, color=INK,
                fontweight="bold" if i == 0 and len(lines) > 1 else "normal")


def _arrow(ax, x0, y0, x1, y1):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.7, mutation_scale=6,
                                                       shrinkA=0, shrinkB=0))


def draw(path=OUT):
    plt.rcParams["font.family"] = _font()
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    # 1 · backbone
    ax.text(MARGIN, H - 0.06, "1 · EfficientNet-B0 backbone (noisy-student weights): 4,049,564 parameters",
            ha="left", va="top", fontsize=8.5, fontweight="bold", color=TEAL)
    bw = 0.62
    gap = (W - 2 * MARGIN - len(BACKBONE) * bw) / (len(BACKBONE) - 1)
    y1 = H - 0.33 - max(BOX_HEIGHT.values()) / 2
    xs = [MARGIN + i * (bw + gap) for i in range(len(BACKBONE))]
    for i, (x, (lines, res)) in enumerate(zip(xs, BACKBONE)):
        _box(ax, x, y1, bw, BOX_HEIGHT[res], lines, GREY_TINT if i == 0 else TEAL_TINT, size=6.3)
        if i:
            _arrow(ax, x - gap, y1, x, y1)

    # 2 · head
    band_bottom = y1 - max(BOX_HEIGHT.values()) / 2
    title2_top = band_bottom - 0.10
    ax.text(MARGIN, title2_top, "2 · Paper's classifier head: 174,370 parameters", ha="left", va="top",
            fontsize=8.5, fontweight="bold", color=ORANGE)
    bus = title2_top - 0.27
    hw, hh = 0.78, 0.44
    hgap = (W - 2 * MARGIN - len(HEAD) * hw) / (len(HEAD) - 1)
    y2 = bus - 0.13 - hh / 2
    hxs = [MARGIN + i * (hw + hgap) for i in range(len(HEAD))]
    top_x = xs[-1] + bw / 2
    ax.plot([top_x, top_x, hxs[0] + hw / 2], [y1 - BOX_HEIGHT[7] / 2, bus, bus], color=INK, lw=0.7)
    _arrow(ax, hxs[0] + hw / 2, bus, hxs[0] + hw / 2, y2 + hh / 2)
    for i, (x, (lines, fill)) in enumerate(zip(hxs, HEAD)):
        _box(ax, x, y2, hw, hh, lines, fill, size=6.8)
        if i:
            _arrow(ax, x - hgap, y2, x, y2)
    ax.text(W - MARGIN, y2 - hh / 2 - 0.06, "Output: P(parasitized), P(uninfected)", ha="right", va="top",
            fontsize=7, fontweight="bold", color=ORANGE)

    # notes
    notes_top = y2 - hh / 2 - 0.30
    for i, line in enumerate([
            "Box height shows the resolution (224 → 112 → 56 → 28 → 14 → 7 pixels) as the channels grow "
            "3 → 32 → … → 320 → 1280.",
            "16 MBConv blocks in 7 stages · 81 convolution layers (65 normal + 16 depthwise) · 49 batch-norm layers",
            "230 Keras layers in the backbone · 4 dense layers in the head"]):
        ax.text(MARGIN, notes_top - i * 0.125, line, ha="left", va="top", fontsize=6.6, color=SECONDARY)
    ax.text(MARGIN, notes_top - 3 * 0.125 - 0.05,
            "Total: 4,223,934 parameters (4,181,918 trainable + 42,016 non-trainable batch-norm statistics), "
            "exactly the paper's Table 2.", ha="left", va="top", fontsize=7, fontweight="bold", color=INK)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path


if __name__ == "__main__":
    print("Saved", os.path.relpath(draw(), REPO))
