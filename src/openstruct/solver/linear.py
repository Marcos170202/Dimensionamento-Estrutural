"""Resolucao do sistema linear ``K u = F``.

Fonte: PROGRAM_MASTER.md secao 11 ("SOLVER"): "Resolver K u = F.
Utilizar SciPy. Preparar arquitetura para: LU, Cholesky, LDLT, Sparse
solvers."

Esta fase implementa apenas o caminho denso
(``scipy.linalg.solve``). ``solve_linear_system`` e o UNICO ponto de
entrada usado por ``openstruct.analysis``/``openstruct.results`` —
trocar para um solver esparso (``scipy.sparse.linalg``) no futuro
exige mudar apenas esta funcao, nao quem a chama (NUMERICAL METHODS
AGENT, ver AGENTS_MASTER.md secao 11).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import scipy.linalg

Method = Literal["auto", "lu", "cholesky", "ldlt"]

#: Subconjunto dos valores de ``assume_a`` aceitos por
#: ``scipy.linalg.solve`` que este modulo efetivamente usa (o tipo
#: precisa ser um ``Literal``, nao ``str``, para casar com a
#: sobrecarga de tipos de ``scipy-stubs``).
_AssumeA = Literal["sym", "gen", "pos"]

#: Mapeamento method -> argumento ``assume_a`` de ``scipy.linalg.solve``.
_ASSUME_A: dict[Method, _AssumeA] = {
    "auto": "sym",
    "lu": "gen",
    "cholesky": "pos",
    "ldlt": "sym",
}


def solve_linear_system(
    k_ff: np.ndarray, f_f: np.ndarray, method: Method = "auto"
) -> np.ndarray:
    """Resolve ``K_ff @ u_f = f_f`` e devolve ``u_f``.

    Parametros
    ----------
    k_ff:
        Submatriz de rigidez restrita aos DOFs livres (ver
        ``BoundaryConditions.partition`` — espera-se que ja tenha
        passado pela checagem de estabilidade, ou seja, nao-singular).
    f_f:
        Vetor de forcas restrito aos DOFs livres.
    method:
        - ``"auto"`` (padrao): LDLT (``assume_a="sym"``) — seguro para
          qualquer matriz simetrica, nao exige positividade definida.
        - ``"lu"``: eliminacao de Gauss geral (nao assume simetria) —
          mais lento; use apenas se ``k_ff`` nao for confiavelmente
          simetrica (nao deveria ocorrer com ``Element3D``, cuja
          matriz e simetrica por construcao — ver VAL-0001).
        - ``"cholesky"``: exige ``k_ff`` simetrica positiva definida —
          mais rapido que LDLT, mas levanta erro se a matriz nao for
          PD (isso pode indicar erro de modelagem mesmo com posto
          cheio).
        - ``"ldlt"``: explicitamente LDLT (equivalente a ``"auto"``
          nesta versao).
    """
    if k_ff.ndim != 2 or k_ff.shape[0] != k_ff.shape[1]:
        raise ValueError(f"k_ff deve ser uma matriz quadrada, recebido shape {k_ff.shape!r}.")
    if f_f.ndim != 1 or f_f.shape[0] != k_ff.shape[0]:
        raise ValueError(
            f"k_ff ({k_ff.shape!r}) e f_f ({f_f.shape!r}) tem dimensoes incompativeis."
        )
    if method not in _ASSUME_A:
        raise ValueError(
            f"method deve ser um de {sorted(_ASSUME_A)}, recebido {method!r}."
        )

    result: np.ndarray = scipy.linalg.solve(k_ff, f_f, assume_a=_ASSUME_A[method])
    return result
