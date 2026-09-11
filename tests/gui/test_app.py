"""Testes de ``openstruct.gui.app.main``.

``main()`` chama ``app.exec()``, que entra no loop de eventos do Qt e
so retorna quando alguem chama ``app.quit()`` — nao ha isso no modo
``offscreen`` sem interacao, entao o ``exec`` real e substituido por um
stub que apenas confirma que foi chamado (o comportamento de
"mostrar a janela e devolver o codigo de saida do Qt" e o unico
contrato que ``main()`` promete; o loop de eventos em si e
responsabilidade do Qt, ja testado por seus proprios mantenedores).
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

import openstruct.gui.app as app_module


def test_main_shows_window_and_returns_exec_code(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(QApplication, "exec", lambda self: calls.append("exec") or 0)

    exit_code = app_module.main()

    assert exit_code == 0
    assert calls == ["exec"]


def test_main_reuses_existing_qapplication_instance(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    assert QApplication.instance() is qapp
    app_module.main()
    assert QApplication.instance() is qapp
