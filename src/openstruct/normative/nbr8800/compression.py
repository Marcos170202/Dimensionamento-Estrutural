"""Barras prismaticas submetidas a forca axial de compressao.

Fonte: ABNT NBR 8800:2024, 5.3 "Barras prismaticas submetidas a forca
axial de compressao" (paginas 45-52). Formulas extraidas por leitura
direta do PDF fornecido pelo usuario — ver rastreabilidade completa em
``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: apenas

- 5.3.1/5.3.2 — condicao de dimensionamento (``Nc,Sd <= Nc,Rd``) e a
  formula de ``Nc,Rd``;
- 5.3.3 — fator de reducao ``chi`` (ambos os ramos do indice de
  esbeltez reduzido ``lambda_0``);
- 5.3.4.1 — area efetiva igual a area bruta quando nao ha flambagem
  local (``b/t <= (b/t)lim`` para todos os elementos da secao);
- 5.3.5.1, casos a) e b) — forca axial de flambagem por FLEXAO em
  torno de cada eixo principal de inercia, para secoes com dupla
  simetria ou simetria em relacao a um ponto.

**ATENCAO — LIMITACAO DE SEGURANCA IMPORTANTE**: NBR 8800:2024, 5.3.5.1
exige que a forca axial de flambagem, ``Ne``, usada em ``lambda_0``
seja o MENOR entre TRES valores: flambagem por flexao em x (``Nex``),
flambagem por flexao em y (``Ney``) e flambagem por TORCAO (``Nez``,
5.3.5.1-c). Para secoes monossimetricas ou assimetricas, a norma exige
ainda considerar flambagem por FLEXO-TORCAO (5.3.5.2/5.3.5.3) em vez
de flexao pura em um dos eixos. **Este modulo so calcula os dois casos
de flexao pura** (:func:`flexural_buckling_force`, usavel para
qualquer um dos dois eixos) — flambagem por torcao e flexo-torcao NAO
sao implementadas aqui, pois dependem da constante de empenamento
(``Cw``) da secao, ainda nao exposta por
:class:`~openstruct.domain.section.Section`.

Isso significa: para secoes fechadas (tubulares) ou I/H com dupla
simetria onde a torcao tipicamente nao governa, usar apenas
``min(Nex, Ney)`` como ``elastic_buckling_force`` em
:func:`check_compression_member` e razoavel. Para secoes abertas de
parede fina onde torcao ou flexo-torcao PODEM governar (cantoneiras,
secoes em T, Z, C, secoes monossimetricas ou assimetricas em geral), o
chamador DEVE calcular ``Nez``/``Neyz`` externamente (ou por outro
meio) e incluir no minimo antes de chamar
:func:`check_compression_member` — do contrario o resultado pode ser
NAO CONSERVADOR (inseguro). Ver ``docs/normative/NBR8800-RULES.md``
para o registro formal desta limitacao (RULE-ID NBR8800-COMP-005).

**Fora do escopo** (ver ``docs/normative/NBR8800-RULES.md`` para a
lista completa e o motivo de cada item adiado): 5.3.4.2/5.3.4.3 (area
efetiva reduzida por flambagem local — Tabelas 4 e 5, requer
classificacao de elementos AA/AL e razoes ``b/t`` que ``Section`` nao
expressa), 5.3.5.1-c)/5.3.5.2/5.3.5.3 (torcao e flexo-torcao, ver
acima), 5.3.5.4 (cantoneiras simples conectadas por uma aba), 5.3.6
(barras compostas) e 5.3.7 (limitacao do indice de esbeltez — e uma
RECOMENDACAO, nao um estado-limite ultimo obrigatorio, mesmo status de
5.2.8 para tracao).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ._check_result import CheckResult
from ._validation import is_positive_finite
from .resistance_factors import SteelResistanceFactors


def flexural_buckling_force(
    elastic_modulus: float, moment_of_inertia: float, length: float
) -> float:
    """Forca axial de flambagem elastica por flexao em torno de um eixo principal.

    NBR 8800:2024, 5.3.5.1, casos a) e b) — mesma formula para os
    eixos x e y (``Nex = pi^2*E*Ix/Lx^2``, ``Ney = pi^2*E*Iy/Ly^2``),
    parametrizada aqui por ``moment_of_inertia``/``length`` genericos
    para nao duplicar a formula duas vezes.

    Parametros
    ----------
    elastic_modulus:
        Modulo de elasticidade do aco, ``E`` (MPa) — tipicamente
        ``material.E``.
    moment_of_inertia:
        Momento de inercia em torno do eixo de flambagem considerado
        (mm^4) — tipicamente ``section.Iy`` ou ``section.Iz``.
    length:
        Comprimento destravado associado a flexao nesse eixo (mm) —
        ``KL``, ja incluindo o fator de comprimento efetivo ``K``
        (nao calculado por este modulo; ver 4.10 para a determinacao
        de ``K``, fora do escopo desta fase).
    """
    if not is_positive_finite(elastic_modulus):
        raise ValueError(
            f"flexural_buckling_force: elastic_modulus deve ser finito e positivo, "
            f"recebido {elastic_modulus!r}."
        )
    if not is_positive_finite(moment_of_inertia):
        raise ValueError(
            f"flexural_buckling_force: moment_of_inertia deve ser finito e positivo, "
            f"recebido {moment_of_inertia!r}."
        )
    if not is_positive_finite(length):
        raise ValueError(
            f"flexural_buckling_force: length deve ser finito e positivo, recebido {length!r}."
        )
    return math.pi**2 * elastic_modulus * moment_of_inertia / length**2


def effective_area_without_local_buckling(gross_area: float) -> float:
    """Area efetiva quando nenhum elemento da secao sofre flambagem local.

    NBR 8800:2024, 5.3.4.1: "A area efetiva da secao transversal, Aef,
    deve ser considerada igual a area bruta, Ag, se todos os elementos
    componentes da secao transversal possuirem relacao entre largura e
    espessura (b/t) igual ou inferior ao valor (b/t)lim [...]".
    """
    if not is_positive_finite(gross_area):
        raise ValueError(
            f"effective_area_without_local_buckling: gross_area deve ser finita e "
            f"positiva, recebido {gross_area!r}."
        )
    return gross_area


def slenderness_parameter(gross_area: float, fy: float, elastic_buckling_force: float) -> float:
    """Indice de esbeltez reduzido, ``lambda_0`` (NBR 8800:2024, 5.3.3.2).

    ``lambda_0 = sqrt(Ag*fy / Ne)``.

    Parametros
    ----------
    gross_area:
        Area bruta da secao transversal, ``Ag`` (mm^2).
    fy:
        Resistencia ao escoamento do aco (MPa).
    elastic_buckling_force:
        Forca axial de flambagem, ``Ne`` (N) — ver ATENCAO no
        docstring do modulo sobre quais modos de flambagem este valor
        precisa contemplar.
    """
    if not is_positive_finite(gross_area):
        raise ValueError(
            f"slenderness_parameter: gross_area deve ser finita e positiva, "
            f"recebido {gross_area!r}."
        )
    if not is_positive_finite(fy):
        raise ValueError(
            f"slenderness_parameter: fy deve ser finito e positivo, recebido {fy!r}."
        )
    if not is_positive_finite(elastic_buckling_force):
        raise ValueError(
            f"slenderness_parameter: elastic_buckling_force deve ser finito e "
            f"positivo, recebido {elastic_buckling_force!r}."
        )
    return math.sqrt(gross_area * fy / elastic_buckling_force)


def reduction_factor(lambda_0: float) -> float:
    """Fator de reducao associado a resistencia a compressao, ``chi`` (NBR 8800:2024, 5.3.3.1).

    ``chi = 0,658^(lambda_0^2)`` para ``lambda_0 <= 1,5``;
    ``chi = 0,877/lambda_0^2`` para ``lambda_0 > 1,5``.

    Nota: as duas formulas (ajustes empiricos independentes, mesma
    origem das curvas de flambagem do AISC 360) NAO se encontram
    exatamente em ``lambda_0=1,5`` — ``chi=0,3899...`` pelo primeiro
    ramo contra ``chi=0,3898...`` pelo segundo, uma diferenca de
    ~1,7e-4 (~0,04% relativo). Isso e uma caracteristica conhecida da
    curva normativa (nao um erro de implementacao) — ver VAL-0007 para
    a confirmacao numerica exata.
    """
    if not math.isfinite(lambda_0) or lambda_0 < 0:
        raise ValueError(
            f"reduction_factor: lambda_0 deve ser finito e nao-negativo, "
            f"recebido {lambda_0!r}."
        )
    if lambda_0 <= 1.5:
        # float(...): tipagem de float.__pow__ inclui `Any` no stub
        # (por causa de expoentes/bases que produziriam complex) —
        # aqui lambda_0**2 >= 0 e a base e positiva, entao o resultado
        # e sempre float real; o cast e so para satisfazer mypy.
        return float(0.658 ** (lambda_0**2))
    return 0.877 / lambda_0**2


@dataclass(frozen=True, slots=True)
class CompressionCheckResult(CheckResult):
    """Resultado da verificacao de uma barra comprimida (NBR 8800:2024, 5.3.1/5.3.2).

    Atributos
    ---------
    nc_sd:
        Forca axial de compressao solicitante de calculo (N).
    lambda_0:
        Indice de esbeltez reduzido (5.3.3.2).
    chi:
        Fator de reducao associado a resistencia a compressao (5.3.3.1).
    nc_rd:
        Forca axial de compressao resistente de calculo (N):
        ``chi*Aef*fy/gamma_a1``.
    """

    nc_sd: float
    lambda_0: float
    chi: float
    nc_rd: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.nc_sd):
            raise ValueError(
                f"CompressionCheckResult.nc_sd deve ser finito, recebido {self.nc_sd!r}."
            )
        if not math.isfinite(self.lambda_0) or self.lambda_0 < 0:
            raise ValueError(
                f"CompressionCheckResult.lambda_0 deve ser finito e nao-negativo, "
                f"recebido {self.lambda_0!r}."
            )
        if not (0.0 < self.chi <= 1.0):
            raise ValueError(
                f"CompressionCheckResult.chi deve satisfazer 0 < chi <= 1, "
                f"recebido {self.chi!r}."
            )
        if not is_positive_finite(self.nc_rd):
            raise ValueError(
                f"CompressionCheckResult.nc_rd deve ser finito e positivo, "
                f"recebido {self.nc_rd!r}."
            )

    @property
    def sd(self) -> float:
        """Alias generico de :attr:`nc_sd` — ver :class:`CheckResult`."""
        return self.nc_sd

    @property
    def rd(self) -> float:
        """Alias generico de :attr:`nc_rd` — ver :class:`CheckResult`."""
        return self.nc_rd


def check_compression_member(
    nc_sd: float,
    gross_area: float,
    effective_area: float,
    fy: float,
    elastic_buckling_force: float,
    resistance_factors: SteelResistanceFactors,
) -> CompressionCheckResult:
    """Verifica uma barra prismatica comprimida (NBR 8800:2024, 5.3.1/5.3.2).

    Ver ATENCAO no docstring do modulo: ``elastic_buckling_force``
    precisa ja ser o menor valor entre todos os modos de flambagem
    aplicaveis a secao real — este modulo nao valida isso, apenas usa
    o valor fornecido.

    Parametros
    ----------
    nc_sd:
        Forca axial de compressao solicitante de calculo (N).
    gross_area:
        Area bruta da secao transversal, ``Ag`` (mm^2) — tipicamente
        ``section.A``.
    effective_area:
        Area efetiva da secao transversal, ``Aef`` (mm^2) — ver
        :func:`effective_area_without_local_buckling` para o caso sem
        flambagem local (5.3.4.1) ou um valor calculado externamente
        para o caso geral (fora do escopo desta fase).
    fy:
        Resistencia ao escoamento do aco (MPa) — tipicamente
        ``material.fy``.
    elastic_buckling_force:
        Forca axial de flambagem, ``Ne`` (N) — ver
        :func:`flexural_buckling_force` e a ATENCAO de seguranca no
        docstring do modulo.
    resistance_factors:
        Coeficientes de ponderacao da resistencia (NBR 8800:2024,
        4.9.2, Tabela 3) — usa apenas ``gamma_a1`` (5.3.2 e um
        estado-limite de instabilidade, nao de ruptura).

    Retorna
    -------
    :class:`CompressionCheckResult` com ``lambda_0``, ``chi``,
    ``nc_rd``, a taxa de utilizacao e se a condicao de 5.3.1 e
    atendida.
    """
    if not math.isfinite(nc_sd):
        raise ValueError(f"check_compression_member: nc_sd deve ser finito, recebido {nc_sd!r}.")
    if not is_positive_finite(gross_area):
        raise ValueError(
            f"check_compression_member: gross_area deve ser finita e positiva, "
            f"recebido {gross_area!r}."
        )
    if not is_positive_finite(effective_area):
        raise ValueError(
            f"check_compression_member: effective_area deve ser finita e positiva, "
            f"recebido {effective_area!r}."
        )
    if effective_area > gross_area:
        # Aef <= Ag sempre (5.3.4: Aef=Ag no melhor caso, ou reduzida
        # por flambagem local) — Aef > Ag e sempre um erro de
        # modelagem, nunca um caso normativo valido (mesmo raciocinio
        # de Ae/Ag em check_tension_member).
        raise ValueError(
            f"check_compression_member: effective_area ({effective_area!r}) nao pode "
            f"ser maior que gross_area ({gross_area!r})."
        )
    if not is_positive_finite(fy):
        raise ValueError(
            f"check_compression_member: fy deve ser finito e positivo, recebido {fy!r}."
        )

    lambda_0 = slenderness_parameter(gross_area, fy, elastic_buckling_force)
    chi = reduction_factor(lambda_0)
    nc_rd = chi * effective_area * fy / resistance_factors.gamma_a1
    return CompressionCheckResult(nc_sd=nc_sd, lambda_0=lambda_0, chi=chi, nc_rd=nc_rd)
