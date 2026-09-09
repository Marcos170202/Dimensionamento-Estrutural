"""Barras prismaticas submetidas a forca axial de tracao.

Fonte: ABNT NBR 8800:2024, 5.2 "Barras prismaticas submetidas a forca
axial de tracao" (paginas 38-44). Formulas extraidas por leitura
direta do PDF fornecido pelo usuario — ver rastreabilidade completa em
``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: apenas

- 5.2.1.2 — condicao de dimensionamento (``Nt,Sd <= Nt,Rd``);
- 5.2.2 — forca axial resistente de calculo, casos a) escoamento da
  secao bruta e b) ruptura da secao liquida;
- 5.2.4.2 — area liquida igual a area bruta quando nao ha furos.

**Fora do escopo** (deixado para uma fase normativa futura, RULE-ID a
definir): 5.2.3/5.2.5 (calculo do coeficiente de reducao ``Ct`` para
ligacoes soldadas/parafusadas — requer modelagem de furos/soldas, que
o dominio geometrico atual (``Section``) nao expressa), 5.2.6 (chapas
ligadas por pino), 5.2.7 (barras redondas com extremidades rosqueadas)
e 5.2.8 (limitacao do indice de esbeltez — e uma RECOMENDACAO, nao um
estado-limite ultimo obrigatorio, e depende de ``Section`` expor raio
de giracao, ainda nao implementado).

Por isso, esta API recebe a area liquida efetiva (``Ae``) diretamente
como parametro em vez de calcula-la — o chamador informa
``net_area_without_holes(section.A)`` no caso mais simples (sem furos,
5.2.4.2) ou um valor ja calculado externamente para os demais casos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ._validation import is_positive_finite
from .resistance_factors import SteelResistanceFactors


def net_area_without_holes(gross_area: float) -> float:
    """Area liquida quando nao ha furos na regiao considerada.

    NBR 8800:2024, 5.2.4.2: "Em regioes em que nao existam furos, a
    area liquida, An, deve ser considerada igual a area bruta da secao
    transversal, Ag."
    """
    if not is_positive_finite(gross_area):
        raise ValueError(
            f"net_area_without_holes: gross_area deve ser finita e positiva, "
            f"recebido {gross_area!r}."
        )
    return gross_area


@dataclass(frozen=True, slots=True)
class TensionCheckResult:
    """Resultado da verificacao de uma barra tracionada (NBR 8800:2024, 5.2.1/5.2.2).

    Atributos
    ---------
    nt_sd:
        Forca axial de tracao solicitante de calculo (N).
    nt_rd_yield:
        Forca axial resistente de calculo por escoamento da secao
        bruta (5.2.2-a): ``Ag*fy/gamma_a1``.
    nt_rd_rupture:
        Forca axial resistente de calculo por ruptura da secao
        liquida (5.2.2-b): ``Ae*fu/gamma_a2``.
    """

    nt_sd: float
    nt_rd_yield: float
    nt_rd_rupture: float

    def __post_init__(self) -> None:
        for name in ("nt_sd", "nt_rd_yield", "nt_rd_rupture"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(
                    f"TensionCheckResult.{name} deve ser finito, recebido {value!r}."
                )
        if not (self.nt_rd_yield > 0):
            raise ValueError(
                f"TensionCheckResult.nt_rd_yield deve ser positivo, "
                f"recebido {self.nt_rd_yield!r}."
            )
        if not (self.nt_rd_rupture > 0):
            raise ValueError(
                f"TensionCheckResult.nt_rd_rupture deve ser positivo, "
                f"recebido {self.nt_rd_rupture!r}."
            )

    @property
    def nt_rd(self) -> float:
        """Forca axial de tracao resistente de calculo — o menor dos
        dois estados-limite (NBR 8800:2024, 5.2.2, "caput": "e o menor
        dos valores obtidos")."""
        return min(self.nt_rd_yield, self.nt_rd_rupture)

    @property
    def governing(self) -> Literal["escoamento_secao_bruta", "ruptura_secao_liquida"]:
        """Qual dos dois estados-limite de 5.2.2 governa (produz o menor Nt,Rd)."""
        if self.nt_rd_yield <= self.nt_rd_rupture:
            return "escoamento_secao_bruta"
        return "ruptura_secao_liquida"

    @property
    def utilization(self) -> float:
        """Taxa de utilizacao ``Nt,Sd / Nt,Rd`` (<=1 significa que a
        condicao de 5.2.1.2 e atendida)."""
        return self.nt_sd / self.nt_rd

    @property
    def is_ok(self) -> bool:
        """Condicao de dimensionamento de 5.2.1.2: ``Nt,Sd <= Nt,Rd``."""
        return self.nt_sd <= self.nt_rd


def check_tension_member(
    nt_sd: float,
    gross_area: float,
    effective_net_area: float,
    fy: float,
    fu: float,
    resistance_factors: SteelResistanceFactors,
) -> TensionCheckResult:
    """Verifica uma barra prismatica tracionada (NBR 8800:2024, 5.2.1.2/5.2.2).

    Parametros
    ----------
    nt_sd:
        Forca axial de tracao solicitante de calculo (N) — tipicamente
        o esforco axial de uma combinacao ultima de acoes ja ponderada
        (fora do escopo deste modulo: a ponderacao das acoes em si,
        ver 4.8.6/4.8.7, e a extracao do esforco a partir de um
        ``AnalysisResult``).
    gross_area:
        Area bruta da secao transversal, ``Ag`` (mm^2) — tipicamente
        ``section.A``.
    effective_net_area:
        Area liquida efetiva, ``Ae`` (mm^2) — ver
        :func:`net_area_without_holes` para o caso sem furos (5.2.4.2)
        ou um valor calculado externamente para os demais casos (fora
        do escopo desta fase, ver docstring do modulo).
    fy:
        Resistencia ao escoamento do aco (MPa) — tipicamente
        ``material.fy``.
    fu:
        Resistencia do aco a ruptura (MPa) — tipicamente
        ``material.fu``.
    resistance_factors:
        Coeficientes de ponderacao da resistencia (NBR 8800:2024,
        4.9.2, Tabela 3) — ver
        :func:`~openstruct.normative.nbr8800.resistance_factors.steel_resistance_factors`.

    Retorna
    -------
    :class:`TensionCheckResult` com os dois valores de Nt,Rd, o
    estado-limite governante, a taxa de utilizacao e se a condicao de
    5.2.1.2 e atendida.
    """
    if not math.isfinite(nt_sd):
        raise ValueError(f"check_tension_member: nt_sd deve ser finito, recebido {nt_sd!r}.")
    if not is_positive_finite(gross_area):
        raise ValueError(
            f"check_tension_member: gross_area deve ser finita e positiva, "
            f"recebido {gross_area!r}."
        )
    if not is_positive_finite(effective_net_area):
        raise ValueError(
            f"check_tension_member: effective_net_area deve ser finita e positiva, "
            f"recebido {effective_net_area!r}."
        )
    if effective_net_area > gross_area:
        # Ae = Ct*An e An <= Ag sempre (An e, na pior das hipoteses, a
        # propria Ag — 5.2.4.2); Ct tambem e <= 1 em todos os casos de
        # 5.2.5. Uma area liquida efetiva maior que a bruta e sempre um
        # erro de modelagem, nao um caso normativo valido.
        raise ValueError(
            f"check_tension_member: effective_net_area ({effective_net_area!r}) nao "
            f"pode ser maior que gross_area ({gross_area!r})."
        )
    if not is_positive_finite(fy):
        raise ValueError(f"check_tension_member: fy deve ser finito e positivo, recebido {fy!r}.")
    if not is_positive_finite(fu):
        raise ValueError(f"check_tension_member: fu deve ser finito e positivo, recebido {fu!r}.")

    nt_rd_yield = gross_area * fy / resistance_factors.gamma_a1
    nt_rd_rupture = effective_net_area * fu / resistance_factors.gamma_a2
    return TensionCheckResult(nt_sd=nt_sd, nt_rd_yield=nt_rd_yield, nt_rd_rupture=nt_rd_rupture)
