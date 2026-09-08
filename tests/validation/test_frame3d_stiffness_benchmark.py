"""VAL-0001 — Validacao estrutural do Element3D (STRUCTURAL VALIDATION AGENT).

Fonte normativa: nenhuma (nao ha regra de NBR envolvida aqui — este e
um teste de metodo numerico contra mecanica dos materiais classica).

Referencia: solucoes fechadas de viga em balanco (cantilever) da
teoria classica de vigas de Euler-Bernoulli, encontradas em qualquer
livro-texto de Resistencia dos Materiais / Mecanica dos Solidos
(p.ex. Hibbeler, "Mechanics of Materials"; Timoshenko & Gere,
"Mechanics of Materials"):

    axial:        u  = P*L / (E*A)
    torcao:       rx = T*L / (G*J)
    flexao (v):   v  = P*L**3 / (3*E*Iz),   rz = P*L**2 / (2*E*Iz)
    flexao (w):   w  = P*L**3 / (3*E*Iy),   ry = -P*L**2 / (2*E*Iy)

Metodo: como Assembly/BoundaryConditions/Solver ainda nao existem
nesta fase, a "solucao" e obtida resolvendo diretamente o sistema
condensado de 6 equacoes do no livre (no 1 engastado => as 6
primeiras linhas/colunas de K saem do sistema, restando exatamente
``K[6:, 6:] @ u2 = F2``), com ``numpy.linalg.solve``. Isso testa
exatamente a matriz de rigidez produzida por ``Element3D``, sem
depender de nenhum outro componente do nucleo.

Cada caso registra PROBLEMA / REFERENCIA / RESULTADO / ERRO /
TOLERANCIA / STATUS, conforme AGENTS_MASTER.md secao 7. O relatorio
consolidado desta validacao esta em
``docs/validation/VAL-0001-frame3d-stiffness-matrix.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.material import Material
from openstruct.domain.node import Node
from openstruct.domain.section import Section

STEEL = Material(
    name="ASTM A572 Gr. 50",
    E=200000.0,   # MPa
    G=77000.0,    # MPa
    density=7.85e-6,
    fy=345.0,
    fu=450.0,
    poisson=0.3,
)
SECTION = Section(
    name="W310x21",
    A=2680.0,     # mm^2
    Iy=3.79e6,    # mm^4
    Iz=37.0e6,    # mm^4
    J=52.8e3,     # mm^4
    Wply=306e3,
    Wplz=254e3,
    Wely=272e3,
    Welz=239e3,
)

#: Tolerancia relativa adotada para esta validacao. A solucao de um
#: unico elemento de viga de Euler-Bernoulli sob carga de extremidade
#: e a solucao EXATA da equacao diferencial (nao ha erro de
#: discretizacao a reduzir) — a tolerancia aqui existe apenas para
#: absorver erro de arredondamento de ponto flutuante, por isso e
#: extremamente apertada.
RELATIVE_TOLERANCE = 1.0e-9


@dataclass(frozen=True)
class ValidationRecord:
    """Um registro PROBLEMA/REFERENCIA/RESULTADO exigido por AGENTS_MASTER."""

    problema: str
    referencia: float
    resultado: float
    tolerancia: float = RELATIVE_TOLERANCE

    @property
    def erro_relativo(self) -> float:
        if self.referencia == 0.0:
            return abs(self.resultado)
        return abs(self.resultado - self.referencia) / abs(self.referencia)

    @property
    def status(self) -> str:
        return "APROVADO" if self.erro_relativo <= self.tolerancia else "REPROVADO"


def _cantilever_free_end_displacement(
    element: Element3D, force_local: np.ndarray
) -> np.ndarray:
    """Resolve os 6 deslocamentos LOCAIS do no livre (no 2) engastando o no 1.

    ``force_local`` e o vetor de 6 forcas/momentos LOCAIS aplicados no
    no 2 (ordem UX,UY,UZ,RX,RY,RZ).
    """
    k_local = element.local_stiffness_matrix()
    k_ff = k_local[6:, 6:]  # no 1 engastado -> equacoes remanescentes sao as do no 2
    return np.linalg.solve(k_ff, force_local)


# ---------------------------------------------------------------------------
# Caso 1: elemento alinhado com o eixo global X (local == global)
# ---------------------------------------------------------------------------

@pytest.fixture()
def axis_aligned_cantilever() -> tuple[Element3D, float]:
    length = 4000.0  # mm
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, length, 0.0, 0.0)
    element = Element3D(1, (n1, n2), STEEL, SECTION)
    return element, length


def test_val0001_axial_elongation(axis_aligned_cantilever: tuple[Element3D, float]) -> None:
    element, length = axis_aligned_cantilever
    p = 50_000.0  # N
    u = _cantilever_free_end_displacement(element, np.array([p, 0, 0, 0, 0, 0]))

    reference = p * length / (STEEL.E * SECTION.A)
    record = ValidationRecord(
        problema="Barra em balanco, carga axial P na extremidade livre",
        referencia=reference,
        resultado=u[0],
    )
    assert record.status == "APROVADO", record


def test_val0001_torsional_twist(axis_aligned_cantilever: tuple[Element3D, float]) -> None:
    element, length = axis_aligned_cantilever
    t = 3_000_000.0  # N.mm
    u = _cantilever_free_end_displacement(element, np.array([0, 0, 0, t, 0, 0]))

    reference = t * length / (STEEL.G * SECTION.J)
    record = ValidationRecord(
        problema="Barra em balanco, torque T na extremidade livre",
        referencia=reference,
        resultado=u[3],
    )
    assert record.status == "APROVADO", record


def test_val0001_bending_about_z_deflection_and_slope(
    axis_aligned_cantilever: tuple[Element3D, float]
) -> None:
    element, length = axis_aligned_cantilever
    p = 10_000.0  # N, na direcao local y
    u = _cantilever_free_end_displacement(element, np.array([0, p, 0, 0, 0, 0]))

    ei = STEEL.E * SECTION.Iz
    v_ref = p * length**3 / (3 * ei)
    rz_ref = p * length**2 / (2 * ei)

    v_record = ValidationRecord(
        problema="Balanco, carga transversal P (plano x-y) — flecha v na ponta",
        referencia=v_ref,
        resultado=u[1],
    )
    rz_record = ValidationRecord(
        problema="Balanco, carga transversal P (plano x-y) — rotacao rz na ponta",
        referencia=rz_ref,
        resultado=u[5],
    )
    assert v_record.status == "APROVADO", v_record
    assert rz_record.status == "APROVADO", rz_record


def test_val0001_bending_about_y_deflection_and_slope(
    axis_aligned_cantilever: tuple[Element3D, float]
) -> None:
    element, length = axis_aligned_cantilever
    p = 10_000.0  # N, na direcao local z
    u = _cantilever_free_end_displacement(element, np.array([0, 0, p, 0, 0, 0]))

    ei = STEEL.E * SECTION.Iy
    w_ref = p * length**3 / (3 * ei)
    ry_ref = -p * length**2 / (2 * ei)  # ver convencao de sinal em frame3d.py

    w_record = ValidationRecord(
        problema="Balanco, carga transversal P (plano x-z) — flecha w na ponta",
        referencia=w_ref,
        resultado=u[2],
    )
    ry_record = ValidationRecord(
        problema="Balanco, carga transversal P (plano x-z) — rotacao ry na ponta",
        referencia=ry_ref,
        resultado=u[4],
    )
    assert w_record.status == "APROVADO", w_record
    assert ry_record.status == "APROVADO", ry_record


# ---------------------------------------------------------------------------
# Caso 2: elemento em orientacao 3D arbitraria — valida transformation_matrix()
# ---------------------------------------------------------------------------

def test_val0001_arbitrary_orientation_global_solution_matches_local_via_transform() -> None:
    """Consistencia local<->global para uma barra em direcao 3D arbitraria.

    Nao ha formula fechada direta para deslocamento GLOBAL de uma barra
    inclinada generica, entao a validacao e feita por um caminho
    independente: resolver no sistema LOCAL (mesma equacao ja validada
    nos casos acima) e comparar com a solucao obtida resolvendo
    diretamente no sistema GLOBAL (o que efetivamente sera usado pela
    futura montagem global). Isso valida que ``transformation_matrix()``
    e ``global_stiffness_matrix()`` sao consistentes entre si e com
    ``local_stiffness_matrix()``.
    """
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 1000.0, 2000.0, 1500.0)
    element = Element3D(1, (n1, n2), STEEL, SECTION)

    rng = np.random.default_rng(seed=42)
    f_global = rng.uniform(-1.0e4, 1.0e4, size=6)

    lam = np.vstack(element.local_axes())
    t2 = np.zeros((6, 6))
    t2[:3, :3] = lam
    t2[3:, 3:] = lam

    f_local = t2 @ f_global
    u_local = _cantilever_free_end_displacement(element, f_local)
    u_global_via_local = t2.T @ u_local

    k_global_ff = element.global_stiffness_matrix()[6:, 6:]
    u_global_direct = np.linalg.solve(k_global_ff, f_global)

    error = np.linalg.norm(u_global_direct - u_global_via_local) / np.linalg.norm(
        u_global_via_local
    )
    record = ValidationRecord(
        problema=(
            "Barra 3D generica (dx=1000, dy=2000, dz=1500 mm): solucao via "
            "sistema global vs. solucao via sistema local transformado"
        ),
        referencia=float(np.linalg.norm(u_global_via_local)),
        resultado=float(np.linalg.norm(u_global_direct)),
        tolerancia=1e-8,
    )
    assert error <= record.tolerancia, (error, record)
    assert np.allclose(u_global_direct, u_global_via_local, rtol=1e-8, atol=1e-12)
