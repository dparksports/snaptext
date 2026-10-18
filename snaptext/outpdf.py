"""Searchable PDF output: original page image + invisible text layer."""
from __future__ import annotations

from pathlib import Path


def _overlay(page, lines, scale: float) -> None:
    for line in lines:
        if not line.box:
            continue
        xs = [p[0] for p in line.box]
        ys = [p[1] for p in line.box]
        x0, y_top = min(xs) * scale, min(ys) * scale
        h = (max(ys) - min(ys)) * scale
        if h <= 0:
            continue
        fontsize = max(4.0, h * 0.85)
        try:
            page.insert_text((x0, y_top + h * 0.8), line.text, fontsize=fontsize, render_mode=3)
        except Exception:
            continue  # glyphs the base PDF font cannot encode


def overlay_pdf(src: Path, out: Path, pages: list) -> None:
    import pymupdf

    doc = pymupdf.open(src)
    for page, data in zip(doc, pages):
        if data.w_px:
            _overlay(page, data.lines, page.rect.width / data.w_px)
    doc.save(out, garbage=3, deflate=True)
    doc.close()


def images_pdf(src: Path, out: Path, page_data) -> None:
    import pymupdf

    scale = 72.0 / 96.0  # treat image pixels as 96 dpi
    doc = pymupdf.open()
    w, h = page_data.w_px * scale, page_data.h_px * scale
    page = doc.new_page(width=w, height=h)
    page.insert_image(pymupdf.Rect(0, 0, w, h), filename=str(src))
    _overlay(page, page_data.lines, scale)
    doc.save(out, garbage=3, deflate=True)
    doc.close()
