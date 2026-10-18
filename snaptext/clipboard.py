"""Cross-platform clipboard: text out, image in."""
from __future__ import annotations

import shutil
import subprocess
import sys
from io import BytesIO


def copy_text(text: str) -> str:
    import pyperclip

    pyperclip.copy(text)
    return "text copied - paste into any chat box (Ctrl+V)"


def grab_image():
    """Return a PIL Image from the clipboard, or None if it holds no image."""
    if sys.platform.startswith("win") or sys.platform == "darwin":
        from PIL import Image, ImageGrab

        try:
            img = ImageGrab.grabclipboard()
        except Exception:
            return None
        return img if isinstance(img, Image.Image) else None

    cmds = [
        ["wl-paste", "--type", "image/png"],
        ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
    ]
    for cmd in cmds:
        if not shutil.which(cmd[0]):
            continue
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0 and proc.stdout:
            from PIL import Image

            return Image.open(BytesIO(proc.stdout))
    return None
