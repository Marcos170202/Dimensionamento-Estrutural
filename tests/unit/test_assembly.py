"""Testes unitarios de openstruct.analysis.assembly.Assembly."""

from __future__ import annotations

import numpy as np

from openstruct.analysis.assembly import Assembly
from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.loads import DistributedLoad, LoadCase, NodalLoad
from openstruct.domain.material import Material
from openstruct.domain.model import AnalysisModel
from openstruct.domain.node import Node
from openstruct.domain.section import Section

STEEL = Material(
    name="Steel", E=200000.0, G=77000.0, density=7.85e-6, fy=345.0, fu=450.0, poisson=0.3
)
SECTION = Section(
    name="Sec1", A=2680.0, Iy=3.79e6, Iz=37.0e6, J=52.8e3,
    Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3,
)


def _single_element_model() -> tuple[AnalysisModel, Element3D]:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    element = Element3D(1, (n1, n2), STEEL, SECTION)
    model.add_element(element)
    return model, element


def test_element_dof_indices_matches_insertion_order() -> None:
    model, element = _single_element_model()
    assembly = Assembly(model)
    assert assembly.element_dof_indices(element) == list(range(12))


def test_global_stiffness_matrix_single_element_equals_element_global_matrix() -> None:
    model, element = _single_element_model()
    assembly = Assembly(model)
    k_global = assembly.global_stiffness_matrix()
    assert k_global.shape == (12, 12)
    assert np.allclose(k_global, element.global_stiffness_matrix())


def test_global_stiffness_matrix_is_symmetric_for_multi_element_model() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    n3 = Node(3, 4000.0, 0.0, 3000.0)
    for n in (n1, n2, n3):
        model.add_node(n)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_element(Element3D(2, (n2, n3), STEEL, SECTION))

    k_global = Assembly(model).global_stiffness_matrix()
    assert k_global.shape == (18, 18)
    assert np.allclose(k_global, k_global.T)


def test_shared_node_accumulates_contributions_from_both_elements() -> None:
    # No 2 e compartilhado por 2 elementos -> o bloco 6x6 de K_global
    # referente ao no 2 deve ser a SOMA das contribuicoes dos dois
    # elementos (regra basica de montagem por sobreposicao).
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    n3 = Node(3, 8000.0, 0.0, 0.0)
    for n in (n1, n2, n3):
        model.add_node(n)
    el1 = Element3D(1, (n1, n2), STEEL, SECTION)
    el2 = Element3D(2, (n2, n3), STEEL, SECTION)
    model.add_element(el1)
    model.add_element(el2)

    k_global = Assembly(model).global_stiffness_matrix()
    # bloco do no 2 (indices 6..11): contribuicao do "no j" de el1 +
    # contribuicao do "no i" de el2.
    block_from_el1 = el1.global_stiffness_matrix()[6:12, 6:12]
    block_from_el2 = el2.global_stiffness_matrix()[0:6, 0:6]
    expected_block = block_from_el1 + block_from_el2
    assert np.allclose(k_global[6:12, 6:12], expected_block)


def test_global_load_vector_scatters_nodal_load() -> None:
    model, _element = _single_element_model()
    assembly = Assembly(model)
    case = LoadCase("P", (NodalLoad(2, fy=-1000.0, mz=500.0),))
    f_global = assembly.global_load_vector(case)
    expected = np.zeros(12)
    expected[7] = -1000.0
    expected[11] = 500.0
    assert np.array_equal(f_global, expected)


def test_global_load_vector_has_correct_length() -> None:
    model, _element = _single_element_model()
    f_global = Assembly(model).global_load_vector(LoadCase("Vazio"))
    assert f_global.shape == (12,)
    assert np.array_equal(f_global, np.zeros(12))


def test_global_load_vector_resolves_element_load_via_model_elements() -> None:
    # Assembly passa model.elements para que DistributedLoad (que so
    # guarda um element_id) consiga encontrar o Element3D de verdade.
    model, element = _single_element_model()
    case = LoadCase("UDL", element_loads=(DistributedLoad(1, wy=5.0),))
    f_global = Assembly(model).global_load_vector(case)
    assert np.allclose(f_global, DistributedLoad(1, wy=5.0).fixed_end_forces_local(element))
