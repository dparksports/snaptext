"""Screen capture via mss (works without any OS-specific integration)."""
from __future__ import annotations

from PIL import Image


def snap(monitor: int = 1, region: str | None = None) -> Image.Image:
    import mss

    with mss.mss() as sct:
        if monitor > 0:
            monitor = min(monitor, len(sct.monitors) - 1)
            mon = dict(sct.monitors[monitor])
        else:
            mon = dict(sct.monitors[0])  # all monitors combined
        if region:
            left, top, width, height = (int(v) for v in region.split(","))
            mon = {
                "left": mon["left"] + left,
                "top": mon["top"] + top,
                "width": width,
                "height": height,
            }
        shot = sct.grab(mon)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
