"""Resident mode: one hotkey, warm engine, capture -> text on clipboard."""
from __future__ import annotations

import sys
import threading
import time

import numpy as np

from .capture import snap as take_screenshot
from .clipboard import copy_text, grab_image
from .extract import Page, render, report
from .ocr import ocr_image

_lock = threading.Lock()


def _warm_engine() -> None:
    from .ocr import get_engine

    get_engine()(np.zeros((64, 64, 3), dtype=np.uint8))


def _capture_once(mode: str, monitor: int, threshold: float) -> None:
    try:
        with _lock:
            started = time.perf_counter()
            if mode == "paste":
                img = grab_image()
                if img is None:
                    print("[hotkey] no image on the clipboard", file=sys.stderr, flush=True)
                    return
            else:
                img = take_screenshot(monitor)
            lines = ocr_image(img)
            page = Page(lines=lines, w_px=img.width, h_px=img.height)
            text = render([page], threshold)
            elapsed = time.perf_counter() - started
            if not text:
                print(f"[hotkey:{mode}] no text found ({elapsed:.1f}s)", file=sys.stderr, flush=True)
                return
            copy_text(text)
            print(
                f"[hotkey:{mode}] {report([page], threshold)} -> clipboard ({elapsed:.1f}s)",
                file=sys.stderr,
                flush=True,
            )
    except Exception as exc:
        print(f"[hotkey:{mode}] failed: {exc}", file=sys.stderr, flush=True)


def run(key: str, mode: str, threshold: float, monitor: int) -> None:
    try:
        import keyboard
    except ImportError:
        raise SystemExit(
            "the hotkey command needs an optional extra:\n"
            "    pip install '.[hotkey]'"
        )

    print("[hotkey] warming the OCR engine...", file=sys.stderr, flush=True)
    _warm_engine()
    keyboard.add_hotkey(key, lambda: _capture_once(mode, monitor, threshold))
    print(
        f"[hotkey] ready - {key} runs '{mode}' into the clipboard, Ctrl+C to quit",
        file=sys.stderr,
        flush=True,
    )
    keyboard.wait()
