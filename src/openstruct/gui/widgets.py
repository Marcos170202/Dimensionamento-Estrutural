"""Widgets reutilizaveis da GUI.

``EditableTable`` fatora o padrao repetido em ``model_tab.py``
(tabela editavel de linhas + botoes "Adicionar linha"/"Remover
linha(s)") para as 6 tabelas do modelo (nos, materiais, secoes,
elementos, apoios, cargas) sem duplicar o mesmo layout/logica 6 vezes.
"""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class EditableTable(QWidget):
    """Tabela editavel com colunas fixas e botoes de adicionar/remover linha.

    Cada celula e texto livre (``QTableWidgetItem`` editavel) — a
    validacao/conversao de tipo (``int``/``float``) e feita pelo
    chamador ao LER os dados (``row_values``), nao por esta classe,
    para manter a mensagem de erro com contexto (qual campo, qual
    linha) no lugar que efetivamente sabe o que cada coluna significa.
    """

    def __init__(self, columns: Sequence[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._columns = list(columns)

        self.table = QTableWidget(0, len(columns), self)
        self.table.setHorizontalHeaderLabels(list(columns))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)

        add_button = QPushButton("Adicionar linha", self)
        add_button.clicked.connect(self.add_row)
        remove_button = QPushButton("Remover linha(s) selecionada(s)", self)
        remove_button.clicked.connect(self._remove_selected_rows)

        button_row = QHBoxLayout()
        button_row.addWidget(add_button)
        button_row.addWidget(remove_button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        layout.addLayout(button_row)

    def add_row(self, values: Sequence[str] | None = None) -> None:
        """Adiciona uma linha, opcionalmente ja preenchida com ``values``."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        if values is not None:
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def _remove_selected_rows(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    @property
    def row_count(self) -> int:
        return self.table.rowCount()

    def cell_text(self, row: int, column: int) -> str:
        """Texto da celula, ou string vazia se a celula nao foi preenchida."""
        item = self.table.item(row, column)
        return "" if item is None else item.text().strip()

    def row_values(self, row: int) -> list[str]:
        """Todos os valores (texto bruto) de uma linha, na ordem das colunas."""
        return [self.cell_text(row, col) for col in range(len(self._columns))]

    def all_rows(self) -> list[list[str]]:
        """Todas as linhas (texto bruto), na ordem em que aparecem na tabela."""
        return [self.row_values(row) for row in range(self.row_count)]
