"""Testes de ``openstruct.gui.main_window.MainWindow``."""

from __future__ import annotations

from openstruct.gui.checks_tab import ChecksTab
from openstruct.gui.main_window import MainWindow
from openstruct.gui.model_tab import ModelTab
from openstruct.gui.viewport_3d import Viewport3D


def test_main_window_title(qapp: object) -> None:
    window = MainWindow()
    assert window.windowTitle() == "OpenStruct 3D"


def test_main_window_has_three_tabs(qapp: object) -> None:
    window = MainWindow()
    tabs = window.centralWidget()
    assert tabs.count() == 3
    assert tabs.tabText(0) == "Modelo e Análise"
    assert tabs.tabText(1) == "Visualização 3D"
    assert tabs.tabText(2) == "Verificações NBR 8800"


def test_main_window_exposes_model_viewport_and_checks_tabs(qapp: object) -> None:
    window = MainWindow()
    assert isinstance(window.model_tab, ModelTab)
    assert isinstance(window.viewport_tab, Viewport3D)
    assert isinstance(window.checks_tab, ChecksTab)


def test_main_window_viewport_shares_the_same_model_tab(qapp: object) -> None:
    window = MainWindow()
    assert window.viewport_tab.model_tab is window.model_tab
