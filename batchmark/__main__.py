"""Allow running batchmark as a module: python -m batchmark."""

import sys

from batchmark.cli import main

if __name__ == "__main__":
    sys.exit(main())
