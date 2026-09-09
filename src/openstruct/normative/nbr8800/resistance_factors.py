"""Coeficientes de ponderacao da resistencia do aco estrutural (ELU).

Fonte: ABNT NBR 8800:2024, 4.9.2 "Coeficientes de ponderacao das
resistencias no estado-limite ultimo (ELU)", Tabela 3 "Valores dos
coeficientes de ponderacao das resistencias dos materiais gamma_m"
(pagina 25). Valores extraidos por leitura direta do PDF fornecido
pelo usuario (``NBR 8800 - 2024 - ...pdf`` na raiz do repositorio) —
ver rastreabilidade completa em ``docs/normative/NBR8800-RULES.md``.

Escopo: apenas as colunas "Aco estrutural" (gamma_a1 = escoamento e
instabilidade; gamma_a2 = ruptura) da Tabela 3. As colunas de concreto
(gamma_c) e aco das armaduras (gamma_s) sao omitidas nesta fase — nao
ha elementos mistos de aco e concreto implementados ainda (ver
PROGRAM_MASTER.md, "STEEL DESIGN" e futuros marcos de elementos
mistos).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ._validation import is_positive_finite


class LoadCombinationClass(Enum):
    """Classificacao da combinacao ultima de acoes — colunas de linha
    da Tabela 3 (NBR 8800:2024, 4.9.2): "Normais", "Especiais ou de
    construcao" e "Excepcionais" (ver tambem 4.8.6/4.8.7 para a
    classificacao das proprias combinacoes de acoes, fora do escopo
    desta primeira fase normativa)."""

    NORMAL = "normal"
    ESPECIAL_OU_CONSTRUCAO = "especial_ou_construcao"
    EXCEPCIONAL = "excepcional"


@dataclass(frozen=True, slots=True)
class SteelResistanceFactors:
    """Coeficientes de ponderacao da resistencia do aco estrutural
    (NBR 8800:2024, 4.9.2, Tabela 3, coluna "Aco estrutural").

    Atributos
    ---------
    gamma_a1:
        Coeficiente para estados-limite ultimos relacionados a
        escoamento e instabilidade.
    gamma_a2:
        Coeficiente para estados-limite ultimos relacionados a
        ruptura.
    """

    gamma_a1: float
    gamma_a2: float

    def __post_init__(self) -> None:
        # is_positive_finite() rejeita NaN e infinito — mais estrito
        # que o "not (valor > 0)" de material.py/section.py, que
        # rejeita NaN mas nao infinito (ver docstring de
        # is_positive_finite para o porque disso ser deliberado aqui).
        if not is_positive_finite(self.gamma_a1):
            raise ValueError(
                f"SteelResistanceFactors.gamma_a1 deve ser finito e positivo, "
                f"recebido {self.gamma_a1!r}."
            )
        if not is_positive_finite(self.gamma_a2):
            raise ValueError(
                f"SteelResistanceFactors.gamma_a2 deve ser finito e positivo, "
                f"recebido {self.gamma_a2!r}."
            )


#: NBR 8800:2024, 4.9.2, Tabela 3 (RULE-ID NBR8800-RES-001 — ver
#: docs/normative/NBR8800-RULES.md). Linhas "Normais" e "Especiais ou
#: de construcao" tem os mesmos valores de gamma_a1/gamma_a2 na
#: tabela; "Excepcionais" usa valores reduzidos (coerente com a menor
#: probabilidade de ocorrencia simultanea considerada pela norma).
_TABELA_3_ACO_ESTRUTURAL: dict[LoadCombinationClass, SteelResistanceFactors] = {
    LoadCombinationClass.NORMAL: SteelResistanceFactors(gamma_a1=1.10, gamma_a2=1.35),
    LoadCombinationClass.ESPECIAL_OU_CONSTRUCAO: SteelResistanceFactors(
        gamma_a1=1.10, gamma_a2=1.35
    ),
    LoadCombinationClass.EXCEPCIONAL: SteelResistanceFactors(gamma_a1=1.00, gamma_a2=1.15),
}


def steel_resistance_factors(combination_class: LoadCombinationClass) -> SteelResistanceFactors:
    """Devolve (gamma_a1, gamma_a2) para a classe de combinacao dada.

    NBR 8800:2024, 4.9.2, Tabela 3, coluna "Aco estrutural".
    """
    return _TABELA_3_ACO_ESTRUTURAL[combination_class]
