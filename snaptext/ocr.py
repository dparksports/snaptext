"""OCR engine wrapper: preprocessing, recognition, per-line confidence."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageOps


@dataclass
class Line:
    text: str
    conf: float
    box: list = field(default_factory=list)


_ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR

        _ENGINE = RapidOCR()
    return _ENGINE


def prepare(img: Image.Image) -> np.ndarray:
    img = ImageOps.exif_transpose(img)
    img = ImageOps.autocontrast(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.asarray(img)


def ocr_image(img: Image.Image) -> list[Line]:
    arr = prepare(img)
    result, _ = get_engine()(arr)
    lines = [
        Line(text=str(text), conf=float(conf), box=[list(p) for p in box])
        for box, text, conf in (result or [])
    ]
    lines.sort(key=lambda l: (min(p[1] for p in l.box), min(p[0] for p in l.box)))
    return lines
