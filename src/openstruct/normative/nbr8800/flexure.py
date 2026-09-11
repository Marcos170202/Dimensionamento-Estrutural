"""Barras prismaticas submetidas a momento fletor.

Fonte: ABNT NBR 8800:2024, 5.4.2 "Momento fletor resistente de
calculo" (paginas 54-56) e Anexo D "Momento fletor resistente de
calculo de vigas de alma nao esbelta", D.1/D.2/D.2.8-a/D.3 (paginas
137, 144-147). Formulas extraidas por leitura direta do PDF fornecido
pelo usuario — ver rastreabilidade completa em
``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: apenas o estado-limite de FLAMBAGEM LATERAL COM
TORCAO (FLT), para secoes I, H com dois eixos de simetria e secoes U
nao sujeitas a momento de torcao, fletidas em relacao ao eixo de MAIOR
momento de inercia (Tabela D.1, primeira linha, coluna FLT) — o caso
mais comum e o unico estado-limite aplicavel quando o eixo de flexao
NAO e o de maior momento de inercia (D.2.8-g). Cobre:

- 5.4.2.1/5.4.1.3 — condicao de dimensionamento (``Msd <= Mrd``);
- 5.4.2.3-a — fator de modificacao para diagrama de momento fletor nao
  uniforme, ``Cb``, caso geral (``Rm=1,0`` para secoes duplamente
  simetricas — os demais casos, b) e c), de 5.4.2.3/5.4.2.4 nao sao
  implementados, ver abaixo);
- D.2.1/D.2.8-a — curva de 3 trechos do momento fletor resistente de
  calculo `Mrd` para FLT (plastificacao / escoamento com tensao
  residual / flambagem elastica), com ``Mcr``/``lambda_r`` calculados
  conforme D.2.8-a (formula generica para secoes I/H/U com dupla
  simetria).

**ATENCAO — LIMITACAO DE SEGURANCA IMPORTANTE**: NBR 8800:2024, 5.4.2.1
exige que ``Mrd`` considere, conforme o caso, TODOS os estados-limite
aplicaveis: FLT, flambagem local da mesa comprimida (FLM), flambagem
local da alma (FLA), flambagem local da aba (cantoneiras), flambagem
local da parede do tubo e escoamento da mesa tracionada — tomando o
MENOR valor entre os que se aplicam (mesmo principio de
``Ne=min(Nex,Ney,Nez)`` em ``compression.py``). Este modulo implementa
**apenas FLT**. Para uma secao real, se FLM ou FLA governar (Mrd menor
que o de FLT — tipico de mesas ou almas muito esbeltas), o valor
retornado por :func:`check_lateral_torsional_buckling` seria NAO
CONSERVADOR se tratado como o `Mrd` final da barra. Ate que FLM/FLA
sejam implementados (incrementos futuros), o resultado desta funcao
deve ser interpretado apenas como a parcela de FLT — nunca como o
`Mrd` completo de 5.4.2.1 — ver ``docs/normative/NBR8800-RULES.md``
(RULE-ID ``NBR8800-FLEX-004``) para o registro formal desta limitacao.

Tambem NAO implementado (fora do escopo desta fase, ver
``docs/normative/NBR8800-RULES.md`` para a lista completa e o motivo
de cada item): 5.4.2.2 (limite ``Mrd <= 1,50*W*fy/gamma_a1`` para
garantir validade da analise elastica — deve ser aplicado pelo
chamador ao ``Mrd`` GOVERNANTE final, apos FLM/FLA existirem, para
nao ser aplicado 3 vezes por engano); 5.4.2.3, casos b) e c), e
5.4.2.4/5.4.2.5 (``Cb`` para balancos e para secoes monossimetricas —
apenas o caso geral duplamente simetrico, 5.4.2.3-a, esta aqui);
5.4.2.6 (furos na mesa tracionada); demais linhas da Tabela D.1
(secoes monossimetricas, tubulares/caixao, T, cantoneiras duplas,
solidas) e flexao em torno do eixo de menor momento de inercia (D.2.5,
onde FLT nao se aplica — D.2.8-g); Anexo E (vigas de ALMA ESBELTA —
substitui Anexo D inteiramente quando a alma nao satisfaz D.1.2, um
requisito de aplicabilidade que este modulo NAO verifica: o chamador e
responsavel por confirmar que a secao e de alma nao esbelta antes de
usar estas formulas); Anexos F/G/H/I; 5.5 (combinacao de esforcos).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ._check_result import CheckResult
from ._validation import is_positive_finite


def moment_gradient_factor_doubly_symmetric(
    m_max: float, m_a: float, m_b: float, m_c: float
) -> float:
    """Fator de modificacao para diagrama de momento fletor nao uniforme, ``Cb``.

    NBR 8800:2024, 5.4.2.3-a (caso geral, pagina 54):
    ``Cb = 12,5*Mmax / (2,5*Mmax + 3*MA + 4*MB + 3*MC) * Rm``, com
    ``Rm=1,0`` para secoes duplamente simetricas (unico caso coberto
    aqui — a formula geral de ``Rm`` para secoes monossimetricas com
    curvatura reversa, ``0,5+2*(Iy,m/Iy)^2``, nao esta implementada).
    Nao cobre os casos b) (balancos com carga transversal
    uniformemente distribuida) nem c) (balancos em geral) de 5.4.2.3,
    nem 5.4.2.4/5.4.2.5 (formulas alternativas para secoes I/U com uma
    mesa livre para se deslocar lateralmente).

    Parametros
    ----------
    m_max:
        Valor do momento fletor maximo solicitante de calculo, em
        modulo, no comprimento destravado (N.mm).
    m_a, m_b, m_c:
        Valores do momento fletor solicitante de calculo, em modulo, a
        1/4, no meio (1/2) e a 3/4 do comprimento destravado,
        respectivamente, medidos a partir de uma mesma extremidade
        (N.mm). Podem ser zero (ex.: proximo a um apoio simples), mas
        nao negativos (valores "em modulo", por definicao da norma).
    """
    if not is_positive_finite(m_max):
        raise ValueError(
            f"moment_gradient_factor_doubly_symmetric: m_max deve ser finito e "
            f"positivo, recebido {m_max!r}."
        )
    for name, value in (("m_a", m_a), ("m_b", m_b), ("m_c", m_c)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(
                f"moment_gradient_factor_doubly_symmetric: {name} deve ser finito e "
                f"nao-negativo, recebido {value!r}."
            )
    return 12.5 * m_max / (2.5 * m_max + 3.0 * m_a + 4.0 * m_b + 3.0 * m_c)


def warping_constant_i_section(
    minor_axis_moment_of_inertia: float, total_depth: float, flange_thickness: float
) -> float:
    """Constante de empenamento, ``Cw``, para secoes I (NBR 8800:2024, D.2.8-a).

    ``Cw = Iy*(d-tf)^2/4``. Util para obter ``Cw`` de uma secao I
    quando ``Section.Cw`` (opcional) nao esta disponivel. Nao cobre a
    formula de ``Cw`` para secoes U, tambem dada em D.2.8-a (mais
    complexa, envolve as larguras/espessuras individuais da mesa e
    alma).

    Parametros
    ----------
    minor_axis_moment_of_inertia:
        Momento de inercia em relacao ao eixo de menor momento de
        inercia, ``Iy`` (mm^4) — tipicamente ``section.Iy`` (ver nota
        de convencao de eixos no docstring de
        :func:`check_lateral_torsional_buckling`).
    total_depth:
        Altura externa da secao, ``d`` (mm).
    flange_thickness:
        Espessura da mesa, ``tf`` (mm).
    """
    if not is_positive_finite(minor_axis_moment_of_inertia):
        raise ValueError(
            f"warping_constant_i_section: minor_axis_moment_of_inertia deve ser "
            f"finito e positivo, recebido {minor_axis_moment_of_inertia!r}."
        )
    if not is_positive_finite(total_depth):
        raise ValueError(
            f"warping_constant_i_section: total_depth deve ser finito e positivo, "
            f"recebido {total_depth!r}."
        )
    if not is_positive_finite(flange_thickness):
        raise ValueError(
            f"warping_constant_i_section: flange_thickness deve ser finito e "
            f"positivo, recebido {flange_thickness!r}."
        )
    if flange_thickness >= total_depth:
        # tf < d sempre para qualquer secao I real (a mesa e uma
        # fracao pequena da altura total) — mesmo raciocinio de
        # web_clear_height<=total_depth em shear.py.
        raise ValueError(
            f"warping_constant_i_section: flange_thickness ({flange_thickness!r}) "
            f"deve ser menor que total_depth ({total_depth!r})."
        )
    return minor_axis_moment_of_inertia * (total_depth - flange_thickness) ** 2 / 4.0


def lateral_torsional_buckling_moment(
    cb: float,
    elastic_modulus: float,
    minor_axis_moment_of_inertia: float,
    torsion_constant: float,
    warping_constant: float,
    unbraced_length: float,
) -> float:
    """Momento fletor critico de flambagem elastica por FLT, ``Mcr`` (NBR 8800:2024, D.2.8-a).

    ``Mcr = (Cb*pi^2*E*Iy/Lb^2) * sqrt((Cw/Iy)*(1 + 0,039*J*Lb^2/Cw))``.

    Parametros
    ----------
    cb:
        Fator de modificacao para diagrama de momento fletor nao
        uniforme — ver :func:`moment_gradient_factor_doubly_symmetric`.
    elastic_modulus:
        Modulo de elasticidade do aco, ``E`` (MPa).
    minor_axis_moment_of_inertia:
        Momento de inercia em relacao ao eixo de menor momento de
        inercia, ``Iy`` (mm^4) — ver nota de convencao de eixos no
        docstring de :func:`check_lateral_torsional_buckling`.
    torsion_constant:
        Constante de torcao de Saint-Venant, ``J`` (mm^4).
    warping_constant:
        Constante de empenamento, ``Cw`` (mm^6) — ver
        :func:`warping_constant_i_section` para secoes I.
    unbraced_length:
        Comprimento destravado a flambagem lateral com torcao, ``Lb``
        (mm).
    """
    if not is_positive_finite(cb):
        raise ValueError(
            f"lateral_torsional_buckling_moment: cb deve ser finito e positivo, recebido {cb!r}."
        )
    if not is_positive_finite(elastic_modulus):
        raise ValueError(
            f"lateral_torsional_buckling_moment: elastic_modulus deve ser finito e "
            f"positivo, recebido {elastic_modulus!r}."
        )
    if not is_positive_finite(minor_axis_moment_of_inertia):
        raise ValueError(
            f"lateral_torsional_buckling_moment: minor_axis_moment_of_inertia deve "
            f"ser finito e positivo, recebido {minor_axis_moment_of_inertia!r}."
        )
    if not is_positive_finite(torsion_constant):
        raise ValueError(
            f"lateral_torsional_buckling_moment: torsion_constant deve ser finito e "
            f"positivo, recebido {torsion_constant!r}."
        )
    if not is_positive_finite(warping_constant):
        raise ValueError(
            f"lateral_torsional_buckling_moment: warping_constant deve ser finito e "
            f"positivo, recebido {warping_constant!r}."
        )
    if not is_positive_finite(unbraced_length):
        raise ValueError(
            f"lateral_torsional_buckling_moment: unbraced_length deve ser finito e "
            f"positivo, recebido {unbraced_length!r}."
        )
    return (
        cb * math.pi**2 * elastic_modulus * minor_axis_moment_of_inertia / unbraced_length**2
    ) * math.sqrt(
        (warping_constant / minor_axis_moment_of_inertia)
        * (1.0 + 0.039 * torsion_constant * unbraced_length**2 / warping_constant)
    )


def lateral_torsional_buckling_slenderness_limit(
    cb: float,
    elastic_modulus: float,
    minor_axis_moment_of_inertia: float,
    torsion_constant: float,
    warping_constant: float,
    radius_of_gyration_minor_axis: float,
    residual_moment: float,
) -> float:
    """Parametro de esbeltez correspondente ao inicio do escoamento, ``lambda_r`` (D.2.8-a).

    ``beta1 = Mr/(E*J)``;
    ``lambda_r = (1,38*Cb*sqrt(Iy*J)/(ry*J*beta1)) *
    sqrt(1 + sqrt(1 + 27*Cw*beta1^2/(Cb^2*Iy)))``.

    Parametros
    ----------
    cb, elastic_modulus, minor_axis_moment_of_inertia, torsion_constant, warping_constant:
        Ver :func:`lateral_torsional_buckling_moment`.
    radius_of_gyration_minor_axis:
        Raio de giracao em relacao ao eixo de menor momento de
        inercia, ``ry`` (mm) — ver nota de convencao de eixos no
        docstring de :func:`check_lateral_torsional_buckling`.
    residual_moment:
        Momento fletor correspondente ao inicio do escoamento
        considerando tensao residual, ``Mr`` (N.mm) —
        ``Mr=(fy-0,3*fy)*W``, ver
        :func:`check_lateral_torsional_buckling`.
    """
    if not is_positive_finite(cb):
        raise ValueError(
            f"lateral_torsional_buckling_slenderness_limit: cb deve ser finito e "
            f"positivo, recebido {cb!r}."
        )
    if not is_positive_finite(elastic_modulus):
        raise ValueError(
            f"lateral_torsional_buckling_slenderness_limit: elastic_modulus deve "
            f"ser finito e positivo, recebido {elastic_modulus!r}."
        )
    if not is_positive_finite(minor_axis_moment_of_inertia):
        raise ValueError(
            f"lateral_torsional_buckling_slenderness_limit: "
            f"minor_axis_moment_of_inertia deve ser finito e positivo, recebido "
            f"{minor_axis_moment_of_inertia!r}."
        )
    if not is_positive_finite(torsion_constant):
        raise ValueError(
            f"lateral_torsional_buckling_slenderness_limit: torsion_constant deve "
            f"ser finito e positivo, recebido {torsion_constant!r}."
        )
    if not is_positive_finite(warping_constant):
        raise ValueError(
            f"lateral_torsional_buckling_slenderness_limit: warping_constant deve "
            f"ser finito e positivo, recebido {warping_constant!r}."
        )
    if not is_positive_finite(radius_of_gyration_minor_axis):
        raise ValueError(
            f"lateral_torsional_buckling_slenderness_limit: "
            f"radius_of_gyration_minor_axis deve ser finito e positivo, recebido "
            f"{radius_of_gyration_minor_axis!r}."
        )
    if not is_positive_finite(residual_moment):
        raise ValueError(
            f"lateral_torsional_buckling_slenderness_limit: residual_moment deve "
            f"ser finito e positivo, recebido {residual_moment!r}."
        )
    beta1 = residual_moment / (elastic_modulus * torsion_constant)
    return (
        1.38
        * cb
        * math.sqrt(minor_axis_moment_of_inertia * torsion_constant)
        / (radius_of_gyration_minor_axis * torsion_constant * beta1)
    ) * math.sqrt(
        1.0
        + math.sqrt(
            1.0 + 27.0 * warping_constant * beta1**2 / (cb**2 * minor_axis_moment_of_inertia)
        )
    )


def flexural_resistance(
    plastic_moment: float,
    residual_moment: float,
    critical_moment: float,
    slenderness: float,
    slenderness_limit_p: float,
    slenderness_limit_r: float,
    gamma_a1: float,
) -> float:
    """Momento fletor resistente de calculo, ``Mrd``, curva de 3 trechos (NBR 8800:2024, D.2.1).

    - ``lambda <= lambda_p``: ``Mrd = Mpl/gamma_a1``;
    - ``lambda_p < lambda <= lambda_r``: ``Mrd =
      [Mpl - (Mpl-Mr)*(lambda-lambda_p)/(lambda_r-lambda_p)]/gamma_a1``;
    - ``lambda > lambda_r``: ``Mrd = Mcr/gamma_a1``.

    Mesma forma conceitual de
    :func:`~openstruct.normative.nbr8800.shear.shear_resistance` e da
    curva de :func:`~openstruct.normative.nbr8800.compression.reduction_factor`
    (plastificacao / regime inelastico com tensao residual / flambagem
    elastica). Escrita de forma generica o suficiente para ser
    reaproveitada pelos estados-limite FLM e FLA (mesma estrutura de
    formula na Tabela D.1) em incrementos futuros — ver ATENCAO no
    docstring do modulo.

    Nota: para FLT, ha uma pequena descontinuidade (~0,18% relativo)
    exatamente em ``lambda=lambda_r`` — ``critical_moment`` calculado
    em ``lambda_r`` (via :func:`lateral_torsional_buckling_moment`)
    nao coincide exatamente com ``residual_moment`` (o limite que o
    segundo ramo atinge em ``lambda_r``), pois ``Mcr`` e ``lambda_r``
    (D.2.8-a) sao formulas empiricas independentes, nao derivadas uma
    da outra para se encontrarem exatamente. Mesma natureza das
    descontinuidades ja documentadas em
    :func:`~openstruct.normative.nbr8800.compression.reduction_factor`
    (~1,7e-4 em ``lambda_0=1,5``) e
    :func:`~openstruct.normative.nbr8800.shear.shear_resistance`
    (~0,4% em ``lambda=lambda_r``) — uma caracteristica das formulas
    da norma, nao um erro de implementacao.

    Parametros
    ----------
    plastic_moment:
        Momento fletor de plastificacao da secao, ``Mpl=fy*Z`` (N.mm),
        ``Z`` o modulo de resistencia plastico.
    residual_moment:
        Momento fletor correspondente ao inicio do escoamento
        considerando tensao residual, ``Mr`` (N.mm).
    critical_moment:
        Momento fletor critico de flambagem elastica, ``Mcr`` (N.mm) —
        ver :func:`lateral_torsional_buckling_moment`.
    slenderness, slenderness_limit_p, slenderness_limit_r:
        Indice de esbeltez e seus limites (``lambda``, ``lambda_p``,
        ``lambda_r``) — para FLT, ``lambda=Lb/ry``.
    gamma_a1:
        Coeficiente de ponderacao da resistencia (NBR 8800:2024,
        4.9.2, Tabela 3).
    """
    if not is_positive_finite(plastic_moment):
        raise ValueError(
            f"flexural_resistance: plastic_moment deve ser finito e positivo, "
            f"recebido {plastic_moment!r}."
        )
    if not is_positive_finite(residual_moment):
        raise ValueError(
            f"flexural_resistance: residual_moment deve ser finito e positivo, "
            f"recebido {residual_moment!r}."
        )
    if residual_moment > plastic_moment:
        # Mr <= Mpl sempre (Mr=(fy-sigma_r)*W <= fy*Z=Mpl, ja que
        # Z>=W para qualquer secao real, fator de forma >= 1) — mesmo
        # raciocinio de Ae<=Ag/Aef<=Ag/web_clear_height<=total_depth
        # no resto do pacote.
        raise ValueError(
            f"flexural_resistance: residual_moment ({residual_moment!r}) nao pode "
            f"ser maior que plastic_moment ({plastic_moment!r})."
        )
    if not is_positive_finite(critical_moment):
        raise ValueError(
            f"flexural_resistance: critical_moment deve ser finito e positivo, "
            f"recebido {critical_moment!r}."
        )
    if not is_positive_finite(slenderness):
        raise ValueError(
            f"flexural_resistance: slenderness deve ser finito e positivo, "
            f"recebido {slenderness!r}."
        )
    if not is_positive_finite(slenderness_limit_p):
        raise ValueError(
            f"flexural_resistance: slenderness_limit_p deve ser finito e "
            f"positivo, recebido {slenderness_limit_p!r}."
        )
    if not is_positive_finite(slenderness_limit_r):
        raise ValueError(
            f"flexural_resistance: slenderness_limit_r deve ser finito e "
            f"positivo, recebido {slenderness_limit_r!r}."
        )
    if not slenderness_limit_r >= slenderness_limit_p:
        raise ValueError(
            f"flexural_resistance: slenderness_limit_r ({slenderness_limit_r!r}) "
            f"nao pode ser menor que slenderness_limit_p ({slenderness_limit_p!r})."
        )
    if not is_positive_finite(gamma_a1):
        raise ValueError(
            f"flexural_resistance: gamma_a1 deve ser finito e positivo, recebido {gamma_a1!r}."
        )

    if slenderness <= slenderness_limit_p:
        return plastic_moment / gamma_a1
    if slenderness <= slenderness_limit_r:
        ratio = (slenderness - slenderness_limit_p) / (slenderness_limit_r - slenderness_limit_p)
        return (plastic_moment - (plastic_moment - residual_moment) * ratio) / gamma_a1
    return critical_moment / gamma_a1


@dataclass(frozen=True, slots=True)
class FlexureCheckResult(CheckResult):
    """Resultado da verificacao ao momento fletor de uma barra (NBR 8800:2024, 5.4.1.3).

    Cobre apenas o estado-limite FLT (ver ATENCAO no docstring do
    modulo) — ``mrd`` aqui NAO e necessariamente o ``Mrd`` completo de
    5.4.2.1 de uma secao real.

    **ATENCAO sobre o sinal de ``msd``**: esta classe NAO toma o valor
    absoluto de ``msd`` automaticamente — ``is_ok``/``utilization``
    (herdados de :class:`CheckResult`) comparam ``msd`` diretamente
    contra ``mrd`` (sempre positivo). A condicao normativa de 5.4.1.3
    e, na pratica, sobre a MAGNITUDE do momento fletor
    (``|Msd|<=Mrd``); um ``msd`` negativo grande (momento fletor no
    sentido oposto, comum em vigas continuas com regioes de momento
    negativo ou em combinacoes de acoes com inversao de sinal) faria
    ``is_ok`` retornar ``True`` de forma NAO CONSERVADORA (``msd``
    muito negativo e sempre "menor" que ``mrd`` positivo), mesmo com a
    barra severamente sobrecarregada. **O chamador e responsavel por
    passar ``abs(msd)`` caso o interesse seja verificar a magnitude do
    momento solicitante** — mesma responsabilidade do chamador ja
    documentada para ``Vsd`` em
    :class:`~openstruct.normative.nbr8800.shear.ShearCheckResult`.

    Atributos
    ---------
    msd:
        Momento fletor solicitante de calculo (N.mm) — ver ATENCAO
        sobre sinal acima.
    mrd:
        Momento fletor resistente de calculo para FLT (N.mm) — ver
        :func:`flexural_resistance`.
    """

    msd: float
    mrd: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.msd):
            raise ValueError(f"FlexureCheckResult.msd deve ser finito, recebido {self.msd!r}.")
        if not is_positive_finite(self.mrd):
            raise ValueError(
                f"FlexureCheckResult.mrd deve ser finito e positivo, recebido {self.mrd!r}."
            )

    @property
    def sd(self) -> float:
        """Alias generico de :attr:`msd` — ver :class:`CheckResult`."""
        return self.msd

    @property
    def rd(self) -> float:
        """Alias generico de :attr:`mrd` — ver :class:`CheckResult`."""
        return self.mrd


def check_lateral_torsional_buckling(
    msd: float,
    fy: float,
    elastic_modulus: float,
    elastic_section_modulus: float,
    plastic_section_modulus: float,
    minor_axis_moment_of_inertia: float,
    torsion_constant: float,
    warping_constant: float,
    radius_of_gyration_minor_axis: float,
    unbraced_length: float,
    cb: float,
    resistance_factors_gamma_a1: float,
) -> FlexureCheckResult:
    """Verifica a FLT de uma barra I/H/U duplamente simetrica fletida no eixo maior.

    NBR 8800:2024, 5.4.1.3 (``Msd<=Mrd``) e Anexo D, Tabela D.1
    (primeira linha, coluna FLT) com D.2.8-a. Ver ATENCAO no docstring
    do modulo: cobre apenas FLT, nao o ``Mrd`` completo de 5.4.2.1.

    Nota sobre convencao de eixos deste pacote: "eixo maior" (major
    axis, o eixo de flexao) usa o modulo de resistencia em torno dele
    (``elastic_section_modulus``/``plastic_section_modulus`` —
    tipicamente ``section.Welz``/``section.Wplz`` na convencao deste
    projeto, onde ``Iz`` e o eixo forte — ver VAL-0009). Os parametros
    de FLT (``minor_axis_moment_of_inertia``,
    ``radius_of_gyration_minor_axis``) sempre se referem ao eixo
    PERPENDICULAR ao eixo de flexao (o eixo fraco, ``Iy``/``ry`` nesta
    convencao), independentemente de qual eixo e "maior" — e assim que
    a propria formula de FLT e definida na norma (a resistencia a
    flambagem lateral vem da rigidez a flexao lateral e a torcao, nao
    da rigidez em torno do eixo de flexao).

    Parametros
    ----------
    msd:
        Momento fletor solicitante de calculo (N.mm). Ver ATENCAO
        sobre sinal na docstring de :class:`FlexureCheckResult` — se o
        interesse e verificar a magnitude do momento (a condicao
        normativa de 5.4.1.3 e sobre ``|Msd|``), o chamador deve
        passar ``abs(msd)``.
    fy:
        Resistencia ao escoamento do aco (MPa).
    elastic_modulus:
        Modulo de elasticidade do aco, ``E`` (MPa).
    elastic_section_modulus:
        Modulo de resistencia elastico em relacao ao eixo de flexao,
        ``W`` (mm^3).
    plastic_section_modulus:
        Modulo de resistencia plastico em relacao ao eixo de flexao,
        ``Z`` (mm^3) — usado em ``Mpl=fy*Z``.
    minor_axis_moment_of_inertia:
        Momento de inercia em relacao ao eixo PERPENDICULAR ao eixo de
        flexao, ``Iy`` (mm^4) — ver nota de convencao de eixos acima.
    torsion_constant:
        Constante de torcao de Saint-Venant, ``J`` (mm^4).
    warping_constant:
        Constante de empenamento, ``Cw`` (mm^6) — ver
        :func:`warping_constant_i_section` para secoes I sem esse
        valor de catalogo.
    radius_of_gyration_minor_axis:
        Raio de giracao em relacao ao eixo PERPENDICULAR ao eixo de
        flexao, ``ry`` (mm).
    unbraced_length:
        Comprimento destravado a flambagem lateral com torcao, ``Lb``
        (mm).
    cb:
        Fator de modificacao para diagrama de momento fletor nao
        uniforme — ver :func:`moment_gradient_factor_doubly_symmetric`,
        ou ``1,0`` de forma conservadora (sempre valido, ver 5.4.2.3).
    resistance_factors_gamma_a1:
        ``gamma_a1`` (NBR 8800:2024, 4.9.2, Tabela 3) — passado como
        ``float`` direto (nao ``SteelResistanceFactors`` completo),
        mesmo padrao de
        ``shear.check_shear_major_axis``, pois esta verificacao usa
        apenas esse coeficiente.

    Retorna
    -------
    :class:`FlexureCheckResult` com ``mrd`` (apenas FLT — ver ATENCAO
    no docstring do modulo), a taxa de utilizacao e se a condicao de
    5.4.1.3 e atendida (para FLT isoladamente).
    """
    if not math.isfinite(msd):
        raise ValueError(
            f"check_lateral_torsional_buckling: msd deve ser finito, recebido {msd!r}."
        )
    if not is_positive_finite(fy):
        raise ValueError(
            f"check_lateral_torsional_buckling: fy deve ser finito e positivo, recebido {fy!r}."
        )
    if not is_positive_finite(elastic_section_modulus):
        raise ValueError(
            f"check_lateral_torsional_buckling: elastic_section_modulus deve ser "
            f"finito e positivo, recebido {elastic_section_modulus!r}."
        )
    if not is_positive_finite(plastic_section_modulus):
        raise ValueError(
            f"check_lateral_torsional_buckling: plastic_section_modulus deve ser "
            f"finito e positivo, recebido {plastic_section_modulus!r}."
        )
    if plastic_section_modulus < elastic_section_modulus:
        # Z >= W sempre (fator de forma >= 1) para qualquer secao real.
        raise ValueError(
            f"check_lateral_torsional_buckling: plastic_section_modulus "
            f"({plastic_section_modulus!r}) nao pode ser menor que "
            f"elastic_section_modulus ({elastic_section_modulus!r})."
        )
    if not is_positive_finite(radius_of_gyration_minor_axis):
        raise ValueError(
            f"check_lateral_torsional_buckling: radius_of_gyration_minor_axis "
            f"deve ser finito e positivo, recebido "
            f"{radius_of_gyration_minor_axis!r}."
        )
    if not is_positive_finite(unbraced_length):
        raise ValueError(
            f"check_lateral_torsional_buckling: unbraced_length deve ser finito e "
            f"positivo, recebido {unbraced_length!r}."
        )

    residual_stress = 0.30 * fy
    residual_moment = (fy - residual_stress) * elastic_section_modulus
    plastic_moment = fy * plastic_section_modulus

    critical_moment = lateral_torsional_buckling_moment(
        cb=cb,
        elastic_modulus=elastic_modulus,
        minor_axis_moment_of_inertia=minor_axis_moment_of_inertia,
        torsion_constant=torsion_constant,
        warping_constant=warping_constant,
        unbraced_length=unbraced_length,
    )
    slenderness_limit_p = 1.76 * math.sqrt(elastic_modulus / fy)
    slenderness_limit_r = lateral_torsional_buckling_slenderness_limit(
        cb=cb,
        elastic_modulus=elastic_modulus,
        minor_axis_moment_of_inertia=minor_axis_moment_of_inertia,
        torsion_constant=torsion_constant,
        warping_constant=warping_constant,
        radius_of_gyration_minor_axis=radius_of_gyration_minor_axis,
        residual_moment=residual_moment,
    )
    slenderness = unbraced_length / radius_of_gyration_minor_axis

    mrd = flexural_resistance(
        plastic_moment=plastic_moment,
        residual_moment=residual_moment,
        critical_moment=critical_moment,
        slenderness=slenderness,
        slenderness_limit_p=slenderness_limit_p,
        slenderness_limit_r=slenderness_limit_r,
        gamma_a1=resistance_factors_gamma_a1,
    )
    return FlexureCheckResult(msd=msd, mrd=mrd)
