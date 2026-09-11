"""Testes de ``openstruct.gui.viewport_3d.Viewport3D``."""

from __future__ import annotations

from openstruct import run_analysis
from openstruct.domain import (
    AnalysisModel,
    Element3D,
    LoadCase,
    Material,
    NodalLoad,
    Node,
    Section,
    Support,
)
from openstruct.gui.model_tab import ModelTab
from openstruct.gui.viewport_3d import Viewport3D, _bounding_diagonal, _lines_polydata

_MATERIAL = Material(
    name="Aco", E=200000.0, G=77000.0, density=7.85e-9, fy=345.0, fu=450.0, poisson=0.3
)
_SECTION = Section(
    name="W310x21",
    A=2680.0,
    Iy=3730000.0,
    Iz=127000.0,
    J=38700.0,
    Wply=417000.0,
    Wplz=83900.0,
    Wely=375000.0,
    Welz=53100.0,
)


def _cantilever_model() -> AnalysisModel:
    model = AnalysisModel()
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    model.add_node(Node(2, 3000.0, 0.0, 0.0))
    model.add_element(Element3D(1, (model.nodes[1], model.nodes[2]), _MATERIAL, _SECTION))
    model.add_support(Support.fixed(1))
    return model


# -- helpers de geometria -------------------------------------------------------


def test_bounding_diagonal_empty_is_one() -> None:
    import numpy as np

    assert _bounding_diagonal(np.empty((0, 3))) == 1.0


def test_bounding_diagonal_computes_norm() -> None:
    import numpy as np

    points = np.array([[0.0, 0.0, 0.0], [3.0, 4.0, 0.0]])
    assert _bounding_diagonal(points) == 5.0


def test_bounding_diagonal_coincident_points_is_one() -> None:
    import numpy as np

    points = np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])
    assert _bounding_diagonal(points) == 1.0


def test_lines_polydata_no_connectivity_returns_points_only() -> None:
    import numpy as np

    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    mesh = _lines_polydata(points, [])
    assert mesh.n_points == 2
    assert mesh.n_lines == 0


def test_lines_polydata_with_connectivity() -> None:
    import numpy as np

    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0]])
    mesh = _lines_polydata(points, [(0, 1), (1, 2)])
    assert mesh.n_points == 3
    assert mesh.n_lines == 2


# -- Viewport3D -------------------------------------------------------------------


def test_viewport_construction(qapp: object) -> None:
    model_tab = ModelTab()
    viewport = Viewport3D(model_tab)
    assert viewport.status_label.text() == ""
    assert viewport.scale_spinbox.value() == 1.0
    assert not viewport.show_deformed_checkbox.isChecked()


def test_render_model_empty_model_does_not_crash(qapp: object) -> None:
    viewport = Viewport3D(ModelTab())
    viewport.render_model(AnalysisModel())
    assert viewport.status_label.text() == ""


def test_render_model_with_geometry(qapp: object) -> None:
    viewport = Viewport3D(ModelTab())
    viewport.render_model(_cantilever_model())
    assert viewport.status_label.text() == ""
    assert viewport.plotter.renderer.actors


def test_render_model_with_load_case_draws_arrow(qapp: object) -> None:
    model = _cantilever_model()
    load_case = LoadCase("P", (NodalLoad(2, fz=-10_000.0),))
    viewport = Viewport3D(ModelTab())

    viewport.render_model(model)  # sem load_case: estrutura + nos + apoios, sem seta
    n_actors_without_load = len(viewport.plotter.renderer.actors)

    viewport.render_model(model, load_case)  # com load_case: mesma cena + seta de carga
    assert len(viewport.plotter.renderer.actors) > n_actors_without_load


def test_render_model_load_with_zero_force_is_skipped(qapp: object) -> None:
    model = _cantilever_model()
    load_case = LoadCase("P", (NodalLoad(2, mx=1000.0),))  # so momento, forca nula
    viewport = Viewport3D(ModelTab())
    viewport.render_model(model, load_case)
    assert viewport.status_label.text() == ""


def test_render_model_load_referencing_missing_node_is_skipped(qapp: object) -> None:
    model = _cantilever_model()
    load_case = LoadCase("P", (NodalLoad(99, fz=-1000.0),))  # no 99 nao existe no modelo
    viewport = Viewport3D(ModelTab())
    viewport.render_model(model, load_case)  # nao deve levantar excecao
    assert viewport.status_label.text() == ""


def test_render_model_with_deformed_shape(qapp: object) -> None:
    model = _cantilever_model()
    load_case = LoadCase("P", (NodalLoad(2, fz=-10_000.0),))
    result = run_analysis(model, load_case)

    viewport = Viewport3D(ModelTab())
    viewport.show_deformed_checkbox.setChecked(True)
    viewport.scale_spinbox.setValue(100.0)
    viewport.render_model(model, load_case, result)
    assert viewport.status_label.text() == ""


def test_render_model_result_without_checkbox_checked_shows_only_undeformed(
    qapp: object,
) -> None:
    model = _cantilever_model()
    load_case = LoadCase("P", (NodalLoad(2, fz=-10_000.0),))
    result = run_analysis(model, load_case)

    viewport = Viewport3D(ModelTab())
    assert not viewport.show_deformed_checkbox.isChecked()
    viewport.render_model(model, load_case, result)  # nao deve desenhar a deformada
    assert viewport.status_label.text() == ""


def test_show_error_sets_status_label(qapp: object) -> None:
    viewport = Viewport3D(ModelTab())
    viewport.show_error("algo deu errado")
    assert "algo deu errado" in viewport.status_label.text()
    assert "Erro" in viewport.status_label.text()


# -- integracao com o botao "Atualizar visualizacao" -----------------------------


def _fill_cantilever_beam(model_tab: ModelTab) -> None:
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.nodes_table.add_row(["2", "3000", "0", "0"])
    model_tab.materials_table.add_row(["Aco", "200000", "77000", "7.85e-9", "345", "450", "0.3"])
    model_tab.sections_table.add_row(
        ["W310x21", "2680", "3730000", "127000", "38700", "417000", "83900", "375000", "53100", ""]
    )
    model_tab.elements_table.add_row(["1", "1", "2", "Aco", "W310x21"])
    model_tab.supports_table.add_row(["1", "1", "1", "1", "1", "1", "1"])
    model_tab.loads_table.add_row(["2", "0", "0", "-10000", "0", "0", "0"])


def test_refresh_button_renders_current_model_tab_state(qapp: object) -> None:
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)
    viewport = Viewport3D(model_tab)

    viewport._on_refresh()

    assert viewport.status_label.text() == ""


def test_refresh_button_shows_model_input_error(qapp: object) -> None:
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["x", "0", "0", "0"])  # ID invalido
    viewport = Viewport3D(model_tab)

    viewport._on_refresh()

    assert "Erro" in viewport.status_label.text()
    assert "ID" in viewport.status_label.text()


def test_refresh_button_shows_generic_exception_not_wrapped_as_model_input_error(
    qapp: object,
) -> None:
    """No duplicado -> ``AnalysisModel.add_node`` levanta ``ValueError`` puro
    (nao ``ModelInputError``) -> exercita o ramo generico de ``_on_refresh``."""
    model_tab = ModelTab()
    model_tab.nodes_table.add_row(["1", "0", "0", "0"])
    model_tab.nodes_table.add_row(["1", "1000", "0", "0"])  # ID 1 duplicado
    viewport = Viewport3D(model_tab)

    viewport._on_refresh()

    assert "Erro" in viewport.status_label.text()
    assert "id=1" in viewport.status_label.text()


def test_refresh_button_refuses_stale_deformed_shape_after_table_edit(qapp: object) -> None:
    """Tabelas editadas apos "Rodar Analise" invalidam a deformada
    cacheada — o viewport deve recusar sobrepor uma deformada que nao
    corresponde mais ao modelo/cargas atuais (achado do code-review)."""
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)
    viewport = Viewport3D(model_tab)

    model_tab._on_run_analysis()
    assert model_tab.last_result is not None
    assert not model_tab.is_last_result_stale()

    # edita uma tabela depois da analise -> last_result fica desatualizado
    model_tab.loads_table.add_row(["1", "1000", "0", "0", "0", "0", "0"])
    assert model_tab.is_last_result_stale()

    viewport.show_deformed_checkbox.setChecked(True)
    viewport._on_refresh()

    assert "NÃO desenhada" in viewport.status_label.text()
    assert "Rodar Análise" in viewport.status_label.text()


def test_refresh_button_shows_deformed_when_checkbox_off_even_if_stale(qapp: object) -> None:
    """Com o checkbox desmarcado, uma deformada desatualizada nao impede
    a atualizacao normal (so a sobreposicao da deformada e recusada)."""
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)
    viewport = Viewport3D(model_tab)

    model_tab._on_run_analysis()
    model_tab.loads_table.add_row(["1", "1000", "0", "0", "0", "0", "0"])
    assert model_tab.is_last_result_stale()

    assert not viewport.show_deformed_checkbox.isChecked()
    viewport._on_refresh()

    assert viewport.status_label.text() == ""


def test_refresh_button_after_analysis_can_show_deformed(qapp: object) -> None:
    model_tab = ModelTab()
    _fill_cantilever_beam(model_tab)
    viewport = Viewport3D(model_tab)

    model_tab._on_run_analysis()
    assert model_tab.last_result is not None

    viewport.show_deformed_checkbox.setChecked(True)
    viewport._on_refresh()

    assert viewport.status_label.text() == ""
