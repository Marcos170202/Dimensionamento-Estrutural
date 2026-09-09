"""Base compartilhada para resultados de verificacao normativa.

Toda verificacao da NBR 8800 segue o mesmo padrao "solicitante <=
resistente" (``Xd,Sd <= Xd,Rd``): tracao (5.2.1.2), compressao (5.3.1)
e as fases futuras desta mesma norma (flexao, cisalhamento, combinacao
de esforcos). Fatorado para nao duplicar a mesma logica de
``utilization``/``is_ok`` em cada nova ``*CheckResult`` — achado do
CODE REVIEW AGENT na fase de compressao (a duplicacao entre
``TensionCheckResult`` e ``CompressionCheckResult`` ja era real com
apenas duas classes; so cresceria a cada fase nova).

Modulo privado (prefixo ``_``): nao faz parte da API publica de
``openstruct.normative.nbr8800``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CheckResult(ABC):
    """Contrato comum: um resultado de verificacao normativa expoe um
    esforco solicitante (``sd``) e um esforco resistente (``rd``), dos
    quais ``utilization`` e ``is_ok`` sao sempre derivados da mesma
    forma (``sd/rd`` e ``sd <= rd``)."""

    # Mesmo padrao de Load/ElementLoad (domain/loads.py): sem isso, uma
    # subclasse com @dataclass(slots=True) ainda ganharia um __dict__
    # por instancia herdado desta base, anulando slots=True (CODE
    # REVIEW AGENT, achado original confirmado na fase SOLVER V1).
    __slots__ = ()

    @property
    @abstractmethod
    def sd(self) -> float:
        """Esforco solicitante de calculo (ex.: ``Nt,Sd``, ``Nc,Sd``)."""
        raise NotImplementedError  # pragma: no cover — corpo de metodo abstrato, nunca executado

    @property
    @abstractmethod
    def rd(self) -> float:
        """Esforco resistente de calculo (ex.: ``Nt,Rd``, ``Nc,Rd``)."""
        raise NotImplementedError  # pragma: no cover — corpo de metodo abstrato, nunca executado

    @property
    def utilization(self) -> float:
        """Taxa de utilizacao (``sd/rd``, ``<=1`` significa que a
        condicao de dimensionamento e atendida)."""
        return self.sd / self.rd

    @property
    def is_ok(self) -> bool:
        """Condicao de dimensionamento generica: ``sd <= rd``."""
        return self.sd <= self.rd
