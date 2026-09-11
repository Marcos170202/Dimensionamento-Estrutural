"""Testes de ``openstruct.gui.main_window.MainWindow``."""

from __future__ import annotations

from openstruct.gui.checks_tab import ChecksTab
from openstruct.gui.main_window import MainWindow
from openstruct.gui.model_tab import ModelTab


def test_main_window_title(qapp: object) -> None:
    window = MainWindow()
    assert window.windowTitle() == "OpenStruct 3D"


def test_main_window_has_two_tabs(qapp: object) -> None:
    window = MainWindow()
    tabs = window.centralWidget()
    assert tabs.count() == 2
    assert tabs.tabText(0) == "Modelo e Análise"
    assert tabs.tabText(1) == "Verificações NBR 8800"


def test_main_window_exposes_model_and_checks_tabs(qapp: object) -> None:
    window = MainWindow()
    assert isinstance(window.model_tab, ModelTab)
    assert isinstance(window.checks_tab, ChecksTab)
