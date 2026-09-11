"""Permite ``python -m openstruct.gui``."""

from __future__ import annotations

import sys

from .app import main

if __name__ == "__main__":  # pragma: no cover — ponto de entrada, `main()` coberto por teste
    sys.exit(main())
