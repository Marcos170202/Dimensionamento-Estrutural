"""Ponto de entrada usado SO pelo PyInstaller.

``openstruct.gui.app`` usa import relativo (``from .main_window import
MainWindow``), o que funciona normalmente porque o modulo e importado
como PARTE do pacote ``openstruct.gui`` (por ``python -m
openstruct.gui`` ou pelo script ``openstruct3d-gui`` do
``[project.gui-scripts]``). O PyInstaller, porem, roda o script dado
em ``Analysis()`` como modulo ``__main__`` de top-level, sem pacote —
e ai o import relativo de ``app.py`` falha com ``ImportError:
attempted relative import with no known parent package``.

Este arquivo existe so para dar ao PyInstaller um ponto de entrada que
importa ``openstruct.gui.app`` da forma normal (absoluta, como
pacote) antes de chamar ``main()`` — nao duplica nenhuma logica da
GUI.
"""

from __future__ import annotations

import sys

from openstruct.gui.app import main

if __name__ == "__main__":
    sys.exit(main())
