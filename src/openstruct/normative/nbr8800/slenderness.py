"""Limitacao (recomendada) do indice de esbeltez de barras tracionadas e comprimidas.

Fonte: ABNT NBR 8800:2024, 5.2.8.1 "Limitacao do indice de esbeltez e
requisito para barras compostas" (barras tracionadas, pagina 44) e
5.3.7.1 "Limitacao do indice de esbeltez" (barras comprimidas, pagina
52). Formulas/valores extraidos por leitura direta do PDF fornecido
pelo usuario — ver rastreabilidade completa em
``docs/normative/NBR8800-RULES.md``.

**Diferenca importante em relacao aos demais modulos deste pacote**:
esta NAO e uma verificacao de estado-limite ultimo obrigatoria. O
texto da norma usa "recomenda-se" (nao "deve"), e 5.2.8.3 explicita
que, se a recomendacao nao for adotada, cabe ao responsavel tecnico
pelo projeto estabelecer novos limites — nao ha uma condicao binaria
"aprovado/reprovado" equivalente a ``Nt,Sd <= Nt,Rd``. Por isso
``SlendernessCheckResult`` nao herda de
:class:`~openstruct.normative.nbr8800._check_result.CheckResult` (que
modela especificamente o padrao "solicitante <= resistente") e expoe
``is_within_recommended_limit`` em vez de ``is_ok``.

Escopo desta fase: apenas o caso mais simples de cada secao — barra
tracionada individual (5.2.8.1) ou comprimida individual (5.3.7.1),
usando o maior indice de esbeltez entre os eixos principais.

**Fora do escopo**: 5.2.8.2 (requisito adicional para barras
COMPOSTAS tracionadas — indice de esbeltez de cada perfil componente
entre ligacoes adjacentes) e a parte equivalente implicita em 5.3.7.1
para barras compostas comprimidas (``Ne,m``, ja parcialmente coberta
por 5.3.6.3, tambem fora do escopo desta fase) — ambas requerem
modelagem de barras compostas (multiplos perfis com ligacoes
intermediarias), ainda nao presente no dominio geometrico atual.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._validation import is_positive_finite

#: NBR 8800:2024, 5.2.8.1 (RULE-ID NBR8800-TRAC-004): indice de
#: esbeltez recomendado para barras tracionadas, excetuando-se
#: tirantes de barras redondas pre-tensionadas ou outras barras
#: montadas com pre-tensao (nao modelados aqui — ver docstring do
#: modulo).
TENSION_SLENDERNESS_LIMIT = 300.0

#: NBR 8800:2024, 5.3.7.1 (RULE-ID NBR8800-COMP-008): indice de
#: esbeltez recomendado para barras comprimidas.
COMPRESSION_SLENDERNESS_LIMIT = 200.0


def slenderness_ratio(length: float, radius_of_gyration: float) -> float:
    """Indice de esbeltez, ``ell/r`` (NBR 8800:2024, 5.2.8.1/5.3.7.1).

    Parametros
    ----------
    length:
        Comprimento destravado da barra, ``ell`` (mm) — para
        compressao, especificamente o "comprimento destravado
        associado a flexao" (5.3.7.1); tipicamente ``KL`` (ja incluido
        o fator de comprimento efetivo ``K``, nao calculado por este
        modulo).
    radius_of_gyration:
        Raio de giracao correspondente ao mesmo eixo de flexao usado
        para ``length`` (mm) — tipicamente
        ``section.radius_of_gyration_y`` ou ``radius_of_gyration_z``.
        A norma pede o MAIOR indice de esbeltez entre os eixos
        principais — o chamador deve calcular ``slenderness_ratio``
        para cada eixo e tomar o maior valor (ver
        :func:`check_tension_slenderness`/:func:`check_compression_slenderness`,
        que ja fazem isso).
    """
    if not is_positive_finite(length):
        raise ValueError(
            f"slenderness_ratio: length deve ser finito e positivo, recebido {length!r}."
        )
    if not is_positive_finite(radius_of_gyration):
        raise ValueError(
            f"slenderness_ratio: radius_of_gyration deve ser finito e positivo, "
            f"recebido {radius_of_gyration!r}."
        )
    return length / radius_of_gyration


@dataclass(frozen=True, slots=True)
class SlendernessCheckResult:
    """Resultado da verificacao (recomendada, nao obrigatoria) do indice de esbeltez.

    Ver docstring do modulo para o porque de nao seguir o padrao
    ``CheckResult`` (solicitante/resistente) do resto do pacote.

    Atributos
    ---------
    ratio:
        Indice de esbeltez calculado, ``ell/r`` (o maior entre os
        eixos principais).
    limit:
        Limite recomendado pela norma (300 para tracao — 5.2.8.1; 200
        para compressao — 5.3.7.1).
    """

    ratio: float
    limit: float

    def __post_init__(self) -> None:
        if not is_positive_finite(self.ratio):
            raise ValueError(
                f"SlendernessCheckResult.ratio deve ser finito e positivo, "
                f"recebido {self.ratio!r}."
            )
        if not is_positive_finite(self.limit):
            raise ValueError(
                f"SlendernessCheckResult.limit deve ser finito e positivo, "
                f"recebido {self.limit!r}."
            )

    @property
    def is_within_recommended_limit(self) -> bool:
        """``True`` se ``ratio <= limit`` (dentro da recomendacao da norma).

        ``False`` NAO significa reprovacao normativa — significa que,
        conforme 5.2.8.3 (tracao; sem clausula equivalente explicita
        para compressao em 5.3.7), cabe ao responsavel tecnico pelo
        projeto estabelecer novos limites justificados para essa
        barra."""
        return self.ratio <= self.limit


def check_tension_slenderness(
    length_y: float,
    radius_of_gyration_y: float,
    length_z: float,
    radius_of_gyration_z: float,
) -> SlendernessCheckResult:
    """Verifica o indice de esbeltez recomendado de uma barra tracionada.

    NBR 8800:2024, 5.2.8.1: limite recomendado de 300, considerado
    como a MAIOR relacao entre o comprimento destravado e o raio de
    giracao correspondente — daqui o calculo em torno de AMBOS os
    eixos principais, tomando o maior.

    Parametros
    ----------
    length_y, length_z:
        Comprimentos destravados associados a flexao em torno de cada
        eixo principal (mm).
    radius_of_gyration_y, radius_of_gyration_z:
        Raios de giracao correspondentes (mm) — tipicamente
        ``section.radius_of_gyration_y``/``radius_of_gyration_z``.
    """
    ratio_y = slenderness_ratio(length_y, radius_of_gyration_y)
    ratio_z = slenderness_ratio(length_z, radius_of_gyration_z)
    return SlendernessCheckResult(ratio=max(ratio_y, ratio_z), limit=TENSION_SLENDERNESS_LIMIT)


def check_compression_slenderness(
    length_y: float,
    radius_of_gyration_y: float,
    length_z: float,
    radius_of_gyration_z: float,
) -> SlendernessCheckResult:
    """Verifica o indice de esbeltez recomendado de uma barra comprimida.

    NBR 8800:2024, 5.3.7.1: limite recomendado de 200, mesma logica de
    :func:`check_tension_slenderness` (maior indice entre os dois
    eixos principais).

    Parametros
    ----------
    length_y, length_z:
        Comprimentos destravados associados a flexao em torno de cada
        eixo principal (mm) — tipicamente os mesmos ``Ly``/``Lz`` de
        :func:`~openstruct.normative.nbr8800.compression.flexural_buckling_force`.
    radius_of_gyration_y, radius_of_gyration_z:
        Raios de giracao correspondentes (mm).
    """
    ratio_y = slenderness_ratio(length_y, radius_of_gyration_y)
    ratio_z = slenderness_ratio(length_z, radius_of_gyration_z)
    return SlendernessCheckResult(
        ratio=max(ratio_y, ratio_z), limit=COMPRESSION_SLENDERNESS_LIMIT
    )
