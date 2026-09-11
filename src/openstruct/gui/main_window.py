"""Janela principal: agrega as abas de modelo/analise, visualizacao 3D
e verificacoes NBR 8800."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

from .checks_tab import ChecksTab
from .model_tab import ModelTab
from .viewport_3d import Viewport3D


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("OpenStruct 3D")
        self.resize(1100, 800)

        tabs = QTabWidget(self)
        self.model_tab = ModelTab(self)
        self.viewport_tab = Viewport3D(self.model_tab, self)
        self.checks_tab = ChecksTab(self)
        tabs.addTab(self.model_tab, "Modelo e Análise")
        tabs.addTab(self.viewport_tab, "Visualização 3D")
        tabs.addTab(self.checks_tab, "Verificações NBR 8800")
        self.setCentralWidget(tabs)
