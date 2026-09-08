"""``AnalysisResult`` e a orquestracao ``run_analysis``.

Fonte: PROGRAM_MASTER.md secao 12 ("RESULTS"): "Resultados:
displacements, reactions, element_forces." e secao 21 ("AI TOOLS"),
que ja antecipa uma futura API ``run_analysis`` /
``get_displacements`` / ``get_reactions`` / ``get_element_forces`` —
os nomes aqui foram escolhidos para casar com essa API futura.

``run_analysis`` e a unica funcao que amarra
DOMAIN (``AnalysisModel``) + ANALYSIS (``Assembly``,
``BoundaryConditions``) + SOLVER (``solve_linear_system``) — ver
ADR-002. Nenhuma das camadas conhece as outras diretamente; apenas
esta funcao (a "camada RESULTS/orquestracao") as compoe.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from ..analysis.assembly import Assembly
from ..analysis.boundary_conditions import BoundaryConditions
from ..domain.loads import LoadSource
from ..domain.model import AnalysisModel
from ..solver.linear import Method, solve_linear_system

#: Tolerancia RELATIVA (adimensional) para o residuo de equilibrio nos
#: DOFs livres (``K_global @ u - F_global``, restrito aos DOFs
#: livres). Um sistema resolvido corretamente tem residuo da ordem do
#: erro de arredondamento de ponto flutuante (~1e-8 a 1e-12 nas
#: validacoes VAL-0001/VAL-0002); um valor muito maior que isso indica
#: algo fisicamente errado (ex.: K_ff nao realmente simetrica apesar
#: de ``solve_linear_system`` assumir isso) — ver alerta do
#: ENGINEERING QA AGENT "Resultado apresenta comportamento
#: fisicamente inconsistente." (AGENTS_MASTER.md secao 10).
EQUILIBRIUM_RESIDUAL_RELATIVE_TOLERANCE = 1.0e-6


class EquilibriumResidualError(RuntimeError):
    """O resultado nao satisfaz o equilibrio (K @ u - F != 0 nos DOFs livres).

    Nunca deveria ocorrer para um ``Element3D`` (matriz local sempre
    simetrica, ver VAL-0001) — existe para pegar cedo qualquer futuro
    tipo de elemento ou de solver cuja matriz global nao seja de fato
    simetrica, em vez de devolver silenciosamente um
    ``AnalysisResult`` fisicamente inconsistente.
    """


@dataclass(frozen=True, eq=False)
class AnalysisResult:
    """Resultado de uma analise linear estatica.

    ``eq=False``: comparar dois resultados exigiria comparar arrays
    numpy elemento a elemento (``==`` entre dicts de ``ndarray``
    levanta ``ValueError: truth value of an array is ambiguous``) —
    a igualdade estrutural nao tem uso pratico aqui, entao o dataclass
    usa a identidade padrao em vez de gerar um ``__eq__`` quebrado.

    Atributos
    ---------
    displacements:
        ``node_id -> vetor (6,)`` de deslocamentos GLOBAIS
        (``UX,UY,UZ,RX,RY,RZ``), para todos os nos do modelo.
    reactions:
        ``node_id -> vetor (6,)`` de reacoes de apoio GLOBAIS, apenas
        para nos com :class:`~openstruct.domain.support.Support`. Os
        componentes em DOFs LIVRES desse no sao numericamente ~0 (nao
        ha reacao onde nao ha restricao) — ver
        ``docs/validation/VAL-0002-...md`` para a checagem de
        equilibrio global que depende disso.
    element_forces:
        ``element_id -> vetor (12,)`` de forcas/momentos internos nas
        extremidades do elemento, em eixos LOCAIS (mesma convencao de
        ``Element3D.local_stiffness_matrix()``): sao as acoes que o
        restante da estrutura exerce sobre cada extremidade do
        elemento para equilibra-lo.
    """

    displacements: Mapping[int, np.ndarray]
    reactions: Mapping[int, np.ndarray]
    element_forces: Mapping[int, np.ndarray]
    free_dof_equilibrium_residual: float = field(default=0.0)


def run_analysis(
    model: AnalysisModel, load_source: LoadSource, method: Method = "auto"
) -> AnalysisResult:
    """Roda uma analise linear estatica completa: monta, restringe, resolve, extrai.

    Passos (cada um delegado ao seu proprio modulo — esta funcao nao
    contem nenhuma formula de elemento finito):

    1. ``Assembly`` monta ``K_global``/``F_global``.
    2. ``BoundaryConditions`` particiona em livre/restrito e detecta
       mecanismo (``ModelInstabilityError``, deixada propagar).
    3. ``solve_linear_system`` resolve ``K_ff @ u_f = F_f``.
    4. Reconstroi o vetor de deslocamentos GLOBAL completo (DOFs
       restritos = 0 — sem recalque nesta fase).
    5. Calcula reacoes por equilibrio: ``R = K_global @ u - F_global``
       (identidade valida em qualquer sistema linear resolvido
       corretamente; ver VAL-0002 para a verificacao de que o residuo
       em DOFs LIVRES e numericamente nulo) e CONFERE que o residuo e
       de fato numericamente nulo antes de devolver qualquer resultado
       — ver :class:`EquilibriumResidualError`.
    6. Extrai esforcos internos de cada elemento a partir de seu
       proprio ``local_stiffness_matrix()``/``transformation_matrix()``.
    """
    assembly = Assembly(model)
    k_global = assembly.global_stiffness_matrix()
    f_global = assembly.global_load_vector(load_source)

    boundary_conditions = BoundaryConditions(model)
    k_ff, f_f, free, _restrained = boundary_conditions.partition(k_global, f_global)

    u_f = solve_linear_system(k_ff, f_f, method=method)

    u_global = np.zeros(model.num_dofs)
    u_global[free] = u_f

    r_global = k_global @ u_global - f_global
    free_residual = float(np.max(np.abs(r_global[free]))) if free else 0.0

    # Escala de referencia para tornar a checagem RELATIVA (um residuo
    # absoluto de 1 N e irrelevante para cargas de 1e6 N e grave para
    # cargas de 1e-3 N) — o "1.0" evita divisao por zero no caso
    # degenerado de LoadCase totalmente nulo.
    force_scale = max(float(np.max(np.abs(f_global))), 1.0) if free else 1.0
    if free and free_residual > EQUILIBRIUM_RESIDUAL_RELATIVE_TOLERANCE * force_scale:
        raise EquilibriumResidualError(
            f"Residuo de equilibrio nos DOFs livres ({free_residual!r}) excede "
            f"a tolerancia relativa ({EQUILIBRIUM_RESIDUAL_RELATIVE_TOLERANCE!r} "
            f"x escala de forca {force_scale!r}) — resultado fisicamente "
            "inconsistente, nao devolvido. Isso indica um bug na formulacao "
            "de algum elemento (matriz global nao realmente simetrica apesar "
            "de solve_linear_system assumir isso) ou no solver."
        )

    displacements = {
        node_id: u_global[model.node_dof_indices(node_id)] for node_id in model.nodes
    }
    reactions = {
        node_id: r_global[model.node_dof_indices(node_id)] for node_id in model.supports
    }

    element_forces: dict[int, np.ndarray] = {}
    for element_id, element in model.elements.items():
        idx = assembly.element_dof_indices(element)
        u_element_global = u_global[idx]
        u_element_local = element.transformation_matrix() @ u_element_global
        element_forces[element_id] = element.local_stiffness_matrix() @ u_element_local

    return AnalysisResult(
        displacements=displacements,
        reactions=reactions,
        element_forces=element_forces,
        free_dof_equilibrium_residual=free_residual,
    )
