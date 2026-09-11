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
secoes monossimetricas/assimetricas, ainda nao implementada), a
limitacao RECOMENDADA (nao obrigatoria) do indice de esbeltez de
barras tracionadas/comprimidas individuais (5.2.8.1/5.3.7.1), a forca
cortante resistente de calculo de secoes I/H/U fletidas em relacao ao
eixo perpendicular a alma (5.4.1.3/5.4.3.1 — ver docstring de
``shear`` para o restante de 5.4, ainda fora do escopo), a flambagem
lateral com torcao (FLT) de secoes I/H/U duplamente simetricas
fletidas no eixo de maior momento de inercia (5.4.1.3/Anexo D,
D.2.8-a — ver ATENCAO na docstring de ``flexure`` sobre FLM/FLA
ainda nao implementados) e os coeficientes de ponderacao da
resistencia do aco estrutural (4.9.2, Tabela 3). Ver docstrings de
``tension``, ``compression``, ``slenderness``, ``shear``, ``flexure``
e ``resistance_factors`` para os limites exatos do escopo.
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
from .flexure import (
    FlexureCheckResult,
    check_lateral_torsional_buckling,
    flexural_resistance,
    lateral_torsional_buckling_moment,
    lateral_torsional_buckling_slenderness_limit,
    moment_gradient_factor_doubly_symmetric,
    warping_constant_i_section,
)
from .resistance_factors import (
    LoadCombinationClass,
    SteelResistanceFactors,
    steel_resistance_factors,
)
from .shear import (
    ShearCheckResult,
    check_shear_major_axis,
    effective_shear_area_major_axis,
    plastic_shear_force,
    shear_buckling_coefficient,
    shear_resistance,
)
from .slenderness import (
    COMPRESSION_SLENDERNESS_LIMIT,
    TENSION_SLENDERNESS_LIMIT,
    SlendernessCheckResult,
    check_compression_slenderness,
    check_tension_slenderness,
    slenderness_ratio,
)
from .tension import (
    TensionCheckResult,
    check_tension_member,
    net_area_without_holes,
)

__all__ = [
    "COMPRESSION_SLENDERNESS_LIMIT",
    "TENSION_SLENDERNESS_LIMIT",
    "CompressionCheckResult",
    "FlexureCheckResult",
    "LoadCombinationClass",
    "ShearCheckResult",
    "SlendernessCheckResult",
    "SteelResistanceFactors",
    "TensionCheckResult",
    "check_compression_member",
    "check_compression_slenderness",
    "check_lateral_torsional_buckling",
    "check_shear_major_axis",
    "check_tension_member",
    "check_tension_slenderness",
    "effective_area_without_local_buckling",
    "effective_shear_area_major_axis",
    "flexural_buckling_force",
    "flexural_resistance",
    "lateral_torsional_buckling_moment",
    "lateral_torsional_buckling_slenderness_limit",
    "moment_gradient_factor_doubly_symmetric",
    "net_area_without_holes",
    "plastic_shear_force",
    "polar_radius_of_gyration",
    "reduction_factor",
    "shear_buckling_coefficient",
    "shear_resistance",
    "slenderness_parameter",
    "slenderness_ratio",
    "steel_resistance_factors",
    "torsional_buckling_force",
    "warping_constant_i_section",
]
