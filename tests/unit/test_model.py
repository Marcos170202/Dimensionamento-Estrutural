"""Testes unitarios de openstruct.domain.model.AnalysisModel."""

from __future__ import annotations

import pytest

from openstruct.domain.dof import DOF, DOFS_PER_NODE
from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.material import Material
from openstruct.domain.model import AnalysisModel
from openstruct.domain.node import Node
from openstruct.domain.section import Section
from openstruct.domain.support import Support

STEEL = Material(
    name="Steel", E=200000.0, G=77000.0, density=7.85e-6, fy=345.0, fu=450.0, poisson=0.3
)
SECTION = Section(
    name="Sec1", A=2680.0, Iy=3.79e6, Iz=37.0e6, J=52.8e3,
    Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3,
)


def test_add_node_and_lookup() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    model.add_node(n1)
    assert model.nodes[1] is n1
    assert len(model.nodes) == 1


def test_add_node_rejects_duplicate_id() -> None:
    model = AnalysisModel()
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        model.add_node(Node(1, 1.0, 1.0, 1.0))


def test_num_dofs_scales_with_node_count() -> None:
    model = AnalysisModel()
    assert model.num_dofs == 0
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    assert model.num_dofs == DOFS_PER_NODE
    model.add_node(Node(2, 1.0, 0.0, 0.0))
    assert model.num_dofs == 2 * DOFS_PER_NODE


def test_dof_index_uses_insertion_order_not_node_id() -> None:
    model = AnalysisModel()
    # ids inseridos fora de ordem (5 antes de 2) -> a numeracao global
    # segue a ORDEM DE INSERCAO, nao o valor do id.
    model.add_node(Node(5, 0.0, 0.0, 0.0))
    model.add_node(Node(2, 1.0, 0.0, 0.0))
    assert model.dof_index(5, DOF.UX) == 0
    assert model.dof_index(2, DOF.UX) == 6
    assert model.dof_index(2, DOF.RZ) == 11


def test_dof_index_raises_for_unknown_node() -> None:
    model = AnalysisModel()
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    with pytest.raises(KeyError):
        model.dof_index(999, DOF.UX)


def test_node_dof_indices_returns_six_consecutive_indices() -> None:
    model = AnalysisModel()
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    model.add_node(Node(2, 1.0, 0.0, 0.0))
    assert model.node_dof_indices(2) == [6, 7, 8, 9, 10, 11]


def test_node_dof_indices_raises_for_unknown_node() -> None:
    model = AnalysisModel()
    with pytest.raises(KeyError):
        model.node_dof_indices(1)


def test_add_element_requires_nodes_already_in_model() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    element = Element3D(1, (n1, n2), STEEL, SECTION)
    # nenhum no foi adicionado ainda
    with pytest.raises(ValueError):
        model.add_element(element)


def test_add_element_rejects_diverging_node_instance_with_same_id() -> None:
    model = AnalysisModel()
    n1_model = Node(1, 0.0, 0.0, 0.0)
    n2_model = Node(2, 1000.0, 0.0, 0.0)
    model.add_node(n1_model)
    model.add_node(n2_model)

    # mesmo id (2), instancia DIFERENTE com coordenadas divergentes
    n2_divergent = Node(2, 9999.0, 9999.0, 9999.0)
    element = Element3D(1, (n1_model, n2_divergent), STEEL, SECTION)
    with pytest.raises(ValueError):
        model.add_element(element)


def test_add_element_succeeds_with_registered_node_instances() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    element = Element3D(1, (n1, n2), STEEL, SECTION)
    model.add_element(element)
    assert model.elements[1] is element


def test_add_element_rejects_duplicate_id() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    with pytest.raises(ValueError):
        model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))


def test_add_support_requires_node_in_model() -> None:
    model = AnalysisModel()
    with pytest.raises(ValueError):
        model.add_support(Support.fixed(1))


def test_add_support_rejects_duplicate_for_same_node() -> None:
    model = AnalysisModel()
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    model.add_support(Support.fixed(1))
    with pytest.raises(ValueError):
        model.add_support(Support.pinned(1))


def test_add_support_succeeds_and_is_readable() -> None:
    model = AnalysisModel()
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    support = Support.fixed(1)
    model.add_support(support)
    assert model.supports[1] is support


def test_nodes_elements_supports_views_are_read_only() -> None:
    model = AnalysisModel()
    model.add_node(Node(1, 0.0, 0.0, 0.0))
    with pytest.raises(TypeError):
        model.nodes[2] = Node(2, 0.0, 0.0, 0.0)  # type: ignore[index]
