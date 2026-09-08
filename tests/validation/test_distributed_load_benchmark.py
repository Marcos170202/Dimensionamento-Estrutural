"""VAL-0003 — Validacao estrutural de DistributedLoad (STRUCTURAL VALIDATION AGENT).

Fonte normativa: nenhuma (metodo numerico contra mecanica dos
materiais classica e estatica basica).

Referencia
----------
- Reacoes de viga em balanco sob carga uniforme ``w`` (N/mm) ao longo
  de todo o vao ``L``: por ESTATICA PURA (resultante ``wL`` no
  centroide da carga, ``x=L/2``), reacao de forca = ``-wL``,
  reacao de momento = ``-wL^2/2`` — independente de qualquer rigidez,
  mesma tecnica de VAL-0002 Caso 3.
- Reacoes de viga simplesmente apoiada sob carga uniforme: por simetria
  e estatica pura, ``R = wL/2`` em cada apoio.
- Flecha/rotacao na ponta de balanco sob carga uniforme (formula
  fechada classica, Hibbeler/Timoshenko & Gere):
  ``v_tip = wL^4/(8EI)``, ``theta_tip = wL^3/(6EI)``.
- Rotacao nos apoios de viga simplesmente apoiada sob carga uniforme:
  ``theta = wL^3/(24EI)`` em cada apoio (sinais opostos, por simetria).

Metodo: um elemento de viga de Euler-Bernoulli com CARGA NODAL
EQUIVALENTE consistente (obtida por trabalho virtual, ver docstring de
``DistributedLoad``) reproduz EXATAMENTE os valores de deslocamento e
rotacao NOS NOS para carga uniforme — propriedade classica de
"superconvergencia nodal" de elementos de viga (ver Cook/Malkus/Plesha
ou Logan, "A First Course in the Finite Element Method"). Isso e
confirmado numericamente abaixo, nao apenas presumido.
"""

from __future__ import annotations

import numpy as np
from validation_record import ValidationRecord

from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.loads import DistributedLoad, LoadCase
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

RELATIVE_TOLERANCE = 1.0e-8

LENGTH = 4000.0
W = 5.0  # N/mm


def _cantilever_with_distributed_load(
    wy: float = 0.0, wz: float = 0.0
) -> tuple[AnalysisModel, Element3D]:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, LENGTH, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    element = Element3D(1, (n1, n2), STEEL, SECTION)
    model.add_element(element)
    model.add_support(Support.fixed(1))
    return model, element


# ---------------------------------------------------------------------------
# Caso 1: balanco sob carga uniforme, plano x-y (wy)
# ---------------------------------------------------------------------------


def test_val0003_cantilever_udl_y_reaction_matches_pure_statics() -> None:
    model, _element = _cantilever_with_distributed_load(wy=W)
    result = run_analysis(model, LoadCase("UDL", element_loads=(DistributedLoad(1, wy=W),)))

    reaction = result.reactions[1]
    records = [
        ValidationRecord(
            problema="Balanco sob UDL wy — reacao Fy (estatica pura: -wL)",
            referencia=-W * LENGTH,
            resultado=reaction[1],
        ),
        ValidationRecord(
            problema="Balanco sob UDL wy — reacao Mz (estatica pura: -wL^2/2)",
            referencia=-W * LENGTH**2 / 2.0,
            resultado=reaction[5],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


def test_val0003_cantilever_udl_y_tip_displacement_matches_closed_form() -> None:
    model, _element = _cantilever_with_distributed_load(wy=W)
    result = run_analysis(model, LoadCase("UDL", element_loads=(DistributedLoad(1, wy=W),)))

    ei = STEEL.E * SECTION.Iz
    v_ref = W * LENGTH**4 / (8 * ei)
    theta_ref = W * LENGTH**3 / (6 * ei)

    records = [
        ValidationRecord(
            problema="Balanco sob UDL wy — flecha na ponta (v = wL^4/8EI)",
            referencia=v_ref,
            resultado=result.displacements[2][1],
        ),
        ValidationRecord(
            problema="Balanco sob UDL wy — rotacao na ponta (theta = wL^3/6EI)",
            referencia=theta_ref,
            resultado=result.displacements[2][5],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


def test_val0003_cantilever_udl_y_free_end_has_zero_internal_force() -> None:
    """Sem carga nodal direta no no livre, o esforco interno la deve ser ~0.

    Verifica que o sinal de ``fixed_end_forces_local_for`` subtraido em
    ``run_analysis`` esta correto — sem essa subtracao (ou com o sinal
    trocado), este valor NAO seria numericamente zero.
    """
    model, _element = _cantilever_with_distributed_load(wy=W)
    result = run_analysis(model, LoadCase("UDL", element_loads=(DistributedLoad(1, wy=W),)))
    assert np.allclose(result.element_forces[1][6:], 0.0, atol=1e-6)


# ---------------------------------------------------------------------------
# Caso 2: balanco sob carga uniforme, plano x-z (wz) — par com sinal invertido
# ---------------------------------------------------------------------------


def test_val0003_cantilever_udl_z_reaction_matches_pure_statics() -> None:
    model, _element = _cantilever_with_distributed_load(wz=W)
    result = run_analysis(model, LoadCase("UDL", element_loads=(DistributedLoad(1, wz=W),)))

    reaction = result.reactions[1]
    records = [
        ValidationRecord(
            problema="Balanco sob UDL wz — reacao Fz (estatica pura: -wL)",
            referencia=-W * LENGTH,
            resultado=reaction[2],
        ),
        ValidationRecord(
            problema="Balanco sob UDL wz — reacao My (estatica pura: +wL^2/2)",
            referencia=W * LENGTH**2 / 2.0,
            resultado=reaction[4],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


def test_val0003_cantilever_udl_z_tip_displacement_matches_closed_form() -> None:
    model, _element = _cantilever_with_distributed_load(wz=W)
    result = run_analysis(model, LoadCase("UDL", element_loads=(DistributedLoad(1, wz=W),)))

    ei = STEEL.E * SECTION.Iy
    w_ref = W * LENGTH**4 / (8 * ei)
    ry_ref = -W * LENGTH**3 / (6 * ei)  # ver convencao de sinal em frame3d.py

    records = [
        ValidationRecord(
            problema="Balanco sob UDL wz — flecha na ponta (w = wL^4/8EI)",
            referencia=w_ref,
            resultado=result.displacements[2][2],
        ),
        ValidationRecord(
            problema="Balanco sob UDL wz — rotacao na ponta (ry = -wL^3/6EI)",
            referencia=ry_ref,
            resultado=result.displacements[2][4],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 3: viga simplesmente apoiada sob carga uniforme (wy)
# ---------------------------------------------------------------------------


def test_val0003_simply_supported_beam_udl_reactions_match_statics() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, LENGTH, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    # no 1: pino (translacoes + torcao restritas, flexao livre);
    # no 2: rolete (so translacoes transversais restritas, UX livre —
    # viga simplesmente apoiada classica, sem restricao axial redundante).
    model.add_support(Support(1, ux=True, uy=True, uz=True, rx=True))
    model.add_support(Support(2, uy=True, uz=True))

    result = run_analysis(
        model, LoadCase("UDL", element_loads=(DistributedLoad(1, wy=W),))
    )

    records = [
        ValidationRecord(
            problema="Viga simplesmente apoiada sob UDL — reacao Fy no apoio 1 (wL/2)",
            referencia=-W * LENGTH / 2.0,
            resultado=result.reactions[1][1],
        ),
        ValidationRecord(
            problema="Viga simplesmente apoiada sob UDL — reacao Fy no apoio 2 (wL/2)",
            referencia=-W * LENGTH / 2.0,
            resultado=result.reactions[2][1],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


def test_val0003_simply_supported_beam_udl_end_rotations_match_closed_form() -> None:
    """Confirma a "superconvergencia nodal": rotacao NOS NOS exata mesmo
    com um unico elemento sob carga distribuida (nao apenas nodal)."""
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, LENGTH, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support(1, ux=True, uy=True, uz=True, rx=True))
    model.add_support(Support(2, uy=True, uz=True))

    result = run_analysis(
        model, LoadCase("UDL", element_loads=(DistributedLoad(1, wy=W),))
    )

    ei = STEEL.E * SECTION.Iz
    theta_ref = W * LENGTH**3 / (24 * ei)

    records = [
        ValidationRecord(
            problema="Viga simplesmente apoiada sob UDL — rotacao no apoio 1 (+wL^3/24EI)",
            referencia=theta_ref,
            resultado=result.displacements[1][5],
        ),
        ValidationRecord(
            problema="Viga simplesmente apoiada sob UDL — rotacao no apoio 2 (-wL^3/24EI)",
            referencia=-theta_ref,
            resultado=result.displacements[2][5],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 4: equilibrio global com carga nodal + distribuida combinadas
# ---------------------------------------------------------------------------


def test_val0003_global_equilibrium_holds_with_mixed_nodal_and_distributed_loads() -> None:
    from openstruct.domain.loads import NodalLoad

    model, _element = _cantilever_with_distributed_load()
    load = LoadCase(
        "Misto",
        loads=(NodalLoad(2, fy=-3000.0, mz=1.5e5),),
        element_loads=(DistributedLoad(1, wy=W, wz=2.0),),
    )
    result = run_analysis(model, load)

    # Equilibrio global: reacao + resultante da carga nodal + resultante
    # da carga distribuida (forca wL no centroide L/2) = 0.
    reaction = result.reactions[1]
    applied_nodal_force = np.array([0.0, -3000.0, 0.0])
    applied_nodal_moment = np.array([0.0, 0.0, 1.5e5])
    distributed_resultant_force = np.array([0.0, W * LENGTH, 2.0 * LENGTH])
    centroid = np.array([LENGTH / 2.0, 0.0, 0.0])
    node2 = np.array([LENGTH, 0.0, 0.0])

    net_force = reaction[:3] + applied_nodal_force + distributed_resultant_force
    net_moment = (
        reaction[3:6]
        + applied_nodal_moment
        + np.cross(node2, applied_nodal_force)
        + np.cross(centroid, distributed_resultant_force)
    )

    assert np.allclose(net_force, 0.0, atol=1e-6), net_force
    assert np.allclose(net_moment, 0.0, atol=1e-3), net_moment
    assert result.free_dof_equilibrium_residual < 1e-6
