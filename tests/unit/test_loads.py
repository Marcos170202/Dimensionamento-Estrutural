"""Testes unitarios de openstruct.domain.loads."""

from __future__ import annotations

import math

import numpy as np
import pytest

from openstruct.domain.dof import DOF
from openstruct.domain.elements.base import Element
from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.loads import (
    DistributedLoad,
    ElementLoad,
    Load,
    LoadCase,
    LoadCombination,
    NodalLoad,
    self_weight_loads,
)
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


class _NonFrame3DElement(Element):
    """Elemento minimo, NAO Element3D — so para testar a rejeicao de
    ``DistributedLoad.fixed_end_forces_local`` a tipos nao suportados
    nesta fase (ver docstring de ``DistributedLoad``)."""

    @property
    def num_dofs(self) -> int:
        return 2

    def local_stiffness_matrix(self) -> np.ndarray:
        return np.eye(2)

    def transformation_matrix(self) -> np.ndarray:
        return np.eye(2)


def _dof_index_2_nodes(node_id: int, dof: DOF) -> int:
    """Indexador de DOF simples para testes: no 1 -> [0..5], no 2 -> [6..11]."""
    base = 0 if node_id == 1 else 6
    return base + dof.value


def _axis_aligned_element(element_id: int = 1, length: float = 4000.0) -> Element3D:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, length, 0.0, 0.0)
    return Element3D(element_id, (n1, n2), STEEL, SECTION)


# -- NodalLoad ---------------------------------------------------------------


def test_nodal_load_stores_components() -> None:
    load = NodalLoad(1, fx=10.0, fy=-20.0, mz=5.0)
    assert load.components == (10.0, -20.0, 0.0, 0.0, 0.0, 5.0)


def test_nodal_load_rejects_negative_node_id() -> None:
    with pytest.raises(ValueError):
        NodalLoad(-1, fx=10.0)


def test_nodal_load_rejects_non_int_node_id() -> None:
    with pytest.raises(TypeError):
        NodalLoad(1.5, fx=10.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["fx", "fy", "fz", "mx", "my", "mz"])
def test_nodal_load_rejects_non_finite_components(field: str) -> None:
    with pytest.raises(ValueError):
        NodalLoad(1, **{field: math.nan})


def test_nodal_load_is_a_load() -> None:
    assert isinstance(NodalLoad(1, fx=1.0), Load)


def test_nodal_load_apply_to_scatters_into_correct_global_indices() -> None:
    load = NodalLoad(2, fx=100.0, mz=50.0)
    f = np.zeros(12)
    load.apply_to(f, _dof_index_2_nodes)
    expected = np.zeros(12)
    expected[6] = 100.0  # no 2, UX
    expected[11] = 50.0  # no 2, RZ
    assert np.array_equal(f, expected)


def test_nodal_load_apply_to_accumulates_on_existing_values() -> None:
    f = np.zeros(12)
    NodalLoad(1, fy=10.0).apply_to(f, _dof_index_2_nodes)
    NodalLoad(1, fy=5.0).apply_to(f, _dof_index_2_nodes)
    assert f[1] == pytest.approx(15.0)


def test_nodal_load_all_zero_is_allowed_and_no_op() -> None:
    f = np.zeros(12)
    NodalLoad(1).apply_to(f, _dof_index_2_nodes)
    assert np.array_equal(f, np.zeros(12))


# -- LoadCase ------------------------------------------------------------


def test_load_case_stores_loads() -> None:
    l1 = NodalLoad(1, fx=1.0)
    l2 = NodalLoad(2, fy=2.0)
    case = LoadCase("Permanente", (l1, l2))
    assert case.loads == (l1, l2)


def test_load_case_rejects_blank_name() -> None:
    with pytest.raises(ValueError):
        LoadCase("   ")


def test_load_case_rejects_non_load_items() -> None:
    with pytest.raises(TypeError):
        LoadCase("X", ("not-a-load",))  # type: ignore[arg-type]


def test_load_case_default_has_no_loads() -> None:
    case = LoadCase("Vazio")
    assert case.loads == ()


def test_load_case_apply_to_sums_all_loads() -> None:
    case = LoadCase(
        "Combinado",
        (NodalLoad(1, fx=10.0), NodalLoad(2, fy=-5.0)),
    )
    f = np.zeros(12)
    case.apply_to(f, _dof_index_2_nodes)
    expected = np.zeros(12)
    expected[0] = 10.0
    expected[7] = -5.0
    assert np.array_equal(f, expected)


def test_load_case_is_hashable() -> None:
    case = LoadCase("X", (NodalLoad(1, fx=1.0),))
    assert isinstance(hash(case), int)


# -- LoadCombination -------------------------------------------------------


def test_load_combination_rejects_blank_name() -> None:
    case = LoadCase("P", (NodalLoad(1, fx=1.0),))
    with pytest.raises(ValueError):
        LoadCombination("  ", {case: 1.0})


def test_load_combination_rejects_empty_factors() -> None:
    with pytest.raises(ValueError):
        LoadCombination("Vazia", {})


def test_load_combination_rejects_non_load_case_key() -> None:
    with pytest.raises(TypeError):
        LoadCombination("X", {"nao-e-load-case": 1.0})  # type: ignore[dict-item]


def test_load_combination_rejects_non_finite_factor() -> None:
    case = LoadCase("P", (NodalLoad(1, fx=1.0),))
    with pytest.raises(ValueError):
        LoadCombination("X", {case: math.nan})


def test_load_combination_applies_scaled_sum_of_cases() -> None:
    permanente = LoadCase("Permanente", (NodalLoad(1, fy=-100.0),))
    vento = LoadCase("Vento", (NodalLoad(2, fx=50.0),))
    combo = LoadCombination("ELU-1", {permanente: 1.4, vento: 1.0})

    f = np.zeros(12)
    combo.apply_to(f, _dof_index_2_nodes)

    expected = np.zeros(12)
    expected[1] = -140.0  # 1.4 * -100
    expected[6] = 50.0  # 1.0 * 50
    assert np.allclose(f, expected)


def test_load_combination_does_not_mutate_load_case_when_applied_twice() -> None:
    case = LoadCase("P", (NodalLoad(1, fx=10.0),))
    combo = LoadCombination("C", {case: 2.0})

    f1 = np.zeros(12)
    combo.apply_to(f1, _dof_index_2_nodes)
    f2 = np.zeros(12)
    combo.apply_to(f2, _dof_index_2_nodes)

    assert np.allclose(f1, f2)
    assert f1[0] == pytest.approx(20.0)


def test_load_combination_dimensions_are_immutable() -> None:
    case = LoadCase("P", (NodalLoad(1, fx=1.0),))
    combo = LoadCombination("C", {case: 1.0})
    with pytest.raises(TypeError):
        combo.factors[case] = 5.0  # type: ignore[index]


# -- DistributedLoad -------------------------------------------------------


def test_distributed_load_stores_fields() -> None:
    load = DistributedLoad(1, wx=1.0, wy=-2.0, wz=3.0)
    assert (load.element_id, load.wx, load.wy, load.wz) == (1, 1.0, -2.0, 3.0)


def test_distributed_load_is_an_element_load() -> None:
    assert isinstance(DistributedLoad(1, wy=1.0), ElementLoad)
    assert not isinstance(DistributedLoad(1, wy=1.0), Load)


def test_distributed_load_rejects_negative_element_id() -> None:
    with pytest.raises(ValueError):
        DistributedLoad(-1, wy=1.0)


def test_distributed_load_rejects_non_int_element_id() -> None:
    with pytest.raises(TypeError):
        DistributedLoad(1.5, wy=1.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["wx", "wy", "wz"])
def test_distributed_load_rejects_non_finite_components(field: str) -> None:
    with pytest.raises(ValueError):
        DistributedLoad(1, **{field: math.nan})


def test_distributed_load_fixed_end_forces_rejects_wrong_element() -> None:
    load = DistributedLoad(1, wy=5.0)
    other_element = _axis_aligned_element(element_id=2)
    with pytest.raises(ValueError):
        load.fixed_end_forces_local(other_element)


def test_distributed_load_fixed_end_forces_rejects_non_element3d() -> None:
    load = DistributedLoad(1, wy=5.0)
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    other = _NonFrame3DElement(1, (n1, n2), STEEL, SECTION)
    with pytest.raises(TypeError):
        load.fixed_end_forces_local(other)


def test_distributed_load_fixed_end_forces_axial() -> None:
    length = 4000.0
    element = _axis_aligned_element(length=length)
    load = DistributedLoad(1, wx=2.0)
    fef = load.fixed_end_forces_local(element)
    expected = np.zeros(12)
    expected[0] = expected[6] = 2.0 * length / 2.0
    assert np.allclose(fef, expected)


def test_distributed_load_fixed_end_forces_bending_y_direction() -> None:
    """Par UY/RZ: f = [wL/2, wL^2/12, wL/2, -wL^2/12] (ver docstring de DistributedLoad)."""
    length = 4000.0
    w = 5.0
    element = _axis_aligned_element(length=length)
    load = DistributedLoad(1, wy=w)
    fef = load.fixed_end_forces_local(element)
    expected = np.zeros(12)
    expected[1] = w * length / 2.0
    expected[5] = w * length**2 / 12.0
    expected[7] = w * length / 2.0
    expected[11] = -(w * length**2 / 12.0)
    assert np.allclose(fef, expected)


def test_distributed_load_fixed_end_forces_bending_z_direction_has_flipped_moment_sign() -> None:
    """Par UZ/RY: sinal do termo de momento invertido em relacao ao par UY/RZ."""
    length = 4000.0
    w = 5.0
    element = _axis_aligned_element(length=length)
    load = DistributedLoad(1, wz=w)
    fef = load.fixed_end_forces_local(element)
    expected = np.zeros(12)
    expected[2] = w * length / 2.0
    expected[4] = -(w * length**2 / 12.0)
    expected[8] = w * length / 2.0
    expected[10] = w * length**2 / 12.0
    assert np.allclose(fef, expected)


def test_distributed_load_apply_to_axis_aligned_element_scatters_correctly() -> None:
    # Elemento alinhado com X -> transformation_matrix() == identidade
    # (ver VAL-0001), entao equivalente global == equivalente local.
    length = 4000.0
    element = _axis_aligned_element(length=length)
    load = DistributedLoad(1, wy=5.0)

    def dof_index(node_id: int, dof: DOF) -> int:
        base = 0 if node_id == 1 else 6
        return base + dof.value

    f_global = np.zeros(12)
    load.apply_to(f_global, element, dof_index)
    assert np.allclose(f_global, load.fixed_end_forces_local(element))


# -- LoadCase.element_loads -------------------------------------------------


def test_load_case_stores_element_loads() -> None:
    dload = DistributedLoad(1, wy=5.0)
    case = LoadCase("Permanente", element_loads=(dload,))
    assert case.element_loads == (dload,)


def test_load_case_rejects_non_element_load_items() -> None:
    with pytest.raises(TypeError):
        LoadCase("X", element_loads=("not-an-element-load",))  # type: ignore[arg-type]


def test_load_case_apply_to_requires_elements_mapping_for_element_loads() -> None:
    case = LoadCase("X", element_loads=(DistributedLoad(1, wy=5.0),))
    f = np.zeros(12)
    with pytest.raises(KeyError):
        case.apply_to(f, _dof_index_2_nodes)  # sem `elements` -> mapeamento vazio


def test_load_case_apply_to_with_element_loads_scatters_via_transformation() -> None:
    element = _axis_aligned_element()
    case = LoadCase("X", element_loads=(DistributedLoad(1, wy=5.0),))
    f = np.zeros(12)
    case.apply_to(f, _dof_index_2_nodes, elements={1: element})
    assert np.allclose(f, DistributedLoad(1, wy=5.0).fixed_end_forces_local(element))


def test_load_case_fixed_end_forces_local_for_sums_matching_element_loads() -> None:
    element = _axis_aligned_element(element_id=1)
    other_element = _axis_aligned_element(element_id=2)
    case = LoadCase(
        "X",
        element_loads=(DistributedLoad(1, wy=5.0), DistributedLoad(2, wy=99.0)),
    )
    fef = case.fixed_end_forces_local_for(element)
    assert np.allclose(fef, DistributedLoad(1, wy=5.0).fixed_end_forces_local(element))
    # a carga do OUTRO elemento nao deve contaminar este resultado
    assert not np.allclose(fef, DistributedLoad(2, wy=99.0).fixed_end_forces_local(other_element))


def test_load_case_fixed_end_forces_local_for_is_zero_without_element_loads() -> None:
    element = _axis_aligned_element()
    case = LoadCase("X", (NodalLoad(1, fx=10.0),))
    assert np.array_equal(case.fixed_end_forces_local_for(element), np.zeros(12))


def test_load_combination_fixed_end_forces_local_for_scales_by_factor() -> None:
    element = _axis_aligned_element()
    case = LoadCase("X", element_loads=(DistributedLoad(1, wy=5.0),))
    combo = LoadCombination("C", {case: 2.0})
    expected = 2.0 * case.fixed_end_forces_local_for(element)
    assert np.allclose(combo.fixed_end_forces_local_for(element), expected)


# -- self_weight_loads -----------------------------------------------------


def _model_with_single_element(n1: Node, n2: Node) -> AnalysisModel:
    model = AnalysisModel()
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    return model


def test_self_weight_loads_empty_model_returns_empty_tuple() -> None:
    assert self_weight_loads(AnalysisModel()) == ()


def test_self_weight_loads_one_per_element() -> None:
    model = _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    loads = self_weight_loads(model)
    assert len(loads) == 1
    assert all(isinstance(load, DistributedLoad) for load in loads)
    assert loads[0].element_id == 1


def test_self_weight_loads_horizontal_beam_is_purely_transverse() -> None:
    """Viga horizontal (eixo local x = eixo global X): peso proprio vira
    carga transversal pura no eixo local z (gravidade = -Z global)."""
    model = _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    load = self_weight_loads(model)[0]
    expected_w = -(STEEL.density * SECTION.A * 9.81)
    assert load.wx == pytest.approx(0.0, abs=1e-15)
    assert load.wy == pytest.approx(0.0, abs=1e-15)
    assert load.wz == pytest.approx(expected_w)


def test_self_weight_loads_vertical_column_is_purely_axial() -> None:
    """Coluna vertical (eixo local x paralelo a gravidade): peso vira
    carga axial pura (compressao), sem componente de flexao."""
    model = _model_with_single_element(Node(1, 0.0, 0.0, 4000.0), Node(2, 0.0, 0.0, 0.0))
    load = self_weight_loads(model)[0]
    # local_x aponta para -Z (mesmo sentido da gravidade)
    expected_w = STEEL.density * SECTION.A * 9.81
    assert load.wx == pytest.approx(expected_w)
    assert load.wy == pytest.approx(0.0, abs=1e-15)
    assert load.wz == pytest.approx(0.0, abs=1e-15)


def test_self_weight_loads_magnitude_independent_of_orientation() -> None:
    """A intensidade RESULTANTE (norma do vetor local) nao deve depender
    da orientacao do elemento — so a distribuicao entre wx/wy/wz muda."""
    horizontal = self_weight_loads(
        _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    )[0]
    vertical = self_weight_loads(
        _model_with_single_element(Node(1, 0.0, 0.0, 4000.0), Node(2, 0.0, 0.0, 0.0))
    )[0]
    inclined = self_weight_loads(
        _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 3000.0, 0.0, 4000.0))
    )[0]
    for load in (horizontal, vertical, inclined):
        norm = math.sqrt(load.wx**2 + load.wy**2 + load.wz**2)
        assert norm == pytest.approx(STEEL.density * SECTION.A * 9.81)


def test_self_weight_loads_rejects_non_positive_gravity() -> None:
    model = _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        self_weight_loads(model, gravity=0.0)
    with pytest.raises(ValueError):
        self_weight_loads(model, gravity=-9.81)


def test_self_weight_loads_rejects_non_finite_gravity() -> None:
    model = _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        self_weight_loads(model, gravity=math.nan)


def test_self_weight_loads_rejects_zero_direction() -> None:
    model = _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        self_weight_loads(model, direction=(0.0, 0.0, 0.0))


def test_self_weight_loads_rejects_malformed_direction() -> None:
    model = _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        self_weight_loads(model, direction=(1.0, 0.0))  # type: ignore[arg-type]


def test_self_weight_loads_direction_does_not_need_to_be_unit_vector() -> None:
    model = _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    load_unit = self_weight_loads(model, direction=(0.0, 0.0, -1.0))[0]
    load_scaled = self_weight_loads(model, direction=(0.0, 0.0, -100.0))[0]
    assert load_unit.wz == pytest.approx(load_scaled.wz)


def test_self_weight_loads_rejects_non_element3d() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(_NonFrame3DElement(1, (n1, n2), STEEL, SECTION))
    with pytest.raises(TypeError):
        self_weight_loads(model)


def test_self_weight_loads_scales_linearly_with_area() -> None:
    section_2x = Section(
        name="Sec2x", A=2 * SECTION.A, Iy=SECTION.Iy, Iz=SECTION.Iz, J=SECTION.J,
        Wply=SECTION.Wply, Wplz=SECTION.Wplz, Wely=SECTION.Wely, Welz=SECTION.Welz,
    )
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    model = AnalysisModel()
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, section_2x))
    load = self_weight_loads(model)[0]
    reference = self_weight_loads(
        _model_with_single_element(Node(1, 0.0, 0.0, 0.0), Node(2, 4000.0, 0.0, 0.0))
    )[0]
    assert load.wz == pytest.approx(2.0 * reference.wz)
