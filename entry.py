"""PyInstaller entry point: the binary is the CLI."""
import sys

from snaptext.cli import main

sys.exit(main())
