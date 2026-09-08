"""VAL-0004 — Validacao estrutural de self_weight_loads (STRUCTURAL VALIDATION AGENT).

Fonte normativa: nenhuma (metodo numerico + estatica basica).

Referencia
----------
- Peso por unidade de comprimento: ``w = density * A * gravity``
  (kg/mm^3 * mm^2 * m/s^2 = N/mm — ver derivacao dimensional completa
  na docstring de ``self_weight_loads``). Este valor e calculado A MAO
  em cada caso abaixo e comparado contra o que ``self_weight_loads``
  gera, fechando o ciclo entre "o que a formula diz" e "o que o codigo
  faz".
- Reacoes de viga em balanco sob peso proprio: mesma tecnica de
  estatica pura de VAL-0002/VAL-0003 (resultante ``w*L`` no centroide
  do vao).
- Flecha na ponta de balanco sob peso proprio: mesma formula fechada
  de VAL-0003 (``v = w*L^4/(8EI)``), com ``w`` calculado
  automaticamente em vez de fornecido a mao.

Metodo: como ``self_weight_loads`` apenas gera uma ``DistributedLoad``
por elemento (ja validada isoladamente em VAL-0003), esta validacao
foca em (1) a formula de calculo de ``w`` a partir de material/secao/
gravidade, e (2) a projecao correta de ``w`` nos eixos LOCAIS do
elemento para orientacoes distintas (horizontal, vertical, inclinada).
"""

from __future__ import annotations

import numpy as np
from validation_record import ValidationRecord

from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.loads import DEFAULT_GRAVITY, LoadCase, self_weight_loads
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
#: Peso proprio por unidade de comprimento, calculado A MAO (referencia
#: independente do codigo em teste) — ver derivacao no modulo.
W_SELF = STEEL.density * SECTION.A * DEFAULT_GRAVITY


# ---------------------------------------------------------------------------
# Caso 1: viga horizontal em balanco sob peso proprio (carga transversal pura)
# ---------------------------------------------------------------------------


def test_val0004_horizontal_cantilever_self_weight_reaction_matches_pure_statics() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, LENGTH, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    load = LoadCase("Peso Proprio", element_loads=self_weight_loads(model))
    result = run_analysis(model, load)

    reaction = result.reactions[1]
    records = [
        ValidationRecord(
            problema="Balanco horizontal sob peso proprio — reacao Fz (estatica pura: +wL)",
            referencia=W_SELF * LENGTH,
            resultado=reaction[2],
        ),
        ValidationRecord(
            problema="Balanco horizontal sob peso proprio — reacao My (estatica pura: -wL^2/2)",
            referencia=-W_SELF * LENGTH**2 / 2.0,
            resultado=reaction[4],
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


def test_val0004_horizontal_cantilever_self_weight_tip_deflection_matches_closed_form() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, LENGTH, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    load = LoadCase("Peso Proprio", element_loads=self_weight_loads(model))
    result = run_analysis(model, load)

    ei = STEEL.E * SECTION.Iy
    # gravidade em -Z global => wz local e NEGATIVO (ver VAL-0003 para o
    # caso wz>0 de referencia; aqui e o mesmo com sinal trocado).
    v_ref = -W_SELF * LENGTH**4 / (8 * ei)

    record = ValidationRecord(
        problema="Balanco horizontal sob peso proprio — flecha na ponta (v = -wL^4/8EI)",
        referencia=v_ref,
        resultado=result.displacements[2][2],
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 2: coluna vertical sob peso proprio (compressao axial pura)
# ---------------------------------------------------------------------------


def test_val0004_vertical_column_self_weight_is_pure_axial_compression() -> None:
    """Coluna vertical: peso proprio e paralelo ao eixo da barra -> sem
    flexao, so compressao axial. Reacao = peso total, sem momento."""
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, LENGTH)  # topo
    n2 = Node(2, 0.0, 0.0, 0.0)  # base
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support.fixed(2))

    load = LoadCase("Peso Proprio", element_loads=self_weight_loads(model))
    result = run_analysis(model, load)

    reaction = result.reactions[2]
    records = [
        ValidationRecord(
            problema="Coluna vertical sob peso proprio — reacao Fz (estatica pura: +wL)",
            referencia=W_SELF * LENGTH,
            resultado=reaction[2],
        ),
        ValidationRecord(
            problema="Coluna vertical sob peso proprio — reacao Mx (deve ser 0, sem flexao)",
            referencia=0.0,
            resultado=reaction[3],
            tolerancia=1e-9,
        ),
        ValidationRecord(
            problema="Coluna vertical sob peso proprio — reacao My (deve ser 0, sem flexao)",
            referencia=0.0,
            resultado=reaction[4],
            tolerancia=1e-9,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 3: portico com 2 elementos (horizontal + vertical) — equilibrio global
# ---------------------------------------------------------------------------


def test_val0004_multi_element_frame_total_reaction_equals_total_self_weight() -> None:
    """Soma das reacoes verticais = soma dos pesos de TODOS os elementos,
    independente de orientacao — checagem de equilibrio global (estatica),
    igual ao espirito de VAL-0002 Caso 2."""
    column_height = 3000.0
    beam_length = 2500.0

    model = AnalysisModel()
    n_a = Node(1, 0.0, 0.0, 0.0)
    n_b = Node(2, 0.0, 0.0, column_height)
    n_c = Node(3, beam_length, 0.0, column_height)
    model.add_node(n_a)
    model.add_node(n_b)
    model.add_node(n_c)
    model.add_element(Element3D(1, (n_a, n_b), STEEL, SECTION))
    model.add_element(Element3D(2, (n_b, n_c), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    load = LoadCase("Peso Proprio", element_loads=self_weight_loads(model))
    result = run_analysis(model, load)

    total_weight = W_SELF * (column_height + beam_length)
    record = ValidationRecord(
        problema="Portico L (coluna + viga) sob peso proprio — reacao Fz total = peso total",
        referencia=total_weight,
        resultado=result.reactions[1][2],
    )
    assert record.status == "APROVADO", record
    assert result.free_dof_equilibrium_residual < 1e-6


# ---------------------------------------------------------------------------
# Caso 4: elemento inclinado — equilibrio global (sem formula fechada direta)
# ---------------------------------------------------------------------------


def test_val0004_inclined_element_self_weight_satisfies_global_equilibrium() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 3000.0, 0.0, 4000.0)  # 3-4-5, comprimento 5000mm
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    load = LoadCase("Peso Proprio", element_loads=self_weight_loads(model))
    result = run_analysis(model, load)

    length = 5000.0
    record = ValidationRecord(
        problema="Elemento inclinado (3-4-5) sob peso proprio — reacao Fz = peso total",
        referencia=W_SELF * length,
        resultado=result.reactions[1][2],
    )
    assert record.status == "APROVADO", record
    assert np.allclose(result.reactions[1][:2], 0.0, atol=1e-6)  # sem componente horizontal
    assert result.free_dof_equilibrium_residual < 1e-6
