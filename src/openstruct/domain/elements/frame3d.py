"""Elemento de portico espacial (3D frame element), 12 DOFs.

Fonte: PROGRAM_MASTER.md secao 7 ("ELEMENTO 3D"):

    Implementar elemento de portico espacial. 12 DOFs.
    Deve considerar: axial, flexao Y, flexao Z, torcao.
    Criar: local_stiffness_matrix(), transformation_matrix(),
    global_stiffness_matrix().

Formulacao
----------
Viga de Euler-Bernoulli (sem deformacao por cisalhamento — a extensao
para viga de Timoshenko, se necessaria, e um refinamento de fase
futura do SOLVER AGENT, nao coberto aqui), com secao constante ao
longo do comprimento e eixos locais y/z coincidentes com os eixos
principais de inercia da secao. Essa formulacao classica e descrita
em qualquer livro-texto de analise matricial de estruturas (p.ex.
Przemieniecki, "Theory of Matrix Structural Analysis", 1968; McGuire,
Gallagher & Ziemian, "Matrix Structural Analysis", 2a ed., 2000,
cap. 5) — nao e um requisito normativo (NBR) e nao deve ser confundida
com um.

Convencao de DOFs locais (ordem, ver ``domain/dof.py``):
``[no_i: UX,UY,UZ,RX,RY,RZ, no_j: UX,UY,UZ,RX,RY,RZ]``, isto e, os
indices 0..5 pertencem ao primeiro no de ``self.nodes`` e 6..11 ao
segundo. UX e a translacao axial (ao longo do eixo local x do
elemento); flexao em torno do eixo local z (RZ) acopla com UY;
flexao em torno do eixo local y (RY) acopla com UZ; RX e a torcao.

Sistema de eixos locais
------------------------
- ``local_x``: do no i para o no j (``(no_j - no_i) / L``).
- ``local_y``, ``local_z``: definidos a partir de um vetor de
  referencia (``reference_vector``), tecnica padrao para evitar a
  ambiguidade de orientacao de uma barra vertical (quando
  ``local_x`` e paralelo ao eixo global Z, nenhum plano vertical fica
  definido apenas por ``local_x``). Por padrao usa-se o eixo global Z
  como referencia; se ``local_x`` for (quase) paralelo a Z, usa-se o
  eixo global Y. Um angulo de rotacao (``beta``, radianos) em torno de
  ``local_x`` permite orientar a secao livremente quando o padrao nao
  for o desejado.
"""

from __future__ import annotations

import math

import numpy as np

from ..dof import DOFS_PER_NODE
from ..material import Material
from ..node import Node
from ..section import Section
from .base import Element

#: Comprimento minimo (mm) abaixo do qual o elemento e considerado
#: degenerado (nos coincidentes) — ver alerta do ENGINEERING QA AGENT
#: em AGENTS_MASTER.md secao 10: "Elemento possui comprimento
#: praticamente nulo."
_MIN_LENGTH = 1.0e-6

#: Tolerancia (adimensional, norma do produto vetorial) usada para
#: decidir se ``local_x`` esta "praticamente paralelo" ao vetor de
#: referencia padrao, disparando a troca de referencia.
_PARALLEL_TOL = 1.0e-6

_GLOBAL_Z = np.array([0.0, 0.0, 1.0])
_GLOBAL_Y = np.array([0.0, 1.0, 0.0])

_NUM_DOFS = 2 * DOFS_PER_NODE  # 12


class Element3D(Element):
    """Elemento de portico espacial de 2 nos (viga-coluna 3D, 12 DOFs).

    Parametros
    ----------
    id, nodes, material, section:
        Ver :class:`~openstruct.domain.elements.base.Element`.
        ``nodes`` deve conter exatamente 2 nos, nao coincidentes.
    reference_vector:
        Vetor (em coordenadas globais) usado para definir o plano que
        contem o eixo local ``x`` e o eixo local ``y``. Se ``None``
        (padrao), usa-se o eixo global Z, trocando automaticamente
        para o eixo global Y quando ``local_x`` for quase paralelo a
        Z. Nao precisa ser unitario nem ortogonal a ``local_x``.
    beta:
        Angulo de rotacao (radianos) do sistema local ``y``/``z`` em
        torno de ``local_x``, aplicado apos a orientacao padrao
        definida por ``reference_vector``. Util para orientar a secao
        (ex.: perfil rotacionado) sem alterar ``reference_vector``.
    """

    def __init__(
        self,
        id: int,
        nodes: tuple[Node, Node],
        material: Material,
        section: Section,
        reference_vector: tuple[float, float, float] | None = None,
        beta: float = 0.0,
    ) -> None:
        super().__init__(id, nodes, material, section)
        if len(self.nodes) != 2:
            raise ValueError(
                f"Element3D requer exatamente 2 nos, recebido {len(self.nodes)}."
            )

        length = self.nodes[0].distance_to(self.nodes[1])
        if length < _MIN_LENGTH:
            raise ValueError(
                f"Element3D id={id!r}: comprimento praticamente nulo "
                f"({length!r} mm) entre os nos {self.nodes[0].id!r} e "
                f"{self.nodes[1].id!r} — nos coincidentes ou quase "
                "coincidentes geram matriz de transformacao indefinida."
            )
        self._length = length

        if reference_vector is not None:
            ref = np.asarray(reference_vector, dtype=float)
            if ref.shape != (3,) or not np.all(np.isfinite(ref)):
                raise ValueError(
                    f"Element3D.reference_vector deve ser um vetor 3D finito, "
                    f"recebido {reference_vector!r}."
                )
            if np.linalg.norm(ref) < _PARALLEL_TOL:
                raise ValueError(
                    "Element3D.reference_vector nao pode ser o vetor nulo."
                )
            self._reference_vector: np.ndarray | None = ref
        else:
            self._reference_vector = None

        if not math.isfinite(beta):
            raise ValueError(f"Element3D.beta deve ser finito, recebido {beta!r}.")
        self._beta = float(beta)

        self._local_axes = self._compute_local_axes()

    @property
    def length(self) -> float:
        """Comprimento do elemento (mm), calculado entre os 2 nos."""
        return self._length

    @property
    def beta(self) -> float:
        return self._beta

    @property
    def num_dofs(self) -> int:
        return _NUM_DOFS

    def local_axes(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Vetores unitarios ``(local_x, local_y, local_z)`` em coordenadas globais.

        Retorna copias — os arrays internos (``self._local_axes``) sao
        calculados uma unica vez em ``__init__`` e reaproveitados em
        ``transformation_matrix()``; devolve-los diretamente permitiria
        que o chamador os alterasse in-place e corrompesse o estado do
        elemento (CODE REVIEW AGENT, achado confirmado).
        """
        x, y, z = self._local_axes
        return x.copy(), y.copy(), z.copy()

    # -- eixos locais ---------------------------------------------------

    def _compute_local_axes(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        p_i = np.array(self.nodes[0].coordinates)
        p_j = np.array(self.nodes[1].coordinates)
        local_x = (p_j - p_i) / self._length

        if self._reference_vector is not None:
            reference = self._reference_vector
        else:
            reference = _GLOBAL_Z
            if np.linalg.norm(np.cross(reference, local_x)) < _PARALLEL_TOL:
                reference = _GLOBAL_Y

        y_raw = np.cross(reference, local_x)
        y_norm = np.linalg.norm(y_raw)
        if y_norm < _PARALLEL_TOL:
            raise ValueError(
                f"Element3D id={self.id!r}: reference_vector e paralelo a "
                "local_x — nao define um plano local x-y. Forneca outro "
                "reference_vector."
            )
        local_y = y_raw / y_norm
        local_z = np.cross(local_x, local_y)

        if self._beta != 0.0:
            local_y, local_z = _rotate_about_axis(local_y, local_z, local_x, self._beta)

        return local_x, local_y, local_z

    # -- contrato Element -------------------------------------------------

    def transformation_matrix(self) -> np.ndarray:
        local_x, local_y, local_z = self._local_axes
        lam = np.vstack([local_x, local_y, local_z])  # (3, 3), linhas ortonormais
        t = np.zeros((_NUM_DOFS, _NUM_DOFS))
        for block in range(4):
            start = block * 3
            t[start : start + 3, start : start + 3] = lam
        return t

    def local_stiffness_matrix(self) -> np.ndarray:
        e = self.material.E
        g = self.material.G
        a = self.section.A
        iy = self.section.Iy
        iz = self.section.Iz
        j = self.section.J
        length = self._length

        k = np.zeros((_NUM_DOFS, _NUM_DOFS))

        # --- axial (UX: indices 0, 6) ---
        k_ax = e * a / length
        k[0, 0] = k_ax
        k[0, 6] = -k_ax
        k[6, 0] = -k_ax
        k[6, 6] = k_ax

        # --- torcao (RX: indices 3, 9) ---
        k_tor = g * j / length
        k[3, 3] = k_tor
        k[3, 9] = -k_tor
        k[9, 3] = -k_tor
        k[9, 9] = k_tor

        # --- flexao em torno de z: acopla UY (1, 7) e RZ (5, 11) ---
        _fill_bending_block(
            k,
            trans_indices=(1, 7),
            rot_indices=(5, 11),
            ei=e * iz,
            length=length,
            rotation_sign=+1.0,
        )

        # --- flexao em torno de y: acopla UZ (2, 8) e RY (4, 10) ---
        _fill_bending_block(
            k,
            trans_indices=(2, 8),
            rot_indices=(4, 10),
            ei=e * iy,
            length=length,
            rotation_sign=-1.0,
        )

        return k


def _fill_bending_block(
    k: np.ndarray,
    trans_indices: tuple[int, int],
    rot_indices: tuple[int, int],
    ei: float,
    length: float,
    rotation_sign: float,
) -> None:
    """Preenche o bloco 4x4 de flexao de Euler-Bernoulli em ``k`` (in-place).

    ``rotation_sign`` e ``+1`` para flexao no plano x-y (translacao UY,
    rotacao RZ) e ``-1`` para flexao no plano x-z (translacao UZ,
    rotacao RY). A inversao de sinal nos termos de acoplamento
    translacao-rotacao (os termos translacao-translacao e
    rotacao-rotacao nao mudam de sinal) vem da relacao cinematica
    entre deslocamento transversal e rotacao em cada plano: no plano
    x-y, ``dv/dx = +theta_z``; no plano x-z, ``dw/dx = -theta_y``
    (rotacao em torno de +y positiva aponta de z para x pela regra da
    mao direita, o que corresponde a uma inclinacao negativa de
    ``w(x)``). Essa diferenca de sinal entre os dois planos e um
    resultado classico de analise matricial de estruturas (ver
    referencias no docstring do modulo) — validado numericamente em
    ``tests/validation/test_frame3d_stiffness_benchmark.py`` contra as
    formulas fechadas de viga em balanco.
    """
    v1, v2 = trans_indices
    r1, r2 = rot_indices
    length_sq = length * length
    length_cb = length_sq * length

    k_vv = 12.0 * ei / length_cb
    k_vr = rotation_sign * 6.0 * ei / length_sq
    k_rr_same = 4.0 * ei / length
    k_rr_cross = 2.0 * ei / length

    # translacao-translacao
    k[v1, v1] += k_vv
    k[v1, v2] += -k_vv
    k[v2, v1] += -k_vv
    k[v2, v2] += k_vv

    # translacao-rotacao (mesmo no: sinal +; nos opostos: sinal -)
    k[v1, r1] += k_vr
    k[r1, v1] += k_vr
    k[v1, r2] += k_vr
    k[r2, v1] += k_vr
    k[v2, r1] += -k_vr
    k[r1, v2] += -k_vr
    k[v2, r2] += -k_vr
    k[r2, v2] += -k_vr

    # rotacao-rotacao
    k[r1, r1] += k_rr_same
    k[r2, r2] += k_rr_same
    k[r1, r2] += k_rr_cross
    k[r2, r1] += k_rr_cross


def _rotate_about_axis(
    y: np.ndarray, z: np.ndarray, axis: np.ndarray, angle: float
) -> tuple[np.ndarray, np.ndarray]:
    """Rotaciona o par ``(y, z)`` em torno de ``axis`` (formula de Rodrigues)."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def rotate(v: np.ndarray) -> np.ndarray:
        result: np.ndarray = (
            v * cos_a
            + np.cross(axis, v) * sin_a
            + axis * np.dot(axis, v) * (1.0 - cos_a)
        )
        return result

    return rotate(y), rotate(z)
