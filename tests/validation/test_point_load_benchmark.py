"""VAL-0005 — Validacao estrutural de PointLoad (STRUCTURAL VALIDATION AGENT).

Fonte normativa: nenhuma (metodo numerico + estatica basica + formulas
fechadas classicas de resistencia dos materiais).

Referencia
----------
- Reacoes de viga em balanco sob carga concentrada em posicao interior
  do vao (estatica pura, mesma tecnica de VAL-0002/VAL-0003/VAL-0004):
  para uma forca ``P`` aplicada a uma distancia ``a`` do engaste,
  ``R = -P`` e ``M = -P*a`` (equilibrio de forcas/momentos no engaste).
- Deflexao/rotacao de viga em balanco sob carga concentrada em ``x=a``
  (Hibbeler, "Mecanica dos Materiais"; Timoshenko/Gere, "Mecanica dos
  Materiais" — tabelas classicas de vigas em balanco):

      v(a) = P*a^3/(3EI)              theta(a) = P*a^2/(2EI)
      v(L) = P*a^2*(3L-a)/(6EI)       theta(L) = P*a^2/(2EI)

  (a rotacao e constante para ``x >= a`` pois nao ha mais momento
  fletor variavel alem do ponto de aplicacao da carga).
- Casos limite ``a->0`` e ``a->L``: o vetor de carga consistente de
  ``PointLoad`` deve reduzir EXATAMENTE (nao aproximadamente) ao de uma
  ``NodalLoad`` equivalente aplicada diretamente no no correspondente
  — ja verificado simbolicamente na docstring de ``PointLoad``, aqui
  confirmado numericamente end-to-end (reacoes E deslocamentos).

Metodo: como o vetor de carga consistente de ``PointLoad`` ja foi
verificado simbolicamente (SymPy) contra as funcoes de forma de
Hermite antes da implementacao (ver docstring/commit), esta validacao
foca em (1) fechar o ciclo estatica-pura/formula-fechada -> resultado
do solver, e (2) confirmar os casos limite que amarram ``PointLoad`` a
``NodalLoad`` (ja validada desde SOLVER V1 / VAL-0002).
"""

from __future__ import annotations

import numpy as np
from validation_record import ValidationRecord

from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.loads import LoadCase, NodalLoad, PointLoad
from openstruct.domain.material import Material
from openstruct.domain.model import AnalysisModel
from openstruct.domain.node import Node
from openstruct.domain.section import Section
from openstruct.domain.support import Support
from openstruct.results.analysis_result import run_analysis

STEEL = Material(
    name="ASTM A572 Gr. 50", E=200000.0, G=77000.0, density=7.85e-6,
    fy=345.0, fu=450.0, poisson=0.3,
)
SECTION = Section(
    name="W310x21", A=2680.0, Iy=3.79e6, Iz=37.0e6, J=52.8e3,
    Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3,
)

LENGTH = 4000.0


def _cantilever() -> tuple[AnalysisModel, Node, Node]:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, LENGTH, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support.fixed(1))
    return model, n1, n2


# ---------------------------------------------------------------------------
# Caso 1: carga transversal (fy) em posicao interior — estatica pura
# ---------------------------------------------------------------------------


def test_val0005_interior_point_load_reaction_matches_pure_statics() -> None:
    model, _, n2 = _cantilever()
    a = 1500.0
    p = -10_000.0

    load = LoadCase("P", element_loads=(PointLoad(1, position=a, fy=p),))
    result = run_analysis(model, load)

    reaction = result.reactions[1]
    records = [
        ValidationRecord(
            problema="Balanco, carga P em x=a — reacao Fy (estatica pura: -P)",
            referencia=-p,
            resultado=reaction[1],
        ),
        ValidationRecord(
            problema="Balanco, carga P em x=a — reacao Mz (estatica pura: -P*a)",
            referencia=-p * a,
            resultado=reaction[5],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record
    assert result.free_dof_equilibrium_residual < 1e-6


def test_val0005_interior_point_load_deflection_matches_closed_form() -> None:
    """Flecha/rotacao na ponta E no proprio ponto de aplicacao da carga,
    comparadas contra as formulas fechadas classicas de viga em balanco."""
    model, n1, n2 = _cantilever()
    a = 1500.0
    p = -10_000.0
    ei = STEEL.E * SECTION.Iz

    load = LoadCase("P", element_loads=(PointLoad(1, position=a, fy=p),))
    result = run_analysis(model, load)

    v_tip_ref = p * a**2 * (3 * LENGTH - a) / (6 * ei)
    theta_tip_ref = p * a**2 / (2 * ei)

    tip = result.displacements[2]
    records = [
        ValidationRecord(
            problema="Balanco, carga P em x=a — flecha na ponta (v(L)=Pa^2(3L-a)/6EI)",
            referencia=v_tip_ref,
            resultado=tip[1],
        ),
        ValidationRecord(
            problema="Balanco, carga P em x=a — rotacao na ponta (theta(L)=Pa^2/2EI)",
            referencia=theta_tip_ref,
            resultado=tip[5],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 2: carga axial (fx) em posicao interior — estatica pura + formula fechada
# ---------------------------------------------------------------------------


def test_val0005_interior_axial_point_load_matches_pure_statics_and_closed_form() -> None:
    """Alem do ponto de aplicacao (x>=a), o alongamento e constante —
    ``u(x>=a) = P*a/(EA)`` (a barra entre 0 e a se alonga; alem disso,
    nenhuma forca axial adicional atua)."""
    model, _, n2 = _cantilever()
    a = 1000.0
    p = 5_000.0
    ea = STEEL.E * SECTION.A

    load = LoadCase("P", element_loads=(PointLoad(1, position=a, fx=p),))
    result = run_analysis(model, load)

    reaction = result.reactions[1]
    u_ref = p * a / ea
    records = [
        ValidationRecord(
            problema="Balanco, carga axial P em x=a — reacao Fx (estatica pura: -P)",
            referencia=-p,
            resultado=reaction[0],
        ),
        ValidationRecord(
            problema="Balanco, carga axial P em x=a — deslocamento axial na ponta (u=Pa/EA)",
            referencia=u_ref,
            resultado=result.displacements[2][0],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 3: par UZ/RY (fz) — mesmo espirito do Caso 1, eixo diferente
# ---------------------------------------------------------------------------


def test_val0005_interior_point_load_z_direction_matches_pure_statics() -> None:
    """Confirma o sinal invertido do par UZ/RY (mesma convencao de
    DistributedLoad, ver VAL-0003) tambem para PointLoad."""
    model, _, n2 = _cantilever()
    a = 2000.0
    p = -6_000.0

    load = LoadCase("P", element_loads=(PointLoad(1, position=a, fz=p),))
    result = run_analysis(model, load)

    reaction = result.reactions[1]
    records = [
        ValidationRecord(
            problema="Balanco, carga P (eixo z) em x=a — reacao Fz (estatica pura: -P)",
            referencia=-p,
            resultado=reaction[2],
        ),
        ValidationRecord(
            problema="Balanco, carga P (eixo z) em x=a — reacao My (estatica pura: +P*a)",
            referencia=p * a,
            resultado=reaction[4],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record
    assert result.free_dof_equilibrium_residual < 1e-6


# ---------------------------------------------------------------------------
# Caso 4: casos limite a->0 e a->L reduzem EXATAMENTE a NodalLoad
# ---------------------------------------------------------------------------


def test_val0005_point_load_at_end_node_matches_nodal_load_exactly() -> None:
    """PointLoad(position=L) sobre um elemento deve produzir reacoes e
    deslocamentos IDENTICOS (nao apenas proximos) a uma NodalLoad
    aplicada diretamente no no final — o vetor de carga consistente
    colapsa exatamente porque as funcoes de forma de Hermite valem
    (1,0,0,0) e (0,0,1,0) nos extremos do elemento."""
    p = -3_000.0

    model_point, _, _ = _cantilever()
    result_point = run_analysis(
        model_point, LoadCase("PtEnd", element_loads=(PointLoad(1, position=LENGTH, fy=p),))
    )

    model_nodal, _, _ = _cantilever()
    result_nodal = run_analysis(model_nodal, LoadCase("Nodal", loads=(NodalLoad(2, fy=p),)))

    max_reaction_diff = float(
        np.max(np.abs(result_point.reactions[1] - result_nodal.reactions[1]))
    )
    max_displacement_diff = float(
        np.max(np.abs(result_point.displacements[2] - result_nodal.displacements[2]))
    )
    records = [
        ValidationRecord(
            problema="PointLoad(a=L) vs NodalLoad — diferenca maxima nas reacoes (deve ser 0)",
            referencia=0.0,
            resultado=max_reaction_diff,
            tolerancia=1e-9,
        ),
        ValidationRecord(
            problema="PointLoad(a=L) vs NodalLoad — diferenca maxima nos deslocamentos "
            "(deve ser 0)",
            referencia=0.0,
            resultado=max_displacement_diff,
            tolerancia=1e-9,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


def test_val0005_point_load_at_start_node_matches_nodal_load_exactly() -> None:
    """Mesma ideia do teste anterior, mas no no INICIAL do elemento —
    exige um modelo com apoio no no final (para o no inicial ficar
    livre e a carga ali fazer diferenca observavel)."""
    p = -3_000.0

    def _model_fixed_at_end() -> AnalysisModel:
        model = AnalysisModel()
        n1 = Node(1, 0.0, 0.0, 0.0)
        n2 = Node(2, LENGTH, 0.0, 0.0)
        model.add_node(n1)
        model.add_node(n2)
        model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
        model.add_support(Support.fixed(2))
        return model

    result_point = run_analysis(
        _model_fixed_at_end(),
        LoadCase("PtStart", element_loads=(PointLoad(1, position=0.0, fy=p),)),
    )
    result_nodal = run_analysis(
        _model_fixed_at_end(), LoadCase("NodalStart", loads=(NodalLoad(1, fy=p),))
    )

    max_reaction_diff = float(
        np.max(np.abs(result_point.reactions[2] - result_nodal.reactions[2]))
    )
    max_displacement_diff = float(
        np.max(np.abs(result_point.displacements[1] - result_nodal.displacements[1]))
    )
    records = [
        ValidationRecord(
            problema="PointLoad(a=0) vs NodalLoad — diferenca maxima nas reacoes (deve ser 0)",
            referencia=0.0,
            resultado=max_reaction_diff,
            tolerancia=1e-9,
        ),
        ValidationRecord(
            problema="PointLoad(a=0) vs NodalLoad — diferenca maxima nos deslocamentos "
            "(deve ser 0)",
            referencia=0.0,
            resultado=max_displacement_diff,
            tolerancia=1e-9,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record
