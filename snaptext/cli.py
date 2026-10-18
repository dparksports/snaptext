"""snaptext CLI: turn on-screen text into clipboard text for LLM chats.

Running snaptext with no command is the main flow: it OCRs whatever image is
on the clipboard (put one there with Win+Shift+S, Ctrl+Cmd+Shift+4 or your
desktop's screenshot tool) and puts the text back on the clipboard, ready to
paste into any chat box.

Commands:
    (none)   clipboard image -> text -> clipboard
    hotkey   resident: one key, warm engine, capture -> text on clipboard
    file     extract text from PDFs/photos (auto-detects text layer vs OCR)
    pdf      build a searchable PDF (invisible text under the original image)
    snap     capture the screen (or a region), OCR it, copy text
    watch    watch a folder, extract every new supported file automatically
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .extract import Page, extract_any, extract_image, extract_pdf, render, report


def _emit(pages: list, threshold: float, output: Path | None, to_clipboard: bool, label: str) -> None:
    text = render(pages, threshold)
    if text:
        print(text)
    print(f"[{label}: {report(pages, threshold)}]", file=sys.stderr)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"[wrote {output}]", file=sys.stderr)
    if to_clipboard and text:
        from .clipboard import copy_text

        print(f"[{copy_text(text)}]", file=sys.stderr)


def cmd_file(args) -> int:
    ok = True
    for path in args.paths:
        try:
            pages = extract_any(path)
        except Exception as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            ok = False
            continue
        if args.no_file:
            out = None
        elif len(args.paths) == 1 and args.output and args.output.suffix == ".txt":
            out = args.output
        elif args.output:
            out = args.output / f"{path.stem}.txt"
        else:
            out = path.with_suffix(".txt")
        _emit(pages, args.threshold, out, False, path.name)
    return 0 if ok else 1


def cmd_pdf(args) -> int:
    src = args.input
    out = args.output or src.with_name(src.stem + "_searchable.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".pdf":
        pages = extract_pdf(src)
        if all(p.source == "text" for p in pages):
            shutil.copy(src, out)
            print("input already has a text layer; copied unchanged", file=sys.stderr)
            return 0
        from .outpdf import overlay_pdf

        overlay_pdf(src, out, pages)
    else:
        pages = extract_image(src)
        from .outpdf import images_pdf

        images_pdf(src, out, pages[0])
    print(f"[wrote {out} ({report(pages)})]", file=sys.stderr)
    return 0


def cmd_paste(args) -> int:
    from .clipboard import grab_image
    from .ocr import ocr_image

    img = grab_image()
    if img is None:
        print(
            "no image on the clipboard - take a screenshot first "
            "(Win+Shift+S, Ctrl+Cmd+Shift+4, or your desktop's screenshot tool)",
            file=sys.stderr,
        )
        return 1
    page = Page(lines=ocr_image(img), w_px=img.width, h_px=img.height)
    _emit([page], args.threshold, getattr(args, "output", None), True, "clipboard image")
    return 0


def cmd_snap(args) -> int:
    from .capture import snap
    from .ocr import ocr_image

    img = snap(args.monitor, args.region)
    if args.save:
        img.save(args.save)
    page = Page(lines=ocr_image(img), w_px=img.width, h_px=img.height)
    _emit([page], args.threshold, args.output, not args.no_clipboard, f"monitor {args.monitor}")
    return 0


def cmd_watch(args) -> int:
    from .watch import process_folder

    try:
        process_folder(args.folder, args.outdir, args.threshold, args.once, args.interval)
    except KeyboardInterrupt:
        print("\nstopped", file=sys.stderr)
    return 0


def cmd_hotkey(args) -> int:
    from .hotkey import run

    try:
        run(args.key, args.mode, args.threshold, args.monitor)
    except KeyboardInterrupt:
        print("\n[hotkey] stopped", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snaptext",
        description=(
            "Turn on-screen text into clipboard text for LLM chats "
            "(ZCode, z.ai, autocrawl, ChatGPT, ...) - fully local. "
            "Run with no command to OCR the clipboard image and put text back."
        ),
    )
    parser.add_argument("--version", action="version", version=f"snaptext {__version__}")
    parser.add_argument(
        "--threshold", type=float, default=0.6,
        help="confidence below this is flagged ' [?]' in output (default 0.6)",
    )
    sub = parser.add_subparsers(dest="cmd")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--threshold", type=float, default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )

    p = sub.add_parser("file", parents=[common], help="extract text from files")
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("-o", "--output", type=Path, help="output .txt (single file) or directory (multiple)")
    p.add_argument("-n", "--no-file", action="store_true", help="print to stdout only, write nothing")
    p.set_defaults(func=cmd_file)

    p = sub.add_parser("pdf", parents=[common], help="make a searchable PDF from a scan or photo")
    p.add_argument("input", type=Path)
    p.add_argument("-o", "--output", type=Path, help="output PDF (default: <name>_searchable.pdf)")
    p.set_defaults(func=cmd_pdf)

    p = sub.add_parser("paste", parents=[common], help="clipboard image -> text -> clipboard")
    p.add_argument("-o", "--output", type=Path, help="also write text to this file")
    p.set_defaults(func=cmd_paste)

    p = sub.add_parser("snap", parents=[common], help="capture screen, OCR it, copy text")
    p.add_argument("--monitor", type=int, default=1, help="1=primary, 2+=secondary, 0=all combined")
    p.add_argument("--region", help="crop 'left,top,width,height' in monitor pixels")
    p.add_argument("--save", type=Path, help="also save the raw screenshot here")
    p.add_argument("--no-clipboard", action="store_true", help="do not overwrite clipboard with text")
    p.add_argument("-o", "--output", type=Path, help="also write text to this file")
    p.set_defaults(func=cmd_snap)

    p = sub.add_parser("watch", parents=[common], help="watch a folder, extract new files automatically")
    p.add_argument("folder", type=Path)
    p.add_argument("--outdir", type=Path, help="write .txt files here (default: next to each input)")
    p.add_argument("--interval", type=float, default=2.0, help="seconds between scans (default 2)")
    p.add_argument("--once", action="store_true", help="process current files once and exit")
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("hotkey", parents=[common], help="resident: one key, capture -> text on clipboard")
    p.add_argument("--key", default="ctrl+alt+t", help="hotkey to register (default ctrl+alt+t)")
    p.add_argument(
        "--mode", choices=["snap", "paste"], default="snap",
        help="snap = capture the whole monitor; paste = OCR whatever image is on the clipboard",
    )
    p.add_argument("--monitor", type=int, default=1, help="monitor for snap mode (default 1)")
    p.set_defaults(func=cmd_hotkey)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "cmd", None) is None:
        args.output = None
        return cmd_paste(args)
    return args.func(args)
