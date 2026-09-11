"""Testes de ``openstruct.gui.checks_tab``."""

from __future__ import annotations

import pytest

from openstruct.gui.checks_tab import ChecksTab, _combination_combo, _parse_float

# -- helper -------------------------------------------------------------------


def test_parse_float_accepts_comma() -> None:
    assert _parse_float("1,5", "campo") == 1.5


def test_parse_float_invalid_raises_value_error_with_field_name() -> None:
    with pytest.raises(ValueError, match="campo"):
        _parse_float("abc", "campo")


def test_combination_combo_has_three_options(qapp: object) -> None:
    combo = _combination_combo()
    assert combo.count() == 3


def test_checks_tab_has_five_pages(qapp: object) -> None:
    tab = ChecksTab()
    assert tab.selector.count() == 5
    assert tab.stack.count() == 5


def test_selector_change_switches_stack_page(qapp: object) -> None:
    tab = ChecksTab()
    tab.selector.setCurrentIndex(2)
    assert tab.stack.currentIndex() == 2


def test_check_page_combo_returns_the_combobox_widget(qapp: object) -> None:
    tab = ChecksTab()
    tension_page = tab.stack.widget(0)
    assert tension_page.combo("Classe de combinação") is tension_page.inputs[
        "Classe de combinação"
    ]


# -- 5.2 tracao -----------------------------------------------------------------


def test_tension_page_default_values_pass(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(0)
    page.run_button.click()
    assert "APROVADO" in page.result_label.text()
    assert "Erro" not in page.result_label.text()


def test_tension_page_invalid_input_shows_error(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(0)
    page.inputs["Nt,Sd — força axial de tração solicitante (N)"].setText("abc")
    page.run_button.click()
    assert "Erro" in page.result_label.text()


def test_tension_page_overloaded_shows_reprovado(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(0)
    page.inputs["Nt,Sd — força axial de tração solicitante (N)"].setText("900000")
    page.run_button.click()
    assert "REPROVADO" in page.result_label.text()


# -- 5.3 compressao ---------------------------------------------------------------


def test_compression_page_default_values_pass(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(1)
    page.run_button.click()
    assert "APROVADO" in page.result_label.text()


def test_compression_page_invalid_input_shows_error(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(1)
    page.inputs["Ag — área bruta (mm²)"].setText("abc")
    page.run_button.click()
    assert "Erro" in page.result_label.text()


# -- 5.4.3.1 cisalhamento -----------------------------------------------------------


def test_shear_page_default_values_pass(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(2)
    page.run_button.click()
    assert "APROVADO" in page.result_label.text()


def test_shear_page_without_stiffener_spacing_uses_none(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(2)
    page.inputs["a — espaçamento entre enrijecedores (mm, vazio = sem enrijecedores)"].setText("")
    page.run_button.click()
    assert "APROVADO" in page.result_label.text()


def test_shear_page_with_stiffener_spacing(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(2)
    page.inputs["a — espaçamento entre enrijecedores (mm, vazio = sem enrijecedores)"].setText(
        "500"
    )
    page.run_button.click()
    assert "APROVADO" in page.result_label.text()


def test_shear_page_invalid_input_shows_error(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(2)
    page.inputs["Vsd — força cortante solicitante (N)"].setText("abc")
    page.run_button.click()
    assert "Erro" in page.result_label.text()


# -- 5.4.2/Anexo D flexao ------------------------------------------------------------


def test_flexure_page_default_values_pass(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(3)
    page.run_button.click()
    assert "APROVADO" in page.result_label.text()


def test_flexure_page_welded_profile(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(3)
    page.checkbox("Perfil").setChecked(False)
    page.run_button.click()
    assert "Erro" not in page.result_label.text()


def test_flexure_page_invalid_input_shows_error(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(3)
    page.inputs["Msd — momento fletor solicitante, MAGNITUDE (N.mm)"].setText("abc")
    page.run_button.click()
    assert "Erro" in page.result_label.text()


def test_flexure_page_slender_web_shows_domain_error(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(3)
    page.inputs["h — altura livre da alma (mm)"].setText("5000")
    page.run_button.click()
    assert "Erro" in page.result_label.text()


# -- 5.5.1.2 combinacao N+M ------------------------------------------------------------


def test_combined_page_default_values_pass(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(4)
    page.run_button.click()
    assert "APROVADO" in page.result_label.text()


def test_combined_page_invalid_input_shows_error(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(4)
    page.inputs["Nsd — força axial solicitante, MAGNITUDE (N)"].setText("abc")
    page.run_button.click()
    assert "Erro" in page.result_label.text()


def test_combined_page_overloaded_shows_reprovado(qapp: object) -> None:
    tab = ChecksTab()
    page = tab.stack.widget(4)
    page.inputs["Nsd — força axial solicitante, MAGNITUDE (N)"].setText("790000")
    page.run_button.click()
    assert "REPROVADO" in page.result_label.text()
