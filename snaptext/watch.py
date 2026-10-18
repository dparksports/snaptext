"""Watch a folder and extract anything new. Polling keeps it dependency-free
and lock-tolerant: a file mid-copy simply fails to open and retries next pass."""
from __future__ import annotations

import time
from pathlib import Path

from .extract import SUPPORTED, extract_any, render, report


def _output_path(path: Path, outdir: Path | None) -> Path:
    target = outdir if outdir else path.parent
    return target / f"{path.stem}.txt"


def process_folder(folder: Path, outdir: Path | None, threshold: float, once: bool, interval: float = 2.0) -> int:
    folder = folder.resolve()
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)
    processed = 0
    while True:
        pending = [
            p
            for p in sorted(folder.iterdir())
            if p.is_file() and p.suffix.lower() in SUPPORTED and not _output_path(p, outdir).exists()
        ]
        for path in pending:
            out_path = _output_path(path, outdir)
            try:
                pages = extract_any(path)
            except Exception as exc:
                print(f"skip  {path.name}: {exc}", flush=True)
                continue
            out_path.write_text(render(pages, threshold), encoding="utf-8")
            print(f"OK    {path.name} -> {out_path}  ({report(pages, threshold)})", flush=True)
            processed += 1
        if once:
            return processed
        time.sleep(interval)
