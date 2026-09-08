"""Testes unitarios de openstruct.domain.support."""

import dataclasses

import pytest

from openstruct.domain.dof import DOF
from openstruct.domain.support import Support


def test_support_stores_node_id_and_flags() -> None:
    s = Support(1, ux=True, uy=True, uz=True)
    assert s.node_id == 1
    assert s.restrained_flags == (True, True, True, False, False, False)


def test_support_rejects_negative_node_id() -> None:
    with pytest.raises(ValueError):
        Support(-1, ux=True)


def test_support_rejects_non_int_node_id() -> None:
    with pytest.raises(TypeError):
        Support(1.0, ux=True)  # type: ignore[arg-type]


def test_support_rejects_bool_node_id() -> None:
    with pytest.raises(TypeError):
        Support(True, ux=True)  # type: ignore[arg-type]


def test_support_rejects_all_flags_false() -> None:
    with pytest.raises(ValueError):
        Support(1)  # nenhum DOF restringido


def test_support_is_restrained() -> None:
    s = Support(1, ux=True, rz=True)
    assert s.is_restrained(DOF.UX)
    assert s.is_restrained(DOF.RZ)
    assert not s.is_restrained(DOF.UY)
    assert not s.is_restrained(DOF.RX)


def test_support_restrained_dofs_canonical_order() -> None:
    s = Support(1, uz=True, ux=True, ry=True)
    assert s.restrained_dofs() == (DOF.UX, DOF.UZ, DOF.RY)


def test_support_fixed_restrains_all_six() -> None:
    s = Support.fixed(5)
    assert s.node_id == 5
    assert s.restrained_flags == (True, True, True, True, True, True)
    assert set(s.restrained_dofs()) == set(DOF)


def test_support_pinned_restrains_only_translations() -> None:
    s = Support.pinned(5)
    assert s.restrained_flags == (True, True, True, False, False, False)


def test_support_is_frozen() -> None:
    s = Support.fixed(1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.node_id = 2  # type: ignore[misc]


def test_support_equality_by_value() -> None:
    assert Support.fixed(1) == Support.fixed(1)
    assert Support.fixed(1) != Support.fixed(2)
    assert hash(Support.fixed(1)) == hash(Support.fixed(1))
