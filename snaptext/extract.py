"""Input dispatch: PDFs (text layer or OCR), photos, plain text."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .ocr import Line, ocr_image

DPI = 200
PDF_EXTS = {".pdf"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}
TEXT_EXTS = {".txt", ".md", ".log"}
SUPPORTED = PDF_EXTS | IMG_EXTS | TEXT_EXTS


@dataclass
class Page:
    lines: list = field(default_factory=list)
    source: str = "ocr"  # "text" = embedded text layer, "ocr" = recognized
    w_px: int = 0
    h_px: int = 0


def _pixmap_to_image(pix):
    from PIL import Image

    mode = "RGB" if pix.n == 3 else "RGBA"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def extract_pdf(path: Path) -> list:
    from pypdf import PdfReader

    reader = PdfReader(path)
    embedded = [(page.extract_text() or "").strip() for page in reader.pages]
    if any(embedded):
        return [
            Page(lines=[Line(text=t, conf=1.0) for t in text.splitlines()], source="text")
            for text in embedded
        ]

    import pymupdf

    doc = pymupdf.open(path)
    pages = []
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=DPI, alpha=False)
            pages.append(
                Page(lines=ocr_image(_pixmap_to_image(pix)), w_px=pix.width, h_px=pix.height)
            )
    finally:
        doc.close()
    return pages


def extract_image(path: Path) -> list:
    from PIL import Image

    with Image.open(path) as img:
        w, h = img.size
        lines = ocr_image(img)
    return [Page(lines=lines, w_px=w, h_px=h)]


def extract_any(path: Path) -> list:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTS:
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                raw = path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
            return [Page(lines=[Line(text=t, conf=1.0) for t in raw.splitlines()], source="text")]
        return [Page()]
    if suffix in IMG_EXTS:
        return extract_image(path)
    if suffix in PDF_EXTS:
        return extract_pdf(path)
    raise ValueError(f"unsupported file type: {path.suffix}")


def render(pages: list, threshold: float = 0.6) -> str:
    parts = []
    multi = len(pages) > 1
    for i, page in enumerate(pages, start=1):
        if multi:
            parts.append(f"--- Page {i} ---")
        for line in page.lines:
            text = line.text.rstrip()
            if not text:
                continue
            if line.conf < threshold:
                text += "  [?]"
            parts.append(text)
    return "\n".join(parts)


def report(pages: list, threshold: float = 0.6) -> str:
    total = sum(len(p.lines) for p in pages)
    if total == 0:
        return "no text found"
    chars = sum(len(line.text) for p in pages for line in p.lines)
    flagged = sum(1 for p in pages for line in p.lines if line.conf < threshold)
    confs = [line.conf for p in pages if p.source == "ocr" for line in p.lines]
    avg = f", avg confidence {sum(confs) / len(confs):.2f}" if confs else ""
    sources = ", ".join(sorted({p.source for p in pages}))
    return f"{total} lines, {chars} chars ({sources}{avg}), {flagged} flagged below {threshold}"
