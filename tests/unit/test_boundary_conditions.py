"""Testes unitarios de openstruct.analysis.boundary_conditions."""

from __future__ import annotations

import numpy as np
import pytest

from openstruct.analysis.assembly import Assembly
from openstruct.analysis.boundary_conditions import (
    BoundaryConditions,
    ModelInstabilityError,
)
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


def _cantilever_model(support: Support | None) -> AnalysisModel:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    if support is not None:
        model.add_support(support)
    return model


def test_restrained_dof_indices_for_fixed_support() -> None:
    model = _cantilever_model(Support.fixed(1))
    bc = BoundaryConditions(model)
    assert bc.restrained_dof_indices() == [0, 1, 2, 3, 4, 5]


def test_free_dof_indices_is_complement_of_restrained() -> None:
    model = _cantilever_model(Support.fixed(1))
    bc = BoundaryConditions(model)
    assert bc.free_dof_indices() == [6, 7, 8, 9, 10, 11]


def test_restrained_dof_indices_for_partial_support() -> None:
    model = _cantilever_model(support=Support(1, ux=True, uy=True, uz=True))
    bc = BoundaryConditions(model)
    assert bc.restrained_dof_indices() == [0, 1, 2]
    assert bc.free_dof_indices() == [3, 4, 5, 6, 7, 8, 9, 10, 11]


def test_partition_returns_correct_shapes() -> None:
    model = _cantilever_model(Support.fixed(1))
    assembly = Assembly(model)
    k_global = assembly.global_stiffness_matrix()
    f_global = np.zeros(12)
    bc = BoundaryConditions(model)
    k_ff, f_f, free, restrained = bc.partition(k_global, f_global)
    assert k_ff.shape == (6, 6)
    assert f_f.shape == (6,)
    assert free == [6, 7, 8, 9, 10, 11]
    assert restrained == [0, 1, 2, 3, 4, 5]


def test_partition_k_ff_matches_manual_submatrix() -> None:
    model = _cantilever_model(Support.fixed(1))
    k_global = Assembly(model).global_stiffness_matrix()
    f_global = np.zeros(12)
    bc = BoundaryConditions(model)
    k_ff, _f_f, free, _restrained = bc.partition(k_global, f_global)
    assert np.allclose(k_ff, k_global[np.ix_(free, free)])


def test_partition_raises_when_no_supports_at_all() -> None:
    # Elemento livre no espaco: 6 modos de corpo rigido -> K_ff (=K_global
    # inteira, pois nao ha nenhum DOF restrito) e singular.
    model = _cantilever_model(support=None)
    k_global = Assembly(model).global_stiffness_matrix()
    f_global = np.zeros(12)
    bc = BoundaryConditions(model)
    with pytest.raises(ModelInstabilityError):
        bc.partition(k_global, f_global)


def test_partition_raises_when_support_insufficient_to_prevent_mechanism() -> None:
    # So UX restringido no no 1 -> ainda sobra mecanismo (o elemento
    # pode girar/transladar livremente nas demais direcoes).
    model = _cantilever_model(support=Support(1, ux=True))
    k_global = Assembly(model).global_stiffness_matrix()
    f_global = np.zeros(12)
    bc = BoundaryConditions(model)
    with pytest.raises(ModelInstabilityError):
        bc.partition(k_global, f_global)


def test_partition_raises_when_no_free_dofs_remain() -> None:
    model = _cantilever_model(support=None)
    model.add_support(Support.fixed(1))
    model.add_support(Support.fixed(2))
    k_global = Assembly(model).global_stiffness_matrix()
    f_global = np.zeros(12)
    bc = BoundaryConditions(model)
    with pytest.raises(ModelInstabilityError):
        bc.partition(k_global, f_global)


def test_fully_fixed_at_both_ends_is_stable_but_has_no_free_dof() -> None:
    # Caso limite documentado por test_partition_raises_when_no_free_dofs_remain:
    # nao e uma falha de MODELAGEM, mas nao ha nada a resolver — o
    # comportamento (levantar ModelInstabilityError) e o esperado e
    # documentado, nao um bug.
    model = _cantilever_model(support=None)
    model.add_support(Support.fixed(1))
    model.add_support(Support.fixed(2))
    bc = BoundaryConditions(model)
    assert bc.free_dof_indices() == []
