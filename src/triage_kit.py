#!/usr/bin/env python3
"""Full-size pages of the Phase 3b blind-triage gallery (docs/phase3b_addendum.md, E4e).

phase3b_error_gallery.png shrinks every cell to 72 px, too small to judge a faint ring. These pages show the same
numbered cells at full resolution, 24 per A4 page. They carry numbers only: the labels and model calls stay in the
key file, which is opened after the triage (docs/blind_triage_protocol.md).

Usage:
    python src/triage_kit.py      # writes results/phase3b/phase3b_triage_pages.pdf
"""
import argparse
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FOLDER = {"parasitized": "Parasitized", "uninfected": "Uninfected"}  # NIH's class folders


def tiles_from_key(key, image_dir):
    """(ids, paths) in id order. The label only locates each file's folder and is not returned."""
    key = key.sort_values("id")
    paths = [os.path.join(image_dir, FOLDER[label], f) for label, f in zip(key["label"], key["file"])]
    return [int(i) for i in key["id"]], paths


def triage_pdf(ids, paths, out_pdf, per_page=24, cols=4, title="Blind triage"):
    """Write the cells, each under its number, `per_page` to an A4 page. Returns the number of pages."""
    if len(ids) != len(paths):
        raise ValueError(f"{len(ids)} ids but {len(paths)} images")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from PIL import Image
    rows = int(np.ceil(per_page / cols))
    n_pages = int(np.ceil(len(ids) / per_page))
    tiles = list(zip(ids, paths))
    with PdfPages(out_pdf, metadata={"Title": title}) as pdf:
        for page in range(n_pages):
            chunk = tiles[page * per_page:(page + 1) * per_page]
            fig, axes = plt.subplots(rows, cols, figsize=(8.27, 11.69), squeeze=False)
            for ax in axes.flat:
                ax.axis("off")
            for ax, (i, path) in zip(axes.flat, chunk):
                ax.imshow(Image.open(path).convert("RGB"), interpolation="none")  # original pixels, no resampling
                ax.set_title(str(i), fontsize=15, fontweight="bold", color="#1F2A44", pad=4)
            fig.suptitle(f"{title} · cells {chunk[0][0]}–{chunk[-1][0]} of {len(ids)} · page {page + 1} of {n_pages}",
                         fontsize=10, color="#52514e")
            fig.subplots_adjust(left=0.04, right=0.96, top=0.94, bottom=0.03, wspace=0.12, hspace=0.25)
            pdf.savefig(fig)
            plt.close(fig)
    return n_pages


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--key", default=os.path.join(REPO, "results", "phase3b", "phase3b_error_gallery_KEY.csv"))
    ap.add_argument("--image-dir", default=os.path.join(REPO, "outputs", "data", "cell_images"))
    ap.add_argument("--out", default=os.path.join(REPO, "results", "phase3b", "phase3b_triage_pages.pdf"))
    args = ap.parse_args()
    ids, paths = tiles_from_key(pd.read_csv(args.key), args.image_dir)
    n = triage_pdf(ids, paths, args.out)
    print(f"wrote {args.out}: {len(ids)} cells on {n} pages")


if __name__ == "__main__":
    main()
