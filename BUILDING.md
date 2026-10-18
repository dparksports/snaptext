# BUILDING.md — four ways to run snaptext you built yourself

For DIY-technical users. Paths are ordered by effort; all of them start from
a clone of this repo. CI is not required for any of them.

    git clone https://github.com/dparksports/snaptext
    cd snaptext

| Path | You get | Effort | Best when |
|---|---|---|---|
| 1 · [pipx](#1-pipx) | the `snaptext` command on your PATH | ~2 min | you just want to use it |
| 2 · [PyInstaller](#2-pyinstaller--standalone-binary) | a standalone binary bundle | ~5 min | you want an app you can copy around |
| 3 · [Docker](#3-docker) | a container image / Linux runs | ~3 min | reproducibility, or no local Python |
| 4 · [OS-native packages](#4-os-native-packages) | setup.exe / .app / .deb | +5 min | distributing to other machines |

## 1 · pipx

```bash
pipx install .          # from the clone directory
snaptext --version
```

pipx creates the isolated environment for you and links `snaptext` onto your
PATH. Upgrades: `pipx upgrade snaptext`. If you don't have pipx:
`python -m pip install --user pipx` (Windows) or `brew install pipx` (macOS)
or `sudo apt install pipx` (Ubuntu).

## 2 · PyInstaller — standalone binary

One command, natively on each OS (PyInstaller does not cross-compile, so
build the Windows binary on Windows, the .app on a Mac, etc.):

```bash
pip install -e ".[build]"        # pulls in pyinstaller + the hotkey extra
pyinstaller snaptext.spec
```

Output: `dist/snaptext/` containing `snaptext.exe` (Windows) or `snaptext`
(macOS/Linux) plus everything it needs — **OCR models are bundled**, so the
binary works offline from the first run. `snaptext.spec` is the build
contract; it is the same file release automation runs, so your build and the
official one cannot drift apart.

Why *onedir* and not a single file: onefile bundles self-extract on every
launch (slow first start) and trigger far more antivirus false positives on
Windows. Zip the `dist/snaptext/` folder if you want to move it around.

## 3 · Docker

```bash
docker build -t snaptext .
docker run --rm -v "$PWD:/data" snaptext file /data/scan.pdf
```

Scope: `file`, `pdf` and `watch` on mounted volumes. Screen capture and
hotkeys need a host desktop session and are **not supported** in the
container. To produce a *Linux binary* without installing anything on your
host, run the Path 2 commands inside a `python:3.12-slim` container.

## 4 · OS-native packages

Optional polish for distributing to other machines. Each script consumes the
`dist/snaptext/` output of Path 2:

| OS | Command | Requirement | Output |
|---|---|---|---|
| Windows | `iscc packaging\windows-installer.iss` | [Inno Setup 6](https://jrsoftware.org/isinfo.php) | `snaptext-setup.exe` |
| macOS | `bash packaging/macos-app.sh` | none | `Snaptext.app` |
| Ubuntu | `bash packaging/deb.sh` | `gem install fpm` | `snaptext_<version>_<arch>.deb` |

## Verify your build

Before trusting (or shipping) a build, run:

```bash
dist/snaptext/snaptext --version
# render a known image and check the OCR reads it back:
python - <<'EOF'
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB", (700, 160), "white")
d = ImageDraw.Draw(img)
d.text((30, 50), "Warranty Claim #BA7763", fill="black",
       font=ImageFont.load_default(size=36))
img.save("smoke.png")
EOF
dist/snaptext/snaptext file smoke.png -n
```

Expect `Warranty Claim #BA7763` in the output with no ` [?]` flags.

## Caveats worth knowing before you distribute

- **Size**: bundles are ~150–300 MB (a measured Windows build is 266 MB);
  ONNX Runtime is the bulk of it.
- **Unsigned binaries**: Windows SmartScreen will say "Windows protected
  your PC" → *More info → Run anyway*. macOS Gatekeeper: right-click →
  *Open* the first time. Ubuntu: no warnings. Real code signing (esp. an
  Apple Developer ID, $99/yr) is a later, separate decision.
- **Python versions**: supported 3.9–3.13. Note that on Python 3.13 pip
  resolves `rapidocr-onnxruntime` to 1.2.3 (the last release whose metadata
  allows 3.13) — that is expected, not a bug; don't "fix" the pin.
- **First-run network**: not needed — models ship inside the wheel and the
  spec bundles them.

## Repo layout for builders

    entry.py                    PyInstaller entry point
    snaptext.spec               the build contract (models, hidden imports)
    Dockerfile                  container image
    packaging/windows-installer.iss   Inno Setup script
    packaging/macos-app.sh      .app wrapper
    packaging/deb.sh            fpm .deb packager
