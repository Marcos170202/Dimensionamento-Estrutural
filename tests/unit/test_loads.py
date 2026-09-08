"""Testes unitarios de openstruct.domain.loads."""

from __future__ import annotations

import math

import numpy as np
import pytest

from openstruct.domain.dof import DOF
from openstruct.domain.loads import Load, LoadCase, LoadCombination, NodalLoad


def _dof_index_2_nodes(node_id: int, dof: DOF) -> int:
    """Indexador de DOF simples para testes: no 1 -> [0..5], no 2 -> [6..11]."""
    base = 0 if node_id == 1 else 6
    return base + dof.value


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
