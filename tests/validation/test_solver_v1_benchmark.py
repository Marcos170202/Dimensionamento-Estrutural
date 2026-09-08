"""VAL-0002 — Validacao estrutural do pipeline SOLVER V1.

Fonte normativa: nenhuma (nao ha regra de NBR envolvida — metodo
numerico contra mecanica dos materiais classica e estatica basica).

Agente responsavel: STRUCTURAL VALIDATION AGENT.

Componentes validados em conjunto: ``AnalysisModel``, ``Assembly``,
``BoundaryConditions``, ``solve_linear_system``, ``run_analysis``
(``AnalysisResult``). ``Element3D`` isolado ja foi validado em
VAL-0001 — aqui o alvo e a MONTAGEM e a RESOLUCAO do sistema global,
nao a formulacao do elemento em si.

Casos:

1. **Cadeia de 2 elementos colineares == 1 elemento equivalente**:
   para uma viga prismatica uniforme sob carga apenas nodal (sem
   carga distribuida), o elemento de viga de Euler-Bernoulli de 2 nos
   e a solucao EXATA da equacao diferencial — logo subdividir o vao
   em 2 elementos nao pode mudar o resultado, nem na ponta nem em
   nenhum ponto interior. Isso valida que ``Assembly`` monta a matriz
   global corretamente (sobreposicao nos DOFs compartilhados).
2. **Equilibrio global**: para qualquer modelo resolvido,
   ``soma das reacoes + soma das cargas aplicadas = 0`` (forcas E
   momentos, Newton/estatica basica) — verificacao completamente
   independente da formulacao de qualquer elemento.
3. **Estrutura "em arvore" (sem malha fechada) com um unico apoio
   engastado**: quando ha exatamente um apoio e ele e um engastamento
   perfeito, a reacao nesse apoio e determinada SOMENTE por estatica
   (equilibrio do corpo livre inteiro), independente de qualquer
   rigidez de material/secao — validacao forte e independente de
   ``Assembly``+``BoundaryConditions``+``solve_linear_system``+
   extracao de reacoes em ``run_analysis``.
"""

from __future__ import annotations

import numpy as np
import pytest
from validation_record import ValidationRecord

from openstruct.analysis.boundary_conditions import ModelInstabilityError
from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.loads import LoadCase, NodalLoad
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

#: Tolerancia relativa usada nos casos com valor de referencia fechado
#: (Casos 1 e 3). ``ValidationRecord`` compartilhado esta em
#: ``validation_record.py`` (CODE REVIEW AGENT apontou a duplicacao
#: anterior desta classe entre este arquivo e VAL-0001).
RELATIVE_TOLERANCE = 1.0e-8


# ---------------------------------------------------------------------------
# Caso 1: cadeia de 2 elementos colineares == 1 elemento equivalente
# ---------------------------------------------------------------------------


def test_val0002_two_element_chain_matches_single_element_tip_deflection() -> None:
    total_length = 4000.0
    half_length = total_length / 2.0
    p = 10_000.0  # N, direcao local/global y

    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, half_length, 0.0, 0.0)
    n3 = Node(3, total_length, 0.0, 0.0)
    for n in (n1, n2, n3):
        model.add_node(n)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_element(Element3D(2, (n2, n3), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    load = LoadCase("P", (NodalLoad(3, fy=p),))
    result = run_analysis(model, load)

    ei = STEEL.E * SECTION.Iz
    v_tip_ref = p * total_length**3 / (3 * ei)
    rz_tip_ref = p * total_length**2 / (2 * ei)

    v_record = ValidationRecord(
        problema="Cadeia de 2 elementos (2000+2000mm) vs. 1 elemento de 4000mm — flecha na ponta",
        referencia=v_tip_ref,
        resultado=result.displacements[3][1],
    )
    rz_record = ValidationRecord(
        problema="Cadeia de 2 elementos — rotacao na ponta",
        referencia=rz_tip_ref,
        resultado=result.displacements[3][5],
    )
    assert v_record.status == "APROVADO", v_record
    assert rz_record.status == "APROVADO", rz_record


def test_val0002_two_element_chain_matches_analytical_deflection_curve_at_interior_node() -> None:
    """Confere o no INTERIOR (no 2, meio do vao) contra a curva de deflexao classica.

    Formula classica (viga em balanco, carga P na ponta, x medido a
    partir do engaste, 0<=x<=L): ``v(x) = P*x^2*(3L-x) / (6EI)``,
    ``theta(x) = P*x*(2L-x) / (2EI)`` — ver docstring do modulo.
    """
    total_length = 4000.0
    half_length = total_length / 2.0
    p = 10_000.0

    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, half_length, 0.0, 0.0)
    n3 = Node(3, total_length, 0.0, 0.0)
    for n in (n1, n2, n3):
        model.add_node(n)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_element(Element3D(2, (n2, n3), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    load = LoadCase("P", (NodalLoad(3, fy=p),))
    result = run_analysis(model, load)

    ei = STEEL.E * SECTION.Iz
    x = half_length
    v_ref = p * x**2 * (3 * total_length - x) / (6 * ei)
    theta_ref = p * x * (2 * total_length - x) / (2 * ei)

    v_record = ValidationRecord(
        problema="No interior (x=L/2) da cadeia de 2 elementos — flecha",
        referencia=v_ref,
        resultado=result.displacements[2][1],
    )
    theta_record = ValidationRecord(
        problema="No interior (x=L/2) da cadeia de 2 elementos — rotacao",
        referencia=theta_ref,
        resultado=result.displacements[2][5],
    )
    assert v_record.status == "APROVADO", v_record
    assert theta_record.status == "APROVADO", theta_record


# ---------------------------------------------------------------------------
# Caso 2: equilibrio global (forca e momento) em modelo 3D com varios apoios
# ---------------------------------------------------------------------------


def test_val0002_global_equilibrium_holds_for_multi_support_3d_model() -> None:
    """Soma de reacoes + soma de cargas aplicadas = 0 (forca e momento).

    Modelo: portico em L com 3 nos e 2 elementos, DOIS apoios (um
    engaste e um apoio parcial) — nao e mais um unico corpo livre
    trivial como no Caso 3, entao esta verificacao usa apenas a lei
    geral de equilibrio (nao um valor de referencia fechado).
    """
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 0.0, 0.0, 3000.0)
    n3 = Node(3, 2500.0, 0.0, 3000.0)
    for n in (n1, n2, n3):
        model.add_node(n)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_element(Element3D(2, (n2, n3), STEEL, SECTION))
    model.add_support(Support.fixed(1))
    model.add_support(Support(3, ux=True, uy=True, uz=True))

    load = LoadCase(
        "Geral",
        (
            NodalLoad(2, fx=1500.0, fy=-800.0, mz=2.0e5),
            NodalLoad(3, fy=-4000.0, fz=-2500.0, mx=1.0e5),
        ),
    )
    result = run_analysis(model, load)

    def _force_and_moment_about_origin(
        node_id: int, force: np.ndarray, moment: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Forca (invariante) e momento referido a origem (``M + r x F``).

        Um binario forca+momento aplicado em ``r`` e EQUIVALENTE, para
        fins de equilibrio de corpo rigido, a esse mesmo binario
        transportado para a origem somando ``r x F`` ao momento — e
        assim que forcas/momentos aplicados (ou reagidos) em pontos
        diferentes podem ser somados de forma fisicamente valida.
        """
        r = np.array(model.nodes[node_id].coordinates)
        return force, moment + np.cross(r, force)

    net_force = np.zeros(3)
    net_moment = np.zeros(3)

    for node_id, reaction in result.reactions.items():
        f, m = _force_and_moment_about_origin(node_id, reaction[:3], reaction[3:6])
        net_force += f
        net_moment += m

    for load_item in load.loads:
        assert isinstance(load_item, NodalLoad)
        f, m = _force_and_moment_about_origin(
            load_item.node_id,
            np.array(load_item.components[:3]),
            np.array(load_item.components[3:6]),
        )
        net_force += f
        net_moment += m

    assert np.allclose(net_force, 0.0, atol=1e-6), net_force
    assert np.allclose(net_moment, 0.0, atol=1e-3), net_moment


# ---------------------------------------------------------------------------
# Caso 3: estrutura em "arvore" com um unico apoio engastado — reacao
# determinada por ESTATICA PURA, independente de qualquer rigidez.
# ---------------------------------------------------------------------------


def test_val0002_tree_structure_single_fixed_support_reaction_matches_pure_statics() -> None:
    """L-bracket (coluna + viga em balanco) com um unico engaste.

    Como a estrutura nao tem nenhuma malha fechada (e uma "arvore": A
    -> B -> C, sem caminho alternativo) e ha um UNICO apoio (engaste
    perfeito em A), a reacao em A e determinada inteiramente pelo
    equilibrio do corpo livre inteiro — ``R = -F_aplicada`` e
    ``M_R = -(r_C x F_aplicada + M_aplicado)`` — e NAO depende de E,
    G, A, I, J de nenhum elemento. Essa e uma verificacao
    completamente independente da formulacao de ``Element3D``
    (ja validada em VAL-0001): valida apenas que
    ``Assembly``+``BoundaryConditions``+``solve_linear_system`` +
    extracao de reacoes em ``run_analysis`` preservam o equilibrio
    estatico correto.
    """
    column_height = 3000.0
    beam_length = 2500.0

    model = AnalysisModel()
    n_a = Node(1, 0.0, 0.0, 0.0)
    n_b = Node(2, 0.0, 0.0, column_height)
    n_c = Node(3, beam_length, 0.0, column_height)
    for n in (n_a, n_b, n_c):
        model.add_node(n)
    model.add_element(Element3D(1, (n_a, n_b), STEEL, SECTION))
    model.add_element(Element3D(2, (n_b, n_c), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    applied_force = np.array([1000.0, -2000.0, -5000.0])
    applied_moment = np.array([300_000.0, -150_000.0, 80_000.0])
    load = LoadCase(
        "P",
        (
            NodalLoad(
                3,
                fx=applied_force[0], fy=applied_force[1], fz=applied_force[2],
                mx=applied_moment[0], my=applied_moment[1], mz=applied_moment[2],
            ),
        ),
    )
    result = run_analysis(model, load)

    r_c = np.array(n_c.coordinates)
    reaction_force_ref = -applied_force
    reaction_moment_ref = -(np.cross(r_c, applied_force) + applied_moment)

    reaction = result.reactions[1]
    force_records = [
        ValidationRecord(
            problema=f"Reacao em apoio unico (arvore estaticamente determinada) — F{axis}",
            referencia=reaction_force_ref[i],
            resultado=reaction[i],
            tolerancia=1e-6,
        )
        for i, axis in enumerate("xyz")
    ]
    moment_records = [
        ValidationRecord(
            problema=f"Reacao em apoio unico (arvore estaticamente determinada) — M{axis}",
            referencia=reaction_moment_ref[i],
            resultado=reaction[3 + i],
            tolerancia=1e-6,
        )
        for i, axis in enumerate("xyz")
    ]
    for record in force_records + moment_records:
        assert record.status == "APROVADO", record


def test_val0002_mechanism_is_rejected_before_producing_wrong_results() -> None:
    """Confirma que um modelo instavel NUNCA produz um resultado silencioso.

    Repete, no nivel de ``run_analysis`` (nao apenas
    ``BoundaryConditions`` isolado, ja coberto em
    ``tests/unit/test_boundary_conditions.py``), o alerta do
    ENGINEERING QA AGENT: "Modelo possui mecanismo."
    """
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    # nenhum Support -> mecanismo (corpo livre no espaco)
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    with pytest.raises(ModelInstabilityError):
        run_analysis(model, load)


# ---------------------------------------------------------------------------
# Caso 5: esforcos internos (element_forces) — elemento alinhado com X
# ---------------------------------------------------------------------------


def test_val0002_element_forces_match_reaction_and_applied_load_for_axis_aligned_member() -> None:
    """Para um elemento unico alinhado com um eixo global, local == global.

    Nesse caso particular (`` local_x == eixo global X``,
    ``transformation_matrix() == identidade`` — ja confirmado em
    VAL-0001), os esforcos internos nas extremidades tem um
    significado fisico direto e verificavel sem nenhum calculo extra:

    - No no ENGASTADO, o esforco interno do elemento e EXATAMENTE a
      reacao de apoio (o elemento e a unica coisa conectada aquele no
      alem do apoio, entao "o que o resto da estrutura aplica no
      elemento" e literalmente a reacao).
    - No no CARREGADO (sem nenhuma outra conexao), o esforco interno
      do elemento e EXATAMENTE a carga externa aplicada (mesma logica:
      equilibrio do no exige que a unica forca vizinha seja igual a
      carga aplicada).

    Isso valida a extracao de ``element_forces`` em ``run_analysis``
    sem depender de nenhuma formula de viga adicional — so da reacao
    (Caso 3, ja validada por estatica pura) e da propria carga
    aplicada (dado de entrada).
    """
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support.fixed(1))

    applied = NodalLoad(2, fx=123.0, fy=-456.0, fz=789.0, mx=111.0, my=-222.0, mz=333.0)
    result = run_analysis(model, LoadCase("P", (applied,)))

    node_i_records = [
        ValidationRecord(
            problema=f"Esforco interno no engaste (no i) vs. reacao — componente {i}",
            referencia=result.reactions[1][i],
            resultado=result.element_forces[1][i],
            tolerancia=1e-9,
        )
        for i in range(6)
    ]
    node_j_records = [
        ValidationRecord(
            problema=f"Esforco interno na ponta carregada (no j) vs. carga aplicada — comp. {i}",
            referencia=applied.components[i],
            resultado=result.element_forces[1][6 + i],
            tolerancia=1e-9,
        )
        for i in range(6)
    ]
    for record in node_i_records + node_j_records:
        assert record.status == "APROVADO", record
