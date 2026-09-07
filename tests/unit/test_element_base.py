"""Testes unitarios de openstruct.domain.elements.base.Element.

``Element`` e abstrata; usamos uma subclasse minima (``_DummyElement``)
apenas para exercitar o contrato comum (validacao de construtor e a
implementacao generica de ``global_stiffness_matrix()``). O elemento
concreto real (``Element3D``) tem sua propria suite de testes e de
validacao estrutural.
"""

from __future__ import annotations

import numpy as np
import pytest

from openstruct.domain.elements.base import Element
from openstruct.domain.material import Material
from openstruct.domain.node import Node
from openstruct.domain.section import Section

STEEL = Material(
    name="Steel", E=200000.0, G=77000.0, density=7.85e-6, fy=345.0, fu=450.0, poisson=0.3
)
SECTION = Section(
    name="Sec1", A=2680.0, Iy=3.79e6, Iz=37.0e6, J=52.8e3,
    Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3,
)


class _DummyElement(Element):
    """Elemento minimo (2 DOFs) so para testar o contrato da base.

    Usa uma matriz de rigidez local trivial (mola axial 1D) e uma
    transformacao identidade, o que basta para verificar que
    ``global_stiffness_matrix()`` aplica corretamente ``T.T @ K @ T``.
    """

    @property
    def num_dofs(self) -> int:
        return 2

    def local_stiffness_matrix(self) -> np.ndarray:
        k = 42.0
        return np.array([[k, -k], [-k, k]])

    def transformation_matrix(self) -> np.ndarray:
        return np.eye(2)


class _RotatedDummyElement(_DummyElement):
    """Mesma mola axial, mas com uma transformacao nao-trivial (rotacao 2D)."""

    def transformation_matrix(self) -> np.ndarray:
        theta = np.pi / 6
        c, s = np.cos(theta), np.sin(theta)
        return np.array([[c, s], [-s, c]])


def _nodes() -> tuple[Node, Node]:
    return (Node(1, 0.0, 0.0, 0.0), Node(2, 1000.0, 0.0, 0.0))


def test_element_stores_id_nodes_material_section() -> None:
    n1, n2 = _nodes()
    el = _DummyElement(1, (n1, n2), STEEL, SECTION)
    assert el.id == 1
    assert el.nodes == (n1, n2)
    assert el.material is STEEL
    assert el.section is SECTION


def test_element_rejects_negative_id() -> None:
    with pytest.raises(ValueError):
        _DummyElement(-1, _nodes(), STEEL, SECTION)


def test_element_rejects_non_int_id() -> None:
    with pytest.raises(TypeError):
        _DummyElement(1.0, _nodes(), STEEL, SECTION)  # type: ignore[arg-type]


def test_element_rejects_fewer_than_two_nodes() -> None:
    with pytest.raises(ValueError):
        _DummyElement(1, (Node(1, 0.0, 0.0, 0.0),), STEEL, SECTION)


def test_element_rejects_duplicate_node_ids() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n1_dup = Node(1, 1000.0, 0.0, 0.0)  # mesmo id, coordenadas diferentes
    with pytest.raises(ValueError):
        _DummyElement(1, (n1, n1_dup), STEEL, SECTION)


def test_element_rejects_non_node_in_nodes() -> None:
    with pytest.raises(TypeError):
        _DummyElement(1, (Node(1, 0.0, 0.0, 0.0), "not-a-node"), STEEL, SECTION)  # type: ignore[arg-type]


def test_element_rejects_non_material() -> None:
    with pytest.raises(TypeError):
        _DummyElement(1, _nodes(), "not-a-material", SECTION)  # type: ignore[arg-type]


def test_element_rejects_non_section() -> None:
    with pytest.raises(TypeError):
        _DummyElement(1, _nodes(), STEEL, "not-a-section")  # type: ignore[arg-type]


def test_element_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Element(1, _nodes(), STEEL, SECTION)  # type: ignore[abstract]


def test_global_stiffness_matrix_equals_local_when_transform_is_identity() -> None:
    el = _DummyElement(1, _nodes(), STEEL, SECTION)
    assert np.allclose(el.global_stiffness_matrix(), el.local_stiffness_matrix())


def test_global_stiffness_matrix_is_congruent_transform_of_local() -> None:
    el = _RotatedDummyElement(1, _nodes(), STEEL, SECTION)
    t = el.transformation_matrix()
    k_local = el.local_stiffness_matrix()
    expected = t.T @ k_local @ t
    assert np.allclose(el.global_stiffness_matrix(), expected)


def test_global_stiffness_matrix_stays_symmetric_under_rotation() -> None:
    el = _RotatedDummyElement(1, _nodes(), STEEL, SECTION)
    k_global = el.global_stiffness_matrix()
    assert np.allclose(k_global, k_global.T)


def test_global_stiffness_matrix_preserves_eigenvalues_under_orthogonal_transform() -> None:
    # T ortogonal (rotacao) preserva o espectro de autovalores de K por
    # ser uma transformacao de similaridade/congruencia com T^-1 == T.T.
    el_id = _DummyElement(1, _nodes(), STEEL, SECTION)
    el_rot = _RotatedDummyElement(1, _nodes(), STEEL, SECTION)
    eig_local = np.sort(np.linalg.eigvalsh(el_id.local_stiffness_matrix()))
    eig_global_rotated = np.sort(np.linalg.eigvalsh(el_rot.global_stiffness_matrix()))
    assert np.allclose(eig_local, eig_global_rotated)


def test_element_repr_contains_class_id_and_node_ids() -> None:
    el = _DummyElement(5, _nodes(), STEEL, SECTION)
    text = repr(el)
    assert "_DummyElement" in text
    assert "5" in text
    assert "1" in text and "2" in text
