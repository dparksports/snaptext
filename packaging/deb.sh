#!/usr/bin/env bash
# Package the PyInstaller output as a .deb (Ubuntu/Debian).
# Run after `pyinstaller snaptext.spec` produced dist/snaptext/
#
# Requires fpm:  gem install fpm
#   bash packaging/deb.sh
set -euo pipefail

VERSION="$(python3 -c 'import snaptext; print(snaptext.__version__)')"

fpm --input-type dir --output-type deb \
    --name snaptext --version "$VERSION" --architecture native \
    --license "Apache-2.0" \
    --description "Feed LLMs text, not screenshots - local OCR to clipboard" \
    --url "https://github.com/dparksports/snaptext" \
    --after-install <(echo 'ln -sf /opt/snaptext/snaptext /usr/local/bin/snaptext') \
    --after-remove <(echo 'rm -f /usr/local/bin/snaptext') \
    --prefix /opt/snaptext \
    -C dist/snaptext .

echo "built snaptext_${VERSION}_$(dpkg --print-architecture).deb"
