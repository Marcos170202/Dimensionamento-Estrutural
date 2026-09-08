"""Particionamento livre/restrito e deteccao de modelo instavel.

Fonte: PROGRAM_MASTER.md secao 9 ("BOUNDARY CONDITIONS"): "Implementar
restricoes: UX, UY, UZ, RX, RY, RZ. Detectar modelos instaveis." e
AGENTS_MASTER.md secao 10 (alerta do ENGINEERING QA AGENT): "Matriz
global e singular."

Fase atual: apenas apoio com deslocamento prescrito NULO (ver
``domain/support.py``) — particionar em `(livre, restrito)` e
suficiente; recalque (prescrito != 0) exigiria um terceiro termo
(``K_fr @ u_r``) no vetor de forcas efetivo, fora do escopo aqui.
"""

from __future__ import annotations

import numpy as np

from ..domain.model import AnalysisModel


class ModelInstabilityError(ValueError):
    """Levantada quando o sistema restrito e singular (modelo possui mecanismo).

    Corresponde ao alerta "Modelo possui mecanismo." /
    "Matriz global e singular." do ENGINEERING QA AGENT
    (AGENTS_MASTER.md secao 10).
    """


class BoundaryConditions:
    """Particiona o sistema global em graus de liberdade livres e restritos."""

    def __init__(self, model: AnalysisModel) -> None:
        self.model = model

    def restrained_dof_indices(self) -> list[int]:
        """Indices globais (ordenados, sem repeticao) restringidos por algum apoio."""
        indices = {
            self.model.dof_index(node_id, dof)
            for node_id, support in self.model.supports.items()
            for dof in support.restrained_dofs()
        }
        return sorted(indices)

    def free_dof_indices(self) -> list[int]:
        """Indices globais que NAO estao restringidos por nenhum apoio."""
        restrained = set(self.restrained_dof_indices())
        return [i for i in range(self.model.num_dofs) if i not in restrained]

    def partition(
        self, k_global: np.ndarray, f_global: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, list[int], list[int]]:
        """Particiona ``(K_global, F_global)`` em ``(K_ff, F_f, livres, restritos)``.

        Levanta :class:`ModelInstabilityError` se nao houver nenhum
        DOF livre, ou se ``K_ff`` for singular (mecanismo).
        """
        free = self.free_dof_indices()
        restrained = self.restrained_dof_indices()

        if not free:
            raise ModelInstabilityError(
                "Modelo nao possui nenhum grau de liberdade livre — todos os "
                "DOFs estao restringidos, nao ha nada para o solver resolver."
            )

        k_ff = k_global[np.ix_(free, free)]
        f_f = f_global[free]
        self._check_stability(k_ff)
        return k_ff, f_f, free, restrained

    @staticmethod
    def _check_stability(k_ff: np.ndarray) -> None:
        # NUMERICAL METHODS AGENT / CODE REVIEW AGENT: matrix_rank() usa SVD
        # (O(n^3)) so para detectar singularidade, e run_analysis chama
        # solve_linear_system() logo em seguida — ou seja, DUAS fatoracoes
        # O(n^3) da mesma matriz por analise. E deliberado nesta fase: um
        # solve "otimista" (sem checagem previa) pode "suceder" numericamente
        # em cima de uma matriz quase-singular e devolver deslocamentos
        # absurdos sem levantar nenhum erro (LDLT/Cholesky nao garantem
        # detectar singularidade como matrix_rank via SVD garante). Por
        # PROGRAM_MASTER.md secao 35 ("CORRECAO -> VALIDACAO -> RASTREABILIDADE
        # -> PERFORMANCE -> INTERFACE"), a deteccao confiavel de mecanismo
        # vem antes de evitar uma fatoracao redundante. Otimizar isso (ex.:
        # reaproveitar a fatoracao do proprio solver, ou pivoteamento
        # explicito) fica para quando performance for de fato um gargalo
        # medido, nao uma preocupacao especulativa.
        rank = np.linalg.matrix_rank(k_ff)
        if rank < k_ff.shape[0]:
            raise ModelInstabilityError(
                f"Matriz de rigidez restrita e singular (posto {rank} de "
                f"{k_ff.shape[0]}) — modelo possui mecanismo. Verifique se "
                "todos os nos tem apoio e/ou conectividade suficiente para "
                "impedir deslocamento de corpo rigido."
            )
