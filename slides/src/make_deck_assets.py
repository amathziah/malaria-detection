#!/usr/bin/env python3
"""Cut the deck's circular cell images (slides/src/assets/) from the NIH dataset.

Usage: python slides/src/make_deck_assets.py [--data outputs/data/cell_images]
"""
import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "src"))
import marques2022_exact as mx  # noqa: E402

# The cells used on the slides (chosen for being large and sharp)
PICKS = {
    "parasitized_0": "C101P62ThinF_IMG_20150918_151006_cell_76.png",
    "parasitized_1": "C99P60ThinF_IMG_20150918_141620_cell_6.png",
    "parasitized_3": "C82P43ThinF_IMG_20150817_124418_cell_164.png",
    "uninfected_0": "C12NThinF_IMG_20150614_124212_cell_165.png",
    "uninfected_1": "C87P48ThinF_IMG_20150820_132642_cell_83.png",
    "uninfected_2": "C6NThinF_IMG_20150609_122832_cell_170.png",
}


def circle(path, out, size=480, yuv=False):
    bgr = cv2.imread(path)
    if yuv:
        bgr = mx.yuv_equalize(bgr)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    s = max(h, w)
    canvas = np.zeros((s, s, 3), np.uint8)
    canvas[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = rgb
    im = Image.fromarray(canvas).resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    im.putalpha(mask)
    im.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(REPO, "outputs", "data", "cell_images"))
    args = ap.parse_args()
    out = os.path.join(HERE, "assets")
    os.makedirs(out, exist_ok=True)
    for name, f in PICKS.items():
        label = "Parasitized" if name.startswith("parasitized") else "Uninfected"
        path = os.path.join(args.data, label, f)
        circle(path, os.path.join(out, f"{name}.png"))
        if name.endswith("_0"):
            circle(path, os.path.join(out, f"{name}_yuv.png"), yuv=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
