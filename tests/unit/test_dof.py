"""Testes unitarios de openstruct.domain.dof."""

from openstruct.domain.dof import DOF, DOFS_PER_NODE, NODE_DOF_ORDER


def test_dof_has_six_members() -> None:
    assert len(DOF) == 6


def test_dof_values_are_sequential_indices() -> None:
    assert [d.value for d in DOF] == [0, 1, 2, 3, 4, 5]


def test_dof_translation_members() -> None:
    assert DOF.UX.is_translation
    assert DOF.UY.is_translation
    assert DOF.UZ.is_translation
    assert not DOF.UX.is_rotation


def test_dof_rotation_members() -> None:
    assert DOF.RX.is_rotation
    assert DOF.RY.is_rotation
    assert DOF.RZ.is_rotation
    assert not DOF.RX.is_translation


def test_dofs_per_node_matches_enum_size() -> None:
    assert DOFS_PER_NODE == len(DOF)


def test_node_dof_order_is_canonical() -> None:
    assert NODE_DOF_ORDER == (DOF.UX, DOF.UY, DOF.UZ, DOF.RX, DOF.RY, DOF.RZ)


def test_dof_is_unique_enum() -> None:
    # @unique ja garante isso na definicao (levantaria ValueError na
    # importacao se houvesse alias); o teste documenta a garantia.
    values = [d.value for d in DOF]
    assert len(values) == len(set(values))
