"""Testes unitarios de openstruct.domain.elements.frame3d.Element3D.

Cobre construcao/validacao e propriedades estruturais gerais da
matriz de rigidez (simetria, posto, ortogonalidade de T). A
comparacao numerica contra formulas fechadas de viga (validacao de
engenharia propriamente dita) esta em
``tests/validation/test_frame3d_stiffness_benchmark.py``.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openstruct.domain.elements.frame3d import Element3D
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


def test_element3d_computes_length() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 3000.0, 4000.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    assert el.length == pytest.approx(5000.0)


def test_element3d_beta_property_returns_stored_angle() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION, beta=math.radians(15.0))
    assert el.beta == pytest.approx(math.radians(15.0))


def test_element3d_num_dofs_is_twelve() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    assert el.num_dofs == 12
    assert el.local_stiffness_matrix().shape == (12, 12)
    assert el.transformation_matrix().shape == (12, 12)
    assert el.global_stiffness_matrix().shape == (12, 12)


def test_element3d_rejects_more_than_two_nodes() -> None:
    nodes = (Node(1, 0.0, 0.0, 0.0), Node(2, 1.0, 0.0, 0.0), Node(3, 2.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        Element3D(1, nodes, STEEL, SECTION)  # type: ignore[arg-type]


def test_element3d_rejects_coincident_nodes() -> None:
    n1 = Node(1, 5.0, 5.0, 5.0)
    n2 = Node(2, 5.0, 5.0, 5.0)
    with pytest.raises(ValueError):
        Element3D(1, (n1, n2), STEEL, SECTION)


def test_element3d_rejects_near_zero_length() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1e-9, 0.0, 0.0)
    with pytest.raises(ValueError):
        Element3D(1, (n1, n2), STEEL, SECTION)


@pytest.mark.parametrize(
    "bad_reference",
    [
        (1.0, 0.0),  # forma errada (2D em vez de 3D)
        (1.0, 0.0, 0.0, 0.0),  # forma errada (4D)
        (math.nan, 0.0, 1.0),  # componente nao finita
    ],
)
def test_element3d_rejects_malformed_reference_vector(bad_reference: tuple) -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        Element3D(1, (n1, n2), STEEL, SECTION, reference_vector=bad_reference)


def test_element3d_rejects_zero_reference_vector() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        Element3D(1, (n1, n2), STEEL, SECTION, reference_vector=(0.0, 0.0, 0.0))


def test_element3d_rejects_reference_vector_parallel_to_axis() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)  # local_x = global X
    with pytest.raises(ValueError):
        Element3D(1, (n1, n2), STEEL, SECTION, reference_vector=(1.0, 0.0, 0.0))


def test_element3d_rejects_non_finite_beta() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        Element3D(1, (n1, n2), STEEL, SECTION, beta=math.nan)


def test_element3d_local_axes_orthonormal_for_horizontal_member() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    x, y, z = el.local_axes()
    axes = np.vstack([x, y, z])
    assert np.allclose(axes @ axes.T, np.eye(3), atol=1e-12)
    # x cross y == z (triedro diretamente orientado)
    assert np.allclose(np.cross(x, y), z, atol=1e-12)


def test_element3d_local_axes_orthonormal_for_vertical_member() -> None:
    # Caso critico: elemento paralelo ao eixo global Z (coluna vertical),
    # onde o vetor de referencia padrao (Z) e trocado automaticamente por Y.
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 0.0, 0.0, 3000.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    x, y, z = el.local_axes()
    axes = np.vstack([x, y, z])
    assert np.allclose(axes @ axes.T, np.eye(3), atol=1e-12)
    assert np.allclose(np.cross(x, y), z, atol=1e-12)


def test_element3d_local_axes_orthonormal_for_arbitrary_diagonal_member() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 2000.0, 1500.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    x, y, z = el.local_axes()
    axes = np.vstack([x, y, z])
    assert np.allclose(axes @ axes.T, np.eye(3), atol=1e-12)
    assert np.allclose(np.cross(x, y), z, atol=1e-12)


def test_element3d_beta_rotation_preserves_orthonormality() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION, beta=math.radians(37.0))
    x, y, z = el.local_axes()
    axes = np.vstack([x, y, z])
    assert np.allclose(axes @ axes.T, np.eye(3), atol=1e-12)
    assert np.allclose(np.cross(x, y), z, atol=1e-12)


def test_element3d_beta_rotation_leaves_local_x_unchanged() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    el_plain = Element3D(1, (n1, n2), STEEL, SECTION)
    el_rot = Element3D(1, (n1, n2), STEEL, SECTION, beta=math.radians(90.0))
    x_plain, _, _ = el_plain.local_axes()
    x_rot, y_rot, z_rot = el_rot.local_axes()
    assert np.allclose(x_plain, x_rot)
    # beta=90 graus deve mapear y->z e z->-y (rotacao em torno de x)
    _, y_plain, z_plain = el_plain.local_axes()
    assert np.allclose(y_rot, z_plain, atol=1e-10)
    assert np.allclose(z_rot, -y_plain, atol=1e-10)


def test_element3d_local_axes_returns_copy_not_internal_state() -> None:
    # regressao: local_axes() devolvia os arrays internos por referencia;
    # mutar o retorno corrompia self._local_axes e, por consequencia,
    # transformation_matrix() (CODE REVIEW AGENT, achado confirmado).
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)

    x, y, z = el.local_axes()
    x[:] = 0.0
    y[:] = 0.0
    z[:] = 0.0

    x2, y2, z2 = el.local_axes()
    assert np.allclose(x2, [1.0, 0.0, 0.0])
    assert not np.allclose(x2, 0.0)

    t = el.transformation_matrix()
    assert np.allclose(t, np.eye(12), atol=1e-12)


def test_element3d_local_stiffness_matrix_is_symmetric() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    k = el.local_stiffness_matrix()
    assert np.allclose(k, k.T)


def test_element3d_local_stiffness_matrix_has_six_rigid_body_modes() -> None:
    # Um elemento livre no espaco tem exatamente 6 modos de corpo rigido
    # (3 translacoes + 3 rotacoes), logo K local (12x12) deve ter posto 6.
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    k = el.local_stiffness_matrix()
    eigvals = np.linalg.eigvalsh(k)
    zero_modes = np.sum(np.abs(eigvals) < 1e-6 * np.max(np.abs(eigvals)))
    assert zero_modes == 6
    assert np.all(eigvals > -1e-6 * np.max(np.abs(eigvals)))  # positivo-semidefinida


def test_element3d_transformation_matrix_is_orthogonal() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 2000.0, 1500.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    t = el.transformation_matrix()
    assert np.allclose(t @ t.T, np.eye(12), atol=1e-12)
    assert np.linalg.det(t) == pytest.approx(1.0, abs=1e-9)


def test_element3d_global_stiffness_matrix_symmetric_and_same_spectrum_as_local() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 2000.0, 1500.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    k_local = el.local_stiffness_matrix()
    k_global = el.global_stiffness_matrix()
    assert np.allclose(k_global, k_global.T)

    # T ortogonal -> congruencia preserva o espectro de autovalores. Os 6
    # modos de corpo rigido sao ~0 nos dois casos, mas cancelamento de
    # ponto flutuante entre termos da ordem de 1e10 deixa ruido residual
    # na faixa de 1e-6 a 1e-9 com sinais distintos entre local e global —
    # por isso a tolerancia e proporcional a escala da matriz, e os 6
    # autovalores estruturais (nao-nulos) sao comparados separadamente
    # com tolerancia relativa apertada.
    eig_local = np.sort(np.linalg.eigvalsh(k_local))
    eig_global = np.sort(np.linalg.eigvalsh(k_global))
    scale = max(np.max(np.abs(eig_local)), np.max(np.abs(eig_global)))

    zero_tol = 1e-6 * scale
    assert np.all(np.abs(eig_local[:6]) < zero_tol)
    assert np.all(np.abs(eig_global[:6]) < zero_tol)
    assert np.allclose(eig_local[6:], eig_global[6:], rtol=1e-8)


def test_element3d_axis_aligned_with_global_x_has_identity_like_transform() -> None:
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 0.0, 0.0)
    el = Element3D(1, (n1, n2), STEEL, SECTION)
    t = el.transformation_matrix()
    assert np.allclose(t, np.eye(12), atol=1e-12)
    assert np.allclose(el.global_stiffness_matrix(), el.local_stiffness_matrix())
