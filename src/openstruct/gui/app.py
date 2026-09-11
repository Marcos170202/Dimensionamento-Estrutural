"""Ponto de entrada da GUI desktop.

Uso: ``python -m openstruct.gui`` ou o script ``openstruct3d-gui``
instalado por ``pip install -e ".[gui]"`` (ver
``[project.gui-scripts]`` em ``pyproject.toml``).
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover — ponto de entrada, `main()` coberto por teste
    sys.exit(main())
