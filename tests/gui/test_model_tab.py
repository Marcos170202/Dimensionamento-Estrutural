"""Testes de ``openstruct.gui.model_tab``."""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtWidgets import QMessageBox

from openstruct.gui.model_tab import (
    ModelInputError,
    ModelTab,
    _parse_bool,
    _parse_float,
    _parse_int,
)

# -- helpers de parsing -------------------------------------------------------


def test_parse_float_accepts_dot() -> None:
    assert _parse_float("1.5", field="X", table="Nós", row=0) == 1.5


def test_parse_float_accepts_comma_as_decimal_separator() -> None:
    assert _parse_float("1,5", field="X", table="Nós", row=0) == 1.5


def test_parse_float_invalid_raises_model_input_error_with_context() -> None:
    with pytest.raises(ModelInputError) as excinfo:
        _parse_float("abc", field="X", table="Nós", row=2)
    message = str(excinfo.value)
    assert "Nós" in message
    assert "linha 3" in message
    assert "X" in message


def test_parse_int_valid() -> None:
    assert _parse_int("42", field="ID", table="Nós", row=0) == 42


def test_parse_int_invalid_raises_model_input_error_with_context() -> None:
    with pytest.raises(ModelInputError) as excinfo:
        _parse_int("abc", field="ID", table="Elementos", row=1)
    message = str(excinfo.value)
    assert "Elementos" in message
    assert "linha 2" in message
    assert "ID" in message


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1", True),
        ("true", True),
        ("True", True),
        ("verdadeiro", True),
        ("sim", True),
        ("S", True),
        ("x", True),
        ("X", True),
        ("0", False),
        ("false", False),
        ("nao", False),
        ("", False),
        ("  ", False),
    ],
)
def test_parse_bool(text: str, expected: bool) -> None:
    assert _parse_bool(text) is expected


# -- fixture: viga em balanco simples ------------------------------------------


def _fill_cantilever_beam(model_tab: ModelTab) -> None:
    """Preenche as tabelas com uma viga em balanco valida (2 nos, 1 elemento)."""
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.nodes_table.add_row(["2", "3000", "0", "0"])
    model_tab.materials_table.add_row(["Aco", "200000", "77000", "7.85e-9", "345", "450", "0.3"])
    model_tab.sections_table.add_row(
        ["W310x21", "2680", "3730000", "127000", "38700", "417000", "83900", "375000", "53100", ""]
    )
    model_tab.elements_table.add_row(["1", "1", "2", "Aco", "W310x21"])
    model_tab.supports_table.add_row(["1", "1", "1", "1", "1", "1", "1"])
    model_tab.loads_table.add_row(["2", "0", "0", "-10000", "0", "0", "0"])


def test_build_model_and_load_case_valid_cantilever(qapp: object) -> None:
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)

    model, load_case = model_tab.build_model_and_load_case()

    assert len(model.nodes) == 2
    assert len(model.elements) == 1
    assert len(model.supports) == 1
    assert len(load_case.loads) == 1
    assert load_case.element_loads == ()


def test_build_model_and_load_case_section_cw_optional_when_blank(qapp: object) -> None:
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)
    model, _load_case = model_tab.build_model_and_load_case()
    section = next(iter(model.elements.values())).section
    assert section.Cw is None


def test_build_model_and_load_case_section_cw_parsed_when_given(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.nodes_table.add_row(["2", "3000", "0", "0"])
    model_tab.materials_table.add_row(["Aco", "200000", "77000", "7.85e-9", "345", "450", "0.3"])
    model_tab.sections_table.add_row(
        [
            "W310x21", "2680", "3730000", "127000", "38700",
            "417000", "83900", "375000", "53100", "1e9",
        ]
    )
    model_tab.elements_table.add_row(["1", "1", "2", "Aco", "W310x21"])
    model_tab.supports_table.add_row(["1", "1", "1", "1", "1", "1", "1"])
    model, _load_case = model_tab.build_model_and_load_case()
    section = next(iter(model.elements.values())).section
    assert section.Cw == 1e9


def test_build_model_and_load_case_self_weight_checked(qapp: object) -> None:
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)
    model_tab.self_weight_checkbox.setChecked(True)

    _model, load_case = model_tab.build_model_and_load_case()

    assert len(load_case.element_loads) == 1


def test_build_model_and_load_case_material_empty_name_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.materials_table.add_row(["", "200000", "77000", "7.85e-9", "345", "450", "0.3"])
    with pytest.raises(ModelInputError, match="Materiais"):
        model_tab.build_model_and_load_case()


def test_build_model_and_load_case_section_empty_name_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.sections_table.add_row(
        ["", "2680", "3730000", "127000", "38700", "417000", "83900", "375000", "53100", ""]
    )
    with pytest.raises(ModelInputError, match="Seções"):
        model_tab.build_model_and_load_case()


def test_build_model_and_load_case_element_references_missing_node_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.materials_table.add_row(["Aco", "200000", "77000", "7.85e-9", "345", "450", "0.3"])
    model_tab.sections_table.add_row(
        ["W310x21", "2680", "3730000", "127000", "38700", "417000", "83900", "375000", "53100", ""]
    )
    model_tab.elements_table.add_row(["1", "1", "99", "Aco", "W310x21"])
    with pytest.raises(ModelInputError, match="nó 1 ou 99 não existe"):
        model_tab.build_model_and_load_case()


def test_build_model_and_load_case_element_references_missing_material_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.nodes_table.add_row(["2", "3000", "0", "0"])
    model_tab.sections_table.add_row(
        ["W310x21", "2680", "3730000", "127000", "38700", "417000", "83900", "375000", "53100", ""]
    )
    model_tab.elements_table.add_row(["1", "1", "2", "Inexistente", "W310x21"])
    with pytest.raises(ModelInputError, match="material 'Inexistente' não existe"):
        model_tab.build_model_and_load_case()


def test_build_model_and_load_case_element_references_missing_section_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.nodes_table.add_row(["2", "3000", "0", "0"])
    model_tab.materials_table.add_row(["Aco", "200000", "77000", "7.85e-9", "345", "450", "0.3"])
    model_tab.elements_table.add_row(["1", "1", "2", "Aco", "Inexistente"])
    with pytest.raises(ModelInputError, match="seção 'Inexistente' não existe"):
        model_tab.build_model_and_load_case()


def test_build_model_and_load_case_support_references_missing_node_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.supports_table.add_row(["99", "1", "1", "1", "1", "1", "1"])
    with pytest.raises(ModelInputError, match="Apoios.*nó 99 não existe"):
        model_tab.build_model_and_load_case()


def test_build_model_and_load_case_load_references_missing_node_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.loads_table.add_row(["99", "0", "0", "-1000", "0", "0", "0"])
    with pytest.raises(ModelInputError, match="Cargas.*nó 99 não existe"):
        model_tab.build_model_and_load_case()


def test_build_model_and_load_case_invalid_node_field_raises(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["x", "0", "0", "0"])
    with pytest.raises(ModelInputError, match="Nós"):
        model_tab.build_model_and_load_case()


# -- construcao da janela / tabelas de resultado -------------------------------


def test_model_tab_builds_all_child_tables(qapp: object) -> None:
    model_tab = ModelTab()
    assert model_tab.displacements_table.columnCount() == 7
    assert model_tab.reactions_table.columnCount() == 7
    assert model_tab.element_forces_table.columnCount() == 13
    assert model_tab.results_tabs.count() == 3


# -- execucao da analise --------------------------------------------------------


def test_on_run_analysis_success_populates_result_tables(qapp: object) -> None:
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)

    model_tab._on_run_analysis()

    assert model_tab.displacements_table.rowCount() == 2
    assert model_tab.reactions_table.rowCount() == 1
    assert model_tab.element_forces_table.rowCount() == 1
    assert model_tab.displacements_table.item(0, 0).text() == "1"


def test_on_run_analysis_model_input_error_shows_dialog_and_keeps_tables_empty(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["x", "0", "0", "0"])

    captured: dict[str, Any] = {}

    def fake_critical(*args: Any, **kwargs: Any) -> QMessageBox.StandardButton:
        captured["args"] = args
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)

    model_tab._on_run_analysis()

    assert "args" in captured
    assert model_tab.displacements_table.rowCount() == 0


def test_on_run_analysis_generic_exception_shows_dialog(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Modelo sem nenhum apoio -> matriz de rigidez singular -> excecao generica."""
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.nodes_table.add_row(["2", "3000", "0", "0"])
    model_tab.materials_table.add_row(["Aco", "200000", "77000", "7.85e-9", "345", "450", "0.3"])
    model_tab.sections_table.add_row(
        ["W310x21", "2680", "3730000", "127000", "38700", "417000", "83900", "375000", "53100", ""]
    )
    model_tab.elements_table.add_row(["1", "1", "2", "Aco", "W310x21"])
    model_tab.loads_table.add_row(["2", "0", "0", "-10000", "0", "0", "0"])
    # sem apoios -> modelo instavel

    captured: dict[str, Any] = {}

    def fake_critical(*args: Any, **kwargs: Any) -> QMessageBox.StandardButton:
        captured["args"] = args
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)

    model_tab._on_run_analysis()

    assert "args" in captured
    assert model_tab.displacements_table.rowCount() == 0
