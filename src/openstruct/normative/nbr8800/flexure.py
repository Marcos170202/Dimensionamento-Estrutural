"""Barras prismaticas submetidas a momento fletor.

Fonte: ABNT NBR 8800:2024, 5.4.2 "Momento fletor resistente de
calculo" (paginas 54-56) e Anexo D "Momento fletor resistente de
calculo de vigas de alma nao esbelta", D.1/D.2/D.2.8-a/D.3 (paginas
137, 144-147). Formulas extraidas por leitura direta do PDF fornecido
pelo usuario — ver rastreabilidade completa em
``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: os tres estados-limite da PRIMEIRA LINHA da Tabela
D.1 — flambagem lateral com torcao (FLT), flambagem local da mesa
comprimida (FLM) e flambagem local da alma (FLA) — para secoes I, H
com dois eixos de simetria e secoes U nao sujeitas a momento de
torcao, fletidas em relacao ao eixo de MAIOR momento de inercia — o
caso mais comum e o unico conjunto de estados-limite aplicavel quando
o eixo de flexao NAO e o de maior momento de inercia (D.2.8-g, FLT
apenas). Cobre:

- 5.4.2.1/5.4.1.3 — condicao de dimensionamento (``Msd <= Mrd``), com
  ``Mrd = min(Mrd_FLT, Mrd_FLM, Mrd_FLA)`` (:func:`check_flexural_resistance_major_axis`)
  — fecha a limitacao de seguranca antes registrada para este tipo de
  secao/eixo (ver NBR8800-FLEX-004 em ``docs/normative/NBR8800-RULES.md``);
- 5.4.2.2 — limite ``Mrd <= 1,50*W*fy/gamma_a1`` para garantir
  validade da analise elastica, aplicado ao ``Mrd`` GOVERNANTE final
  em :func:`check_flexural_resistance_major_axis`;
- 5.4.2.3-a — fator de modificacao para diagrama de momento fletor nao
  uniforme, ``Cb``, caso geral (``Rm=1,0`` para secoes duplamente
  simetricas — os demais casos, b) e c), de 5.4.2.3/5.4.2.4 nao sao
  implementados, ver abaixo);
- D.2.1/D.2.8-a — curva de 3 trechos do momento fletor resistente de
  calculo `Mrd` para FLT (plastificacao / escoamento com tensao
  residual / flambagem elastica), com ``Mcr``/``lambda_r`` calculados
  conforme D.2.8-a;
- D.2.8-e/f/h — a mesma curva de 3 trechos para FLM (plastificacao /
  escoamento com tensao residual / flambagem local elastica da mesa),
  com ``Mcr``/``lambda_r`` diferentes para perfis LAMINADOS
  (D.2.8-f, primeiro caso) e SOLDADOS (D.2.8-f, segundo caso, usando
  o coeficiente ``kc`` da Tabela 4, nota de rodape a);
- Tabela D.1 (FLA, primeira linha) — a mesma curva de 3 trechos para
  FLA, restrita a vigas de alma NAO esbelta (``lambda_FLA<=lambda_r``,
  D.1.2) — ver ATENCAO abaixo sobre almas esbeltas.

**ATENCAO — LIMITACAO DE SEGURANCA (Anexo E, vigas de alma esbelta)**:
D.1.2 restringe TODO o Anexo D (nao apenas FLA) a "vigas de alma nao
esbelta" (``lambda_FLA=h/tw <= lambda_r=5,70*sqrt(E/fy)``). Se a alma
for esbelta, a norma exige usar o Anexo E (vigas de alma esbelta) para
TODA a verificacao — nao apenas substituir o ramo de FLA.
:func:`check_flexural_resistance_major_axis` VALIDA essa precondicao
(``ValueError`` se violada) antes de calcular FLT/FLM/FLA, mas o Anexo
E em si NAO esta implementado — para vigas de alma esbelta, nenhuma
funcao deste modulo pode ser usada. Ver
``docs/normative/NBR8800-RULES.md`` (RULE-ID ``NBR8800-FLEX-007``).

Tambem NAO implementado (fora do escopo desta fase, ver
``docs/normative/NBR8800-RULES.md`` para a lista completa e o motivo
de cada item): 5.4.2.3, casos b) e c), e 5.4.2.4/5.4.2.5 (``Cb`` para
balancos e para secoes monossimetricas — apenas o caso geral
duplamente simetrico, 5.4.2.3-a, esta aqui); 5.4.2.6 (furos na mesa
tracionada); demais linhas da Tabela D.1 (secoes monossimetricas,
tubulares/caixao, T, cantoneiras duplas, solidas) e flexao em torno do
eixo de menor momento de inercia (D.2.5, onde FLT nao se aplica —
D.2.8-g); Anexo E (ver ATENCAO acima); Anexos F/G/H/I; 5.5 (combinacao
de esforcos).
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


def flange_local_buckling_coefficient_welded(
    web_clear_height: float, web_thickness: float
) -> float:
    """Coeficiente ``kc`` para flambagem local da mesa de perfis SOLDADOS (Tabela 4, nota a).

    ``kc = 4/sqrt(h/tw)``, limitado a ``0,35 <= kc <= 0,76``. Usado
    apenas em :func:`flange_local_buckling_moment_welded` — perfis
    LAMINADOS nao usam ``kc`` (ver :func:`flange_local_buckling_moment_rolled`).

    Parametros
    ----------
    web_clear_height:
        Altura da alma, ``h`` (mm) — mesma definicao de ``h`` usada em
        ``shear.py`` (distancia entre as faces internas das mesas nos
        perfis soldados, ou esse valor subtraindo os raios de
        concordancia nos perfis laminados).
    web_thickness:
        Espessura da alma, ``tw`` (mm).
    """
    if not is_positive_finite(web_clear_height):
        raise ValueError(
            f"flange_local_buckling_coefficient_welded: web_clear_height deve ser "
            f"finito e positivo, recebido {web_clear_height!r}."
        )
    if not is_positive_finite(web_thickness):
        raise ValueError(
            f"flange_local_buckling_coefficient_welded: web_thickness deve ser "
            f"finito e positivo, recebido {web_thickness!r}."
        )
    kc = 4.0 / math.sqrt(web_clear_height / web_thickness)
    return min(0.76, max(0.35, kc))


def flange_local_buckling_moment_rolled(
    elastic_modulus: float, compressed_side_section_modulus: float, slenderness: float
) -> float:
    """Momento fletor critico de FLM para perfis LAMINADOS, ``Mcr`` (NBR 8800:2024, D.2.8-f).

    ``Mcr = 0,69*E/lambda^2 * Wc``.

    Parametros
    ----------
    elastic_modulus:
        Modulo de elasticidade do aco, ``E`` (MPa).
    compressed_side_section_modulus:
        Modulo de resistencia elastico do lado comprimido da secao,
        ``Wc`` (mm^3) — para secoes duplamente simetricas, igual ao
        modulo de resistencia elastico em relacao ao eixo de flexao,
        ``W`` (``elastic_section_modulus`` de
        :func:`check_flexural_resistance_major_axis`).
    slenderness:
        Indice de esbeltez da mesa, ``lambda = b/t`` (D.2.8-h; ``b`` e
        a metade da largura total da mesa para secoes I/H).
    """
    if not is_positive_finite(elastic_modulus):
        raise ValueError(
            f"flange_local_buckling_moment_rolled: elastic_modulus deve ser "
            f"finito e positivo, recebido {elastic_modulus!r}."
        )
    if not is_positive_finite(compressed_side_section_modulus):
        raise ValueError(
            f"flange_local_buckling_moment_rolled: compressed_side_section_modulus "
            f"deve ser finito e positivo, recebido {compressed_side_section_modulus!r}."
        )
    if not is_positive_finite(slenderness):
        raise ValueError(
            f"flange_local_buckling_moment_rolled: slenderness deve ser finito e "
            f"positivo, recebido {slenderness!r}."
        )
    return 0.69 * elastic_modulus / slenderness**2 * compressed_side_section_modulus


def flange_local_buckling_moment_welded(
    elastic_modulus: float,
    flange_local_buckling_coefficient: float,
    compressed_side_section_modulus: float,
    slenderness: float,
) -> float:
    """Momento fletor critico de FLM para perfis SOLDADOS, ``Mcr`` (NBR 8800:2024, D.2.8-f).

    ``Mcr = 0,90*E*kc/lambda^2 * Wc``.

    Parametros
    ----------
    elastic_modulus:
        Modulo de elasticidade do aco, ``E`` (MPa).
    flange_local_buckling_coefficient:
        ``kc`` — ver :func:`flange_local_buckling_coefficient_welded`.
    compressed_side_section_modulus, slenderness:
        Ver :func:`flange_local_buckling_moment_rolled`.
    """
    if not is_positive_finite(elastic_modulus):
        raise ValueError(
            f"flange_local_buckling_moment_welded: elastic_modulus deve ser "
            f"finito e positivo, recebido {elastic_modulus!r}."
        )
    if not is_positive_finite(flange_local_buckling_coefficient):
        raise ValueError(
            f"flange_local_buckling_moment_welded: flange_local_buckling_coefficient "
            f"deve ser finito e positivo, recebido {flange_local_buckling_coefficient!r}."
        )
    if not is_positive_finite(compressed_side_section_modulus):
        raise ValueError(
            f"flange_local_buckling_moment_welded: compressed_side_section_modulus "
            f"deve ser finito e positivo, recebido {compressed_side_section_modulus!r}."
        )
    if not is_positive_finite(slenderness):
        raise ValueError(
            f"flange_local_buckling_moment_welded: slenderness deve ser finito e "
            f"positivo, recebido {slenderness!r}."
        )
    return (
        0.90
        * elastic_modulus
        * flange_local_buckling_coefficient
        / slenderness**2
        * compressed_side_section_modulus
    )


def check_flexural_resistance_major_axis(
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
    flange_width: float,
    flange_thickness: float,
    web_clear_height: float,
    web_thickness: float,
    rolled: bool,
    resistance_factors_gamma_a1: float,
) -> FlexureCheckResult:
    """Verifica o momento fletor resistente de calculo completo (FLT+FLM+FLA).

    NBR 8800:2024, 5.4.1.3/5.4.2.1/5.4.2.2 e Anexo D, Tabela D.1
    (primeira linha) — fecha a limitacao de seguranca antes registrada
    em ``NBR8800-FLEX-004`` para secoes I, H com dois eixos de simetria
    e secoes U nao sujeitas a momento de torcao, fletidas em relacao
    ao eixo de maior momento de inercia: ``Mrd = min(Mrd_FLT, Mrd_FLM,
    Mrd_FLA)``, com o limite adicional de 5.4.2.2
    (``Mrd <= 1,50*W*fy/gamma_a1``) aplicado ao resultado.

    **Precondicao de aplicabilidade (D.1.2)**: esta funcao SO e valida
    para vigas de alma NAO esbelta (``h/tw <= 5,70*sqrt(E/fy)``) — se
    a alma for esbelta, TODO o Anexo D deixa de se aplicar (nao apenas
    FLA) e a verificacao deveria ser feita pelo Anexo E (nao
    implementado); esta funcao levanta ``ValueError`` nesse caso, ver
    ATENCAO no docstring do modulo.

    Nota sobre convencao de eixos: ver docstring de
    :func:`check_lateral_torsional_buckling` — os parametros de FLT
    (``minor_axis_moment_of_inertia``, ``radius_of_gyration_minor_axis``)
    sempre se referem ao eixo PERPENDICULAR ao eixo de flexao.

    Parametros
    ----------
    msd, fy, elastic_modulus, elastic_section_modulus, plastic_section_modulus,
    minor_axis_moment_of_inertia, torsion_constant, warping_constant,
    radius_of_gyration_minor_axis, unbraced_length, cb:
        Ver :func:`check_lateral_torsional_buckling`.
    flange_width:
        Largura total da mesa, ``bf`` (mm) — usada em ``b/t=(bf/2)/tf``
        (D.2.8-h: ``b`` e a metade da largura total para mesas de
        secoes I/H).
    flange_thickness:
        Espessura da mesa, ``tf`` (mm).
    web_clear_height:
        Altura da alma, ``h`` (mm) — mesma definicao usada em
        ``shear.py``.
    web_thickness:
        Espessura da alma, ``tw`` (mm).
    rolled:
        ``True`` para perfis LAMINADOS (usa
        :func:`flange_local_buckling_moment_rolled`), ``False`` para
        perfis SOLDADOS (usa :func:`flange_local_buckling_moment_welded`
        com :func:`flange_local_buckling_coefficient_welded`).
    resistance_factors_gamma_a1:
        ``gamma_a1`` (NBR 8800:2024, 4.9.2, Tabela 3) — passado como
        ``float`` direto, mesmo padrao do resto do pacote.

    Retorna
    -------
    :class:`FlexureCheckResult` com ``mrd`` (o MENOR entre FLT, FLM e
    FLA, ja limitado por 5.4.2.2 — o `Mrd` completo de 5.4.2.1 para
    este tipo de secao/eixo), a taxa de utilizacao e se a condicao de
    5.4.1.3 e atendida.
    """
    if not math.isfinite(msd):
        raise ValueError(
            f"check_flexural_resistance_major_axis: msd deve ser finito, recebido {msd!r}."
        )
    if not is_positive_finite(fy):
        raise ValueError(
            f"check_flexural_resistance_major_axis: fy deve ser finito e positivo, recebido {fy!r}."
        )
    if not is_positive_finite(elastic_modulus):
        raise ValueError(
            f"check_flexural_resistance_major_axis: elastic_modulus deve ser "
            f"finito e positivo, recebido {elastic_modulus!r}."
        )
    if not is_positive_finite(elastic_section_modulus):
        raise ValueError(
            f"check_flexural_resistance_major_axis: elastic_section_modulus deve "
            f"ser finito e positivo, recebido {elastic_section_modulus!r}."
        )
    if not is_positive_finite(plastic_section_modulus):
        raise ValueError(
            f"check_flexural_resistance_major_axis: plastic_section_modulus deve "
            f"ser finito e positivo, recebido {plastic_section_modulus!r}."
        )
    if plastic_section_modulus < elastic_section_modulus:
        raise ValueError(
            f"check_flexural_resistance_major_axis: plastic_section_modulus "
            f"({plastic_section_modulus!r}) nao pode ser menor que "
            f"elastic_section_modulus ({elastic_section_modulus!r})."
        )
    if not is_positive_finite(flange_width):
        raise ValueError(
            f"check_flexural_resistance_major_axis: flange_width deve ser finito "
            f"e positivo, recebido {flange_width!r}."
        )
    if not is_positive_finite(flange_thickness):
        raise ValueError(
            f"check_flexural_resistance_major_axis: flange_thickness deve ser "
            f"finito e positivo, recebido {flange_thickness!r}."
        )
    if not is_positive_finite(web_clear_height):
        raise ValueError(
            f"check_flexural_resistance_major_axis: web_clear_height deve ser "
            f"finito e positivo, recebido {web_clear_height!r}."
        )
    if not is_positive_finite(web_thickness):
        raise ValueError(
            f"check_flexural_resistance_major_axis: web_thickness deve ser finito "
            f"e positivo, recebido {web_thickness!r}."
        )

    residual_stress = 0.30 * fy
    residual_moment = (fy - residual_stress) * elastic_section_modulus
    plastic_moment = fy * plastic_section_modulus
    gamma_a1 = resistance_factors_gamma_a1

    # --- Precondicao D.1.2: viga de alma nao esbelta (senao, Anexo E) ---
    fla_slenderness = web_clear_height / web_thickness
    fla_slenderness_limit_r = 5.70 * math.sqrt(elastic_modulus / fy)
    if fla_slenderness > fla_slenderness_limit_r:
        raise ValueError(
            f"check_flexural_resistance_major_axis: h/tw ({fla_slenderness!r}) "
            f"excede o limite de {fla_slenderness_limit_r!r} (D.1.2) — esta e uma "
            f"viga de ALMA ESBELTA, fora do escopo do Anexo D (todas as formulas "
            f"deste modulo); a verificacao deveria ser feita pelo Anexo E, ainda "
            f"nao implementado (ver docstring do modulo)."
        )

    # --- FLT (D.2.8-a) ---
    flt_critical_moment = lateral_torsional_buckling_moment(
        cb=cb,
        elastic_modulus=elastic_modulus,
        minor_axis_moment_of_inertia=minor_axis_moment_of_inertia,
        torsion_constant=torsion_constant,
        warping_constant=warping_constant,
        unbraced_length=unbraced_length,
    )
    flt_slenderness_limit_p = 1.76 * math.sqrt(elastic_modulus / fy)
    flt_slenderness_limit_r = lateral_torsional_buckling_slenderness_limit(
        cb=cb,
        elastic_modulus=elastic_modulus,
        minor_axis_moment_of_inertia=minor_axis_moment_of_inertia,
        torsion_constant=torsion_constant,
        warping_constant=warping_constant,
        radius_of_gyration_minor_axis=radius_of_gyration_minor_axis,
        residual_moment=residual_moment,
    )
    flt_slenderness = unbraced_length / radius_of_gyration_minor_axis
    mrd_flt = flexural_resistance(
        plastic_moment=plastic_moment,
        residual_moment=residual_moment,
        critical_moment=flt_critical_moment,
        slenderness=flt_slenderness,
        slenderness_limit_p=flt_slenderness_limit_p,
        slenderness_limit_r=flt_slenderness_limit_r,
        gamma_a1=gamma_a1,
    )

    # --- FLM (D.2.8-e/f/h) ---
    # residual_stress ja calculado acima (0,30*fy); fy-residual_stress = 0,70*fy.
    fy_minus_residual_stress = fy - residual_stress
    flm_slenderness = (flange_width / 2.0) / flange_thickness
    flm_slenderness_limit_p = 0.38 * math.sqrt(elastic_modulus / fy)
    if rolled:
        flm_critical_moment = flange_local_buckling_moment_rolled(
            elastic_modulus=elastic_modulus,
            compressed_side_section_modulus=elastic_section_modulus,
            slenderness=flm_slenderness,
        )
        flm_slenderness_limit_r = 0.83 * math.sqrt(elastic_modulus / fy_minus_residual_stress)
    else:
        kc = flange_local_buckling_coefficient_welded(
            web_clear_height=web_clear_height, web_thickness=web_thickness
        )
        flm_critical_moment = flange_local_buckling_moment_welded(
            elastic_modulus=elastic_modulus,
            flange_local_buckling_coefficient=kc,
            compressed_side_section_modulus=elastic_section_modulus,
            slenderness=flm_slenderness,
        )
        flm_slenderness_limit_r = 0.95 * math.sqrt(elastic_modulus * kc / fy_minus_residual_stress)
    mrd_flm = flexural_resistance(
        plastic_moment=plastic_moment,
        residual_moment=residual_moment,
        critical_moment=flm_critical_moment,
        slenderness=flm_slenderness,
        slenderness_limit_p=flm_slenderness_limit_p,
        slenderness_limit_r=flm_slenderness_limit_r,
        gamma_a1=gamma_a1,
    )

    # --- FLA (Tabela D.1) ---
    # Ja confirmado fla_slenderness<=fla_slenderness_limit_r acima (D.1.2)
    # -> o terceiro ramo (flambagem elastica, Anexo E) nunca e
    # selecionado por flexural_resistance() aqui; fla_residual_moment
    # (=fy*W<=fy*Z=plastic_moment, ja que Z>=W foi validado acima) serve
    # tambem de placeholder valido para critical_moment (nunca de fato
    # usado, mas exigido pela assinatura generica da funcao).
    fla_residual_moment = fy * elastic_section_modulus
    fla_slenderness_limit_p = 3.76 * math.sqrt(elastic_modulus / fy)
    mrd_fla = flexural_resistance(
        plastic_moment=plastic_moment,
        residual_moment=fla_residual_moment,
        critical_moment=fla_residual_moment,
        slenderness=fla_slenderness,
        slenderness_limit_p=fla_slenderness_limit_p,
        slenderness_limit_r=fla_slenderness_limit_r,
        gamma_a1=gamma_a1,
    )

    mrd = min(mrd_flt, mrd_flm, mrd_fla)
    # 5.4.2.2: limite para garantir validade da analise elastica.
    mrd = min(mrd, 1.50 * elastic_section_modulus * fy / gamma_a1)
    return FlexureCheckResult(msd=msd, mrd=mrd)
