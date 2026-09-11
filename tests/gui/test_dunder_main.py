"""Testa que ``openstruct.gui.__main__`` importa e expõe ``main`` corretamente.

O bloco ``if __name__ == "__main__":`` em si (guarda de execucao) e
excluido da cobertura via ``# pragma: no cover`` — chamar ``main()``
de verdade entra no loop de eventos do Qt (ver ``test_app.py``).
"""

from __future__ import annotations

import openstruct.gui.__main__ as dunder_main
from openstruct.gui.app import main


def test_dunder_main_re_exports_app_main() -> None:
    assert dunder_main.main is main
