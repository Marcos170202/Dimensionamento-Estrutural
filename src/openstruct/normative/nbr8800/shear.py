"""Barras prismaticas submetidas a forca cortante.

Fonte: ABNT NBR 8800:2024, 5.4.1 "Generalidades" (condicao de
dimensionamento, pagina 53) e 5.4.3 "Forca cortante resistente de
calculo", 5.4.3.1 "Secoes I, H e U fletidas em relacao ao eixo
perpendicular a alma" (paginas 56-57). Formulas extraidas por leitura
direta do PDF fornecido pelo usuario — ver rastreabilidade completa em
``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: apenas

- 5.4.1.3 — condicao de dimensionamento para forca cortante
  (``Vsd <= Vrd``; a condicao de momento fletor, ``Msd <= Mrd``, NAO e
  implementada aqui, ver abaixo);
- 5.4.3.1 — forca cortante resistente de calculo de secoes I, H e U
  fletidas em relacao ao eixo perpendicular a alma (eixo de maior
  momento de inercia) — o caso mais comum, com a alma resistindo ao
  cisalhamento.

**Fora do escopo** (ver ``docs/normative/NBR8800-RULES.md`` para a
lista completa): 5.4.2 (momento fletor resistente de calculo — remete
aos Anexos D/E, que envolvem classificacao da secao
compacta/semicompacta/esbelta e flambagem lateral com torcao (FLT);
substancialmente mais complexo que 5.4.3, fica para um incremento
futuro dedicado); 5.4.3.2 a 5.4.3.6 (forca cortante resistente para
secoes tubulares/caixao, T, cantoneiras duplas, I/H/U fletidas em
torno do eixo fraco, e tubulares circulares — mesma estrutura de
formula de 5.4.3.1, mas com ``kv``/area efetiva de cisalhamento
diferentes; adiado para manter este incremento focado em um unico
caso bem validado); 5.4.4 (chapas de reforco/lamelas); 5.4.5
(requisitos para secoes soldadas); 5.5 (combinacao de momento fletor,
forca cortante, forca axial e momento de torcao).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ._check_result import CheckResult
from ._validation import is_positive_finite


def effective_shear_area_major_axis(total_depth: float, web_thickness: float) -> float:
    """Area efetiva de cisalhamento, ``Aw = d*tw`` (NBR 8800:2024, 5.4.3.1.2).

    Valida para secoes I, H e U fletidas em relacao ao eixo
    perpendicular a alma (eixo de maior momento de inercia).

    Parametros
    ----------
    total_depth:
        Altura total da secao transversal, ``d`` (mm).
    web_thickness:
        Espessura da alma, ``tw`` (mm).
    """
    if not is_positive_finite(total_depth):
        raise ValueError(
            f"effective_shear_area_major_axis: total_depth deve ser finito e "
            f"positivo, recebido {total_depth!r}."
        )
    if not is_positive_finite(web_thickness):
        raise ValueError(
            f"effective_shear_area_major_axis: web_thickness deve ser finito e "
            f"positivo, recebido {web_thickness!r}."
        )
    return total_depth * web_thickness


def plastic_shear_force(effective_shear_area: float, fy: float) -> float:
    """Forca cortante correspondente a plastificacao da alma por cisalhamento.

    NBR 8800:2024, 5.4.3.1.2: ``Vpl = 0,60*Aw*fy``. A formula em si e
    generica (reaproveitavel pelos casos 5.4.3.2 a 5.4.3.6, que usam
    formulas diferentes so para ``Aw`` — fora do escopo desta fase,
    ver docstring do modulo).

    Parametros
    ----------
    effective_shear_area:
        Area efetiva de cisalhamento, ``Aw`` (mm^2) — ver
        :func:`effective_shear_area_major_axis` para o caso de 5.4.3.1.
    fy:
        Resistencia ao escoamento do aco (MPa).
    """
    if not is_positive_finite(effective_shear_area):
        raise ValueError(
            f"plastic_shear_force: effective_shear_area deve ser finito e "
            f"positivo, recebido {effective_shear_area!r}."
        )
    if not is_positive_finite(fy):
        raise ValueError(f"plastic_shear_force: fy deve ser finito e positivo, recebido {fy!r}.")
    return 0.60 * effective_shear_area * fy


def shear_buckling_coefficient(web_clear_height: float, stiffener_spacing: float | None) -> float:
    """Coeficiente de flambagem por cisalhamento, ``kv`` (NBR 8800:2024, 5.4.3.1.1).

    ``kv = 5,34`` para almas sem enrijecedores transversais OU para
    ``a/h > 3``; ``kv = 5,0 + 5/(a/h)^2`` para os demais casos (``a`` e
    a distancia entre enrijecedores transversais adjacentes).

    Parametros
    ----------
    web_clear_height:
        Altura da alma, ``h`` (mm) — a distancia entre as faces
        internas das mesas nos perfis soldados, ou esse valor
        subtraindo os dois raios de concordancia mesa/alma nos perfis
        laminados (5.4.3.1.1). **Nao e a altura total da secao**
        (``d``, usada em :func:`effective_shear_area_major_axis`).
    stiffener_spacing:
        Distancia entre enrijecedores transversais adjacentes, ``a``
        (mm), ou ``None`` se a alma nao tiver enrijecedores
        transversais.
    """
    if not is_positive_finite(web_clear_height):
        raise ValueError(
            f"shear_buckling_coefficient: web_clear_height deve ser finito e "
            f"positivo, recebido {web_clear_height!r}."
        )
    if stiffener_spacing is None:
        return 5.34
    if not is_positive_finite(stiffener_spacing):
        raise ValueError(
            f"shear_buckling_coefficient: stiffener_spacing deve ser finito e "
            f"positivo (ou None), recebido {stiffener_spacing!r}."
        )
    ratio = stiffener_spacing / web_clear_height
    if ratio > 3:
        return 5.34
    return 5.0 + 5.0 / ratio**2


def shear_resistance(
    plastic_shear_force: float,
    slenderness: float,
    slenderness_limit_p: float,
    slenderness_limit_r: float,
    gamma_a1: float,
) -> float:
    """Forca cortante resistente de calculo, ``Vrd`` (NBR 8800:2024, 5.4.3.1.1).

    Curva em 3 trechos (plastificacao / flambagem inelastica /
    flambagem elastica por cisalhamento), mesma estrutura conceitual
    de :func:`~openstruct.normative.nbr8800.compression.reduction_factor`,
    mas com uma formula diferente (a norma nao normaliza este caso
    como um fator adimensional ``chi``):

    - ``lambda <= lambda_p``: ``Vrd = Vpl/gamma_a1``;
    - ``lambda_p < lambda <= lambda_r``:
      ``Vrd = (lambda_p/lambda)*Vpl/gamma_a1``;
    - ``lambda > lambda_r``: ``Vrd = 1,24*(lambda_p/lambda)^2*Vpl/gamma_a1``.

    Generica o suficiente para ser reaproveitada pelos casos 5.4.3.2 a
    5.4.3.6 (mesma estrutura de formula, ``kv``/``Aw` diferentes) —
    fora do escopo desta fase, ver docstring do modulo.

    Nota: ha uma pequena descontinuidade (~0,4% relativo) exatamente
    em ``lambda = lambda_r``, pois ``lambda_r/lambda_p = 1,37/1,10 =
    1,24545...`` nao e exatamente igual a ``1,24`` (o coeficiente da
    formula do terceiro trecho). Mesma natureza da descontinuidade
    documentada em
    :func:`~openstruct.normative.nbr8800.compression.reduction_factor`
    (~1,7e-4 em ``lambda_0=1,5``): uma caracteristica das formulas
    empiricas da norma, nao um erro de implementacao — ambas as
    formulas foram transcritas exatamente como apresentadas no PDF.

    Parametros
    ----------
    plastic_shear_force:
        ``Vpl`` (N) — ver :func:`plastic_shear_force`.
    slenderness:
        Indice de esbeltez da alma, ``lambda = h/tw``.
    slenderness_limit_p, slenderness_limit_r:
        Limites ``lambda_p = 1,10*sqrt(kv*E/fy)`` e
        ``lambda_r = 1,37*sqrt(kv*E/fy)`` (calculados pelo chamador —
        ver :func:`shear_buckling_coefficient` para ``kv``).
    gamma_a1:
        Coeficiente de ponderacao da resistencia (NBR 8800:2024,
        4.9.2, Tabela 3) — este e um estado-limite de instabilidade,
        mesma categoria de ``gamma_a1`` usada em compressao.
    """
    if not is_positive_finite(plastic_shear_force):
        raise ValueError(
            f"shear_resistance: plastic_shear_force deve ser finito e positivo, "
            f"recebido {plastic_shear_force!r}."
        )
    if not is_positive_finite(slenderness):
        raise ValueError(
            f"shear_resistance: slenderness deve ser finito e positivo, "
            f"recebido {slenderness!r}."
        )
    if not is_positive_finite(slenderness_limit_p):
        raise ValueError(
            f"shear_resistance: slenderness_limit_p deve ser finito e positivo, "
            f"recebido {slenderness_limit_p!r}."
        )
    if not is_positive_finite(slenderness_limit_r):
        raise ValueError(
            f"shear_resistance: slenderness_limit_r deve ser finito e positivo, "
            f"recebido {slenderness_limit_r!r}."
        )
    if not slenderness_limit_r >= slenderness_limit_p:
        raise ValueError(
            f"shear_resistance: slenderness_limit_r ({slenderness_limit_r!r}) nao "
            f"pode ser menor que slenderness_limit_p ({slenderness_limit_p!r})."
        )
    if not is_positive_finite(gamma_a1):
        raise ValueError(
            f"shear_resistance: gamma_a1 deve ser finito e positivo, recebido {gamma_a1!r}."
        )

    if slenderness <= slenderness_limit_p:
        return plastic_shear_force / gamma_a1
    if slenderness <= slenderness_limit_r:
        return (slenderness_limit_p / slenderness) * plastic_shear_force / gamma_a1
    return 1.24 * (slenderness_limit_p / slenderness) ** 2 * plastic_shear_force / gamma_a1


@dataclass(frozen=True, slots=True)
class ShearCheckResult(CheckResult):
    """Resultado da verificacao ao cisalhamento de uma barra fletida (NBR 8800:2024, 5.4.1.3).

    Atributos
    ---------
    vsd:
        Forca cortante solicitante de calculo (N).
    vrd:
        Forca cortante resistente de calculo (N) — ver :func:`shear_resistance`.
    """

    vsd: float
    vrd: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.vsd):
            raise ValueError(f"ShearCheckResult.vsd deve ser finito, recebido {self.vsd!r}.")
        if not is_positive_finite(self.vrd):
            raise ValueError(
                f"ShearCheckResult.vrd deve ser finito e positivo, recebido {self.vrd!r}."
            )

    @property
    def sd(self) -> float:
        """Alias generico de :attr:`vsd` — ver :class:`CheckResult`."""
        return self.vsd

    @property
    def rd(self) -> float:
        """Alias generico de :attr:`vrd` — ver :class:`CheckResult`."""
        return self.vrd


def check_shear_major_axis(
    vsd: float,
    total_depth: float,
    web_clear_height: float,
    web_thickness: float,
    fy: float,
    elastic_modulus: float,
    stiffener_spacing: float | None,
    resistance_factors_gamma_a1: float,
) -> ShearCheckResult:
    """Verifica ao cisalhamento uma barra I/H/U fletida no eixo forte.

    NBR 8800:2024, 5.4.1.3/5.4.3.1.

    Parametros
    ----------
    vsd:
        Forca cortante solicitante de calculo (N).
    total_depth:
        Altura total da secao, ``d`` (mm) — usada em ``Aw=d*tw``.
    web_clear_height:
        Altura livre da alma, ``h`` (mm) — usada em ``lambda=h/tw`` e
        em ``kv``. Ver ATENCAO em :func:`shear_buckling_coefficient`
        sobre a diferenca entre ``h`` e ``d``.
    web_thickness:
        Espessura da alma, ``tw`` (mm).
    fy:
        Resistencia ao escoamento do aco (MPa).
    elastic_modulus:
        Modulo de elasticidade do aco, ``E`` (MPa).
    stiffener_spacing:
        Distancia entre enrijecedores transversais adjacentes (mm), ou
        ``None`` se a alma nao tiver enrijecedores transversais.
    resistance_factors_gamma_a1:
        ``gamma_a1`` (NBR 8800:2024, 4.9.2, Tabela 3) — passado como
        ``float`` direto (nao ``SteelResistanceFactors`` completo) pois
        esta verificacao usa apenas esse coeficiente.

    Retorna
    -------
    :class:`ShearCheckResult` com ``vrd``, a taxa de utilizacao e se a
    condicao de 5.4.1.3 e atendida.
    """
    if not math.isfinite(vsd):
        raise ValueError(f"check_shear_major_axis: vsd deve ser finito, recebido {vsd!r}.")
    if not is_positive_finite(elastic_modulus):
        raise ValueError(
            f"check_shear_major_axis: elastic_modulus deve ser finito e positivo, "
            f"recebido {elastic_modulus!r}."
        )
    if web_clear_height > total_depth:
        # h (altura livre da alma) e sempre menor que d (altura total,
        # que inclui as duas mesas) para qualquer secao real — mesmo
        # raciocinio das checagens Ae<=Ag/Aef<=Ag do resto do pacote.
        raise ValueError(
            f"check_shear_major_axis: web_clear_height ({web_clear_height!r}) nao pode "
            f"ser maior que total_depth ({total_depth!r})."
        )

    aw = effective_shear_area_major_axis(total_depth, web_thickness)
    vpl = plastic_shear_force(aw, fy)
    kv = shear_buckling_coefficient(web_clear_height, stiffener_spacing)
    lambda_ratio = web_clear_height / web_thickness
    lambda_p = 1.10 * math.sqrt(kv * elastic_modulus / fy)
    lambda_r = 1.37 * math.sqrt(kv * elastic_modulus / fy)
    vrd = shear_resistance(vpl, lambda_ratio, lambda_p, lambda_r, resistance_factors_gamma_a1)
    return ShearCheckResult(vsd=vsd, vrd=vrd)
