"""ABNT NBR 8800:2024 — Projeto de estruturas de aco e de estruturas
mistas de aco e concreto de edificacoes.

Fonte: PDF fornecido pelo usuario na raiz do repositorio (terceira
edicao, 02.10.2024). Rastreabilidade completa de cada regra
implementada em ``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: verificacao de barras prismaticas tracionadas
(secao 5.2, casos de escoamento da secao bruta e ruptura da secao
liquida sem furos), verificacao de barras prismaticas comprimidas
(secao 5.3, flambagem por flexao E por torcao para secoes com dupla
simetria ou simetricas em relacao a um ponto — ver ATENCAO de
seguranca na docstring de ``compression`` sobre flexo-torcao em
secoes monossimetricas/assimetricas, ainda nao implementada) e os
coeficientes de ponderacao da resistencia do aco estrutural (4.9.2,
Tabela 3). Ver docstrings de ``tension``, ``compression`` e
``resistance_factors`` para os limites exatos do escopo.
"""

from __future__ import annotations

from .compression import (
    CompressionCheckResult,
    check_compression_member,
    effective_area_without_local_buckling,
    flexural_buckling_force,
    polar_radius_of_gyration,
    reduction_factor,
    slenderness_parameter,
    torsional_buckling_force,
)
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
    "CompressionCheckResult",
    "LoadCombinationClass",
    "SteelResistanceFactors",
    "TensionCheckResult",
    "check_compression_member",
    "check_tension_member",
    "effective_area_without_local_buckling",
    "flexural_buckling_force",
    "net_area_without_holes",
    "polar_radius_of_gyration",
    "reduction_factor",
    "slenderness_parameter",
    "steel_resistance_factors",
    "torsional_buckling_force",
]
