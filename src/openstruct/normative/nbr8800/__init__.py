"""ABNT NBR 8800:2024 — Projeto de estruturas de aco e de estruturas
mistas de aco e concreto de edificacoes.

Fonte: PDF fornecido pelo usuario na raiz do repositorio (terceira
edicao, 02.10.2024). Rastreabilidade completa de cada regra
implementada em ``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: apenas a verificacao de barras prismaticas
tracionadas (secao 5.2, casos de escoamento da secao bruta e ruptura
da secao liquida sem furos) e os coeficientes de ponderacao da
resistencia do aco estrutural (4.9.2, Tabela 3). Ver docstrings de
``tension`` e ``resistance_factors`` para os limites exatos do escopo.
"""

from __future__ import annotations

from .resistance_factors import (
    LoadCombinationClass,
    SteelResistanceFactors,
    steel_resistance_factors,
)
from .tension import (
    TensionCheckResult,
    check_tension_member,
    net_area_without_holes,
)

__all__ = [
    "LoadCombinationClass",
    "SteelResistanceFactors",
    "TensionCheckResult",
    "check_tension_member",
    "net_area_without_holes",
    "steel_resistance_factors",
]
