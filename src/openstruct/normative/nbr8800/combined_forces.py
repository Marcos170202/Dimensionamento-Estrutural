"""Barras prismaticas submetidas a esforcos combinados.

Fonte: ABNT NBR 8800:2024, 5.5 "Barras prismaticas submetidas a
esforcos combinados", 5.5.1 "Barras submetidas a momentos fletores,
forca axial e forcas cortantes" (paginas 60-61). Formulas extraidas
por leitura direta do PDF fornecido pelo usuario — ver rastreabilidade
completa em ``docs/normative/NBR8800-RULES.md``.

Escopo desta fase: apenas 5.5.1.1/5.5.1.2 — interacao entre forca
axial (tracao OU compressao, o que for aplicavel) e momento fletor
biaxial, para barras SEM torcao. Cobre:

- 5.5.1.2 — as duas equacoes de interacao (``Nsd/Nrd>=0,2`` e
  ``Nsd/Nrd<0,2``), reunidas em
  :func:`axial_bending_interaction_ratio`/:func:`check_axial_and_bending_interaction`.

5.5.1.3 (forca cortante) NAO precisa de nenhuma formula nova: a propria
norma remete diretamente a 5.4.3 (ja implementado em ``shear.py``) —
"a verificacao da barra a esse esforco deve ser feita conforme 5.4.3"
quando a forca cortante atua em um unico eixo central de inercia. O
caso de forca cortante atuando SIMULTANEAMENTE nos dois eixos remete a
5.5.2.3-b)/d) (secoes tubulares combinadas com torcao) — fora do
escopo, ver abaixo.

**Fora do escopo** (ver ``docs/normative/NBR8800-RULES.md`` para o
registro completo): 5.5.2 (secoes tubulares circulares e retangulares
submetidas a momento de torcao, forca axial, momentos fletores e forca
cortante — inclui `Trd` para torcao pura, 5.5.2.1/5.5.2.1.2/5.5.2.1.3,
e a equacao de interacao com torcao, 5.5.2.2). O dominio geometrico
atual (`Section`) nao distingue secoes tubulares de I/H/U, e a
verificacao de torcao pura (`Trd`) nunca foi implementada em nenhuma
fase anterior deste pacote — adicionar 5.5.2 exigiria primeiro abrir
essas duas frentes, um escopo maior que o deste incremento.

**ATENCAO sobre magnitude de Nsd/Msd**: diferente de
``ShearCheckResult``/``FlexureCheckResult`` (onde ``vsd``/``msd``
aceitam qualquer sinal e o chamador e responsavel por passar a
magnitude quando for o caso — ver ATENCAO nesses modulos), as funcoes
deste modulo EXIGEM que ``n_sd``, ``mx_sd`` e ``my_sd`` ja sejam
passados como magnitudes (>=0), levantando ``ValueError`` caso
contrario. Essa e uma decisao de projeto deliberada, tomada
justamente para NAO repetir aqui o mesmo achado do CODE REVIEW AGENT
que ficou apenas documentado (nao corrigido, por compatibilidade
retroativa) nos dois modulos citados.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ._check_result import CheckResult
from ._validation import is_non_negative_finite, is_positive_finite


def axial_bending_interaction_ratio(
    n_sd: float,
    n_rd: float,
    mx_sd: float,
    mx_rd: float,
    my_sd: float,
    my_rd: float,
) -> float:
    """Razao de interacao entre forca axial e momento fletor biaxial (NBR 8800:2024, 5.5.1.2).

    - ``Nsd/Nrd >= 0,2``:
      ``Nsd/Nrd + (8/9)*(Mx,sd/Mx,rd + My,sd/My,rd)``;
    - ``Nsd/Nrd < 0,2``:
      ``Nsd/(2*Nrd) + (Mx,sd/Mx,rd + My,sd/My,rd)``.

    A barra atende a condicao de 5.5.1.2 se o valor retornado for
    ``<= 1,0`` — ver :func:`check_axial_and_bending_interaction`.

    Parametros
    ----------
    n_sd:
        Forca axial solicitante de calculo, de TRACAO OU COMPRESSAO (a
        que for aplicavel), em MAGNITUDE (``>=0``) — ver ATENCAO no
        docstring do modulo.
    n_rd:
        Forca axial resistente de calculo correspondente ao mesmo tipo
        de esforco de ``n_sd`` (``Nt,Rd`` conforme 5.2 — ver
        ``tension.check_tension_member`` — ou ``Nc,Rd`` conforme 5.3 —
        ver ``compression.check_compression_member``).
    mx_sd, my_sd:
        Momentos fletores solicitantes de calculo em relacao aos eixos
        x e y da secao transversal, em MAGNITUDE (``>=0``) — ver
        ATENCAO no docstring do modulo. Podem ser zero (ex.: barra sem
        momento em um dos eixos).
    mx_rd, my_rd:
        Momentos fletores resistentes de calculo correspondentes,
        determinados conforme 5.4.2 — ver
        ``flexure.check_flexural_resistance_major_axis`` para o eixo
        de maior momento de inercia (o eixo de menor momento de
        inercia nao esta implementado, ver ATENCAO no docstring do
        modulo ``flexure``).
    """
    if not is_non_negative_finite(n_sd):
        raise ValueError(
            f"axial_bending_interaction_ratio: n_sd deve ser finito e "
            f"nao-negativo (magnitude), recebido {n_sd!r}."
        )
    if not is_positive_finite(n_rd):
        raise ValueError(
            f"axial_bending_interaction_ratio: n_rd deve ser finito e positivo, recebido {n_rd!r}."
        )
    if not is_non_negative_finite(mx_sd):
        raise ValueError(
            f"axial_bending_interaction_ratio: mx_sd deve ser finito e "
            f"nao-negativo (magnitude), recebido {mx_sd!r}."
        )
    if not is_positive_finite(mx_rd):
        raise ValueError(
            f"axial_bending_interaction_ratio: mx_rd deve ser finito e "
            f"positivo, recebido {mx_rd!r}."
        )
    if not is_non_negative_finite(my_sd):
        raise ValueError(
            f"axial_bending_interaction_ratio: my_sd deve ser finito e "
            f"nao-negativo (magnitude), recebido {my_sd!r}."
        )
    if not is_positive_finite(my_rd):
        raise ValueError(
            f"axial_bending_interaction_ratio: my_rd deve ser finito e "
            f"positivo, recebido {my_rd!r}."
        )

    ratio_n = n_sd / n_rd
    bending_term = mx_sd / mx_rd + my_sd / my_rd
    if ratio_n >= 0.2:
        return ratio_n + (8.0 / 9.0) * bending_term
    return ratio_n / 2.0 + bending_term


@dataclass(frozen=True, slots=True)
class CombinedForcesCheckResult(CheckResult):
    """Resultado da verificacao a esforcos combinados de uma barra (NBR 8800:2024, 5.5.1.2).

    Atributos
    ---------
    n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd:
        Ver :func:`axial_bending_interaction_ratio`.
    interaction_ratio:
        Valor da equacao de interacao (5.5.1.2-a ou -b, conforme
        ``n_sd/n_rd``) — a barra atende a condicao normativa se
        ``interaction_ratio <= 1,0`` (``is_ok``).
    """

    n_sd: float
    n_rd: float
    mx_sd: float
    mx_rd: float
    my_sd: float
    my_rd: float
    interaction_ratio: float

    def __post_init__(self) -> None:
        if not is_non_negative_finite(self.n_sd):
            raise ValueError(
                f"CombinedForcesCheckResult.n_sd deve ser finito e "
                f"nao-negativo, recebido {self.n_sd!r}."
            )
        if not is_positive_finite(self.n_rd):
            raise ValueError(
                f"CombinedForcesCheckResult.n_rd deve ser finito e positivo, "
                f"recebido {self.n_rd!r}."
            )
        if not is_non_negative_finite(self.mx_sd):
            raise ValueError(
                f"CombinedForcesCheckResult.mx_sd deve ser finito e "
                f"nao-negativo, recebido {self.mx_sd!r}."
            )
        if not is_positive_finite(self.mx_rd):
            raise ValueError(
                f"CombinedForcesCheckResult.mx_rd deve ser finito e positivo, "
                f"recebido {self.mx_rd!r}."
            )
        if not is_non_negative_finite(self.my_sd):
            raise ValueError(
                f"CombinedForcesCheckResult.my_sd deve ser finito e "
                f"nao-negativo, recebido {self.my_sd!r}."
            )
        if not is_positive_finite(self.my_rd):
            raise ValueError(
                f"CombinedForcesCheckResult.my_rd deve ser finito e positivo, "
                f"recebido {self.my_rd!r}."
            )
        if not math.isfinite(self.interaction_ratio) or self.interaction_ratio < 0:
            raise ValueError(
                f"CombinedForcesCheckResult.interaction_ratio deve ser finito "
                f"e nao-negativo, recebido {self.interaction_ratio!r}."
            )

    @property
    def sd(self) -> float:
        """Alias generico — o proprio ``interaction_ratio`` (ver :class:`CheckResult`)."""
        return self.interaction_ratio

    @property
    def rd(self) -> float:
        """Alias generico — sempre ``1,0`` (o limite da equacao de interacao)."""
        return 1.0


def check_axial_and_bending_interaction(
    n_sd: float,
    n_rd: float,
    mx_sd: float,
    mx_rd: float,
    my_sd: float,
    my_rd: float,
) -> CombinedForcesCheckResult:
    """Verifica a interacao entre forca axial e momento fletor biaxial (NBR 8800:2024, 5.5.1).

    Ver :func:`axial_bending_interaction_ratio` para as formulas e
    ATENCAO no docstring do modulo sobre a exigencia de magnitude em
    ``n_sd``/``mx_sd``/``my_sd``.

    Retorna
    -------
    :class:`CombinedForcesCheckResult` com ``interaction_ratio``, a
    taxa de utilizacao (identica a ``interaction_ratio``, pois o
    limite normativo e sempre ``1,0``) e se a condicao de 5.5.1.2 e
    atendida.
    """
    ratio = axial_bending_interaction_ratio(
        n_sd=n_sd, n_rd=n_rd, mx_sd=mx_sd, mx_rd=mx_rd, my_sd=my_sd, my_rd=my_rd
    )
    return CombinedForcesCheckResult(
        n_sd=n_sd,
        n_rd=n_rd,
        mx_sd=mx_sd,
        mx_rd=mx_rd,
        my_sd=my_sd,
        my_rd=my_rd,
        interaction_ratio=ratio,
    )
