"""Testes unitarios de openstruct.domain.node."""

import math

import pytest

from openstruct.domain.dof import DOF
from openstruct.domain.node import Node


def test_node_stores_id_and_coordinates() -> None:
    n = Node(1, 10.0, 20.0, 30.0)
    assert n.id == 1
    assert n.x == 10.0
    assert n.y == 20.0
    assert n.z == 30.0
    assert n.coordinates == (10.0, 20.0, 30.0)


def test_node_accepts_int_like_coordinates() -> None:
    n = Node(1, 0, 0, 0)
    assert n.x == 0.0 and isinstance(n.x, float)


@pytest.mark.parametrize("bad_id", [-1, -100])
def test_node_rejects_negative_id(bad_id: int) -> None:
    with pytest.raises(ValueError):
        Node(bad_id, 0.0, 0.0, 0.0)


def test_node_rejects_non_int_id() -> None:
    with pytest.raises(TypeError):
        Node(1.5, 0.0, 0.0, 0.0)  # type: ignore[arg-type]


def test_node_rejects_bool_id() -> None:
    # bool e subclasse de int em Python; sem esse guard, Node(True, ...)
    # silenciosamente criaria um no com id=1.
    with pytest.raises(TypeError):
        Node(True, 0.0, 0.0, 0.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
def test_node_rejects_non_finite_coordinates(bad_value: float) -> None:
    with pytest.raises(ValueError):
        Node(1, bad_value, 0.0, 0.0)


def test_node_dofs_returns_six_canonical_dofs() -> None:
    n = Node(1, 0.0, 0.0, 0.0)
    assert n.dofs == (DOF.UX, DOF.UY, DOF.UZ, DOF.RX, DOF.RY, DOF.RZ)


def test_node_distance_to() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 3.0, 4.0, 0.0)
    assert n1.distance_to(n2) == pytest.approx(5.0)
    assert n1.distance_to(n2) == n2.distance_to(n1)


def test_node_distance_to_self_is_zero() -> None:
    n = Node(1, 1.0, 2.0, 3.0)
    assert n.distance_to(n) == 0.0


def test_node_equality_and_hash_are_by_id_only() -> None:
    a = Node(1, 0.0, 0.0, 0.0)
    b = Node(1, 999.0, 999.0, 999.0)  # mesmo id, coordenadas diferentes
    c = Node(2, 0.0, 0.0, 0.0)
    assert a == b
    assert hash(a) == hash(b)
    assert a != c
    assert a in {b}  # confirma que o hash tambem trata a==b


def test_node_not_equal_to_other_type() -> None:
    n = Node(1, 0.0, 0.0, 0.0)
    assert n != "not-a-node"
    assert n.__eq__("not-a-node") is NotImplemented


def test_node_repr_contains_id_and_coordinates() -> None:
    n = Node(7, 1.0, 2.0, 3.0)
    text = repr(n)
    assert "7" in text and "1.0" in text and "2.0" in text and "3.0" in text
