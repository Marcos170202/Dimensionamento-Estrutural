"""Fixtures compartilhadas dos testes da GUI.

Roda sempre em modo ``offscreen`` (sem display real) — necessario em
CI e neste sandbox. A variavel precisa estar definida ANTES da
primeira ``QApplication`` ser criada, entao e ajustada aqui no topo do
modulo, antes de qualquer import de ``PySide6``.

O pacote ``openstruct.gui`` depende do extra opcional ``gui``
(``pip install -e ".[gui]"``) — se o ``PySide6`` nao estiver instalado,
todos os testes deste diretorio sao pulados (``importorskip``) em vez
de falhar, para nao quebrar quem roda a suite so com ``.[dev]``.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6", reason="extra opcional 'gui' nao instalado")

from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """``QApplication`` unica para toda a sessao de testes (Qt exige no maximo uma)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
