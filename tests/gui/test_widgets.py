"""Testes de ``openstruct.gui.widgets.EditableTable``."""

from __future__ import annotations

from PySide6.QtWidgets import QTableWidgetSelectionRange

from openstruct.gui.widgets import EditableTable


def test_new_table_is_empty(qapp: object) -> None:
    table = EditableTable(["A", "B"])
    assert table.row_count == 0
    assert table.all_rows() == []


def test_add_row_without_values_creates_empty_row(qapp: object) -> None:
    table = EditableTable(["A", "B"])
    table.add_row()
    assert table.row_count == 1
    assert table.row_values(0) == ["", ""]


def test_add_row_with_values(qapp: object) -> None:
    table = EditableTable(["A", "B"])
    table.add_row(["1", "2"])
    assert table.row_count == 1
    assert table.row_values(0) == ["1", "2"]
    assert table.all_rows() == [["1", "2"]]


def test_add_row_with_non_string_values_is_stringified(qapp: object) -> None:
    table = EditableTable(["A"])
    table.add_row([42])
    assert table.row_values(0) == ["42"]


def test_cell_text_of_unset_cell_is_empty_string(qapp: object) -> None:
    table = EditableTable(["A"])
    table.add_row()
    assert table.cell_text(0, 0) == ""


def test_cell_text_strips_surrounding_whitespace(qapp: object) -> None:
    table = EditableTable(["A"])
    table.add_row(["  x  "])
    assert table.cell_text(0, 0) == "x"


def test_all_rows_preserves_order(qapp: object) -> None:
    table = EditableTable(["A"])
    table.add_row(["1"])
    table.add_row(["2"])
    table.add_row(["3"])
    assert table.all_rows() == [["1"], ["2"], ["3"]]


def test_remove_selected_rows(qapp: object) -> None:
    table = EditableTable(["A"])
    table.add_row(["1"])
    table.add_row(["2"])
    table.add_row(["3"])
    table.table.selectRow(1)
    table._remove_selected_rows()
    assert table.all_rows() == [["1"], ["3"]]


def test_remove_selected_rows_multiple_selection(qapp: object) -> None:
    table = EditableTable(["A"])
    for value in ("1", "2", "3", "4"):
        table.add_row([value])
    table.table.setRangeSelected(QTableWidgetSelectionRange(0, 0, 0, 0), True)
    table.table.setRangeSelected(QTableWidgetSelectionRange(2, 0, 2, 0), True)
    table._remove_selected_rows()
    assert table.all_rows() == [["2"], ["4"]]


def test_remove_selected_rows_none_selected_is_noop(qapp: object) -> None:
    table = EditableTable(["A"])
    table.add_row(["1"])
    table._remove_selected_rows()
    assert table.all_rows() == [["1"]]
