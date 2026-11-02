"""Tests for src/triage_kit.py: full-size, numbers-only pages of the Phase 3b blind-triage gallery."""
import os
import re
import sys

import pandas as pd
import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import triage_kit as tk  # noqa: E402


def pdf_pages(path):
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", open(path, "rb").read()))


def test_tiles_from_key_returns_ids_in_order_with_their_own_files_and_no_labels(tmp_path):
    key = pd.DataFrame(dict(id=[3, 1, 2], file=["c.png", "a.png", "b.png"],
                            label=["uninfected", "parasitized", "uninfected"],
                            p_parasitized=[0.9, 0.1, 0.2], model_call=["parasitized", "uninfected", "uninfected"],
                            error=[True, True, False]))
    out = tk.tiles_from_key(key, "/data")
    assert len(out) == 2  # ids and paths only: nothing that could reveal the answer reaches the pages
    ids, paths = out
    assert ids == [1, 2, 3]
    assert paths == [os.path.join("/data", "Parasitized", "a.png"), os.path.join("/data", "Uninfected", "b.png"),
                     os.path.join("/data", "Uninfected", "c.png")]


def test_triage_pdf_writes_one_page_per_block_of_cells(tmp_path):
    paths = []
    for i in range(30):
        p = tmp_path / f"cell_{i}.png"
        Image.new("RGB", (120 + i, 130), (200, 100, 120)).save(p)
        paths.append(str(p))
    out = tmp_path / "pages.pdf"
    n = tk.triage_pdf(list(range(1, 31)), paths, str(out), per_page=24)
    assert n == 2
    assert pdf_pages(out) == 2


def test_triage_pdf_refuses_ids_and_paths_of_different_lengths(tmp_path):
    with pytest.raises(ValueError):
        tk.triage_pdf([1, 2], ["only_one.png"], str(tmp_path / "x.pdf"))
