"""Secao transversal de um elemento estrutural.

Fonte: PROGRAM_MASTER.md secao 6 ("SECTION"). Preparado para uma
futura biblioteca de perfis (PROGRAM_MASTER: "Preparar para biblioteca
futura de perfis") atraves do campo ``dimensions``, que guarda os
parametros geometricos de origem (ex.: altura, largura, espessuras)
sem prescrever ainda um catalogo especifico.

Convencao de unidades (ver nota em ``material.py``): sistema N, mm,
MPa. Consequentemente:

- ``A``            : mm^2
- ``Iy``, ``Iz``   : mm^4
- ``J``            : mm^4
- ``Wply``, ``Wplz``, ``Wely``, ``Welz`` : mm^3
- ``Cw``           : mm^6

Os eixos locais y/z sao os eixos principais de inercia da secao,
conforme convencao usada em ``elements/frame3d.py``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class Section:
    """Propriedades geometricas de uma secao transversal.

    Atributos
    ---------
    name:
        Identificacao da secao (ex.: ``"W 310x21"``).
    A:
        Area da secao transversal (mm^2).
    Iy:
        Momento de inercia em torno do eixo local y (mm^4).
    Iz:
        Momento de inercia em torno do eixo local z (mm^4).
    J:
        Constante de torcao de Saint-Venant (mm^4).
    Wply:
        Modulo plastico de resistencia em torno de y (mm^3).
    Wplz:
        Modulo plastico de resistencia em torno de z (mm^3).
    Wely:
        Modulo elastico de resistencia em torno de y (mm^3).
    Welz:
        Modulo elastico de resistencia em torno de z (mm^3).
    Cw:
        Constante de empenamento da secao (mm^6), usada em flambagem
        por torcao/flexo-torcao (ex.: NBR 8800:2024, 5.3.5.1-c).
        ``None`` (padrao) significa "nao caracterizada" — deliberado
        em vez de um valor numerico arbitrario (ex.: ``0.0``), que
        poderia ser confundido com um valor real (``Cw=0`` e
        fisicamente valido para secoes fechadas/tubulares). Qualquer
        verificacao que precise de ``Cw`` deve rejeitar explicitamente
        o caso ``None``, nunca assumir um valor.
    dimensions:
        Parametros geometricos de origem da secao (ex.:
        ``{"h": 310.0, "bf": 167.0, "tw": 5.6, "tf": 9.1}``).
        Nao interpretado pelo nucleo de calculo nesta fase; existe
        para rastreabilidade e para a futura biblioteca de perfis.
    """

    name: str
    A: float
    Iy: float
    Iz: float
    J: float
    Wply: float
    Wplz: float
    Wely: float
    Welz: float
    Cw: float | None = None
    dimensions: Mapping[str, float] = field(
        default_factory=lambda: MappingProxyType({}), hash=False
    )

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Section.name nao pode ser vazio.")

        # "not (valor > 0)" em vez de "valor <= 0": para NaN as duas
        # comparacoes (`> 0` e `<= 0`) valem False, entao "valor <= 0"
        # deixaria um NaN passar silenciosamente pela validacao
        # (CODE REVIEW AGENT, achado confirmado).
        for attr_name in ("A", "Iy", "Iz", "J", "Wply", "Wplz", "Wely", "Welz"):
            value = getattr(self, attr_name)
            if not (value > 0):
                raise ValueError(
                    f"Section.{attr_name} deve ser positivo, recebido {value!r}."
                )

        if not (self.Wply >= self.Wely):
            raise ValueError(
                f"Section.Wply ({self.Wply!r}) nao pode ser menor que Wely "
                f"({self.Wely!r}) — o modulo plastico e sempre >= ao elastico "
                "para qualquer secao real."
            )
        if not (self.Wplz >= self.Welz):
            raise ValueError(
                f"Section.Wplz ({self.Wplz!r}) nao pode ser menor que Welz "
                f"({self.Welz!r}) — o modulo plastico e sempre >= ao elastico "
                "para qualquer secao real."
            )

        if self.Cw is not None and not (self.Cw >= 0):
            # ">= 0" (nao "> 0"): Cw=0 e fisicamente valido para secoes
            # fechadas/tubulares (sem empenamento). "not (valor >= 0)"
            # em vez de "valor < 0" pelo mesmo motivo do bloco acima —
            # rejeita NaN corretamente.
            raise ValueError(f"Section.Cw deve ser nao-negativo, recebido {self.Cw!r}.")

        # dimensions precisa ser hasheavel/imutavel para manter o dataclass
        # congelavel e comparavel por valor (== / hash).
        object.__setattr__(self, "dimensions", MappingProxyType(dict(self.dimensions)))

    @property
    def shape_factor_y(self) -> float:
        """Fator de forma em torno de y: ``Wply / Wely`` (>= 1)."""
        return self.Wply / self.Wely

    @property
    def shape_factor_z(self) -> float:
        """Fator de forma em torno de z: ``Wplz / Welz`` (>= 1)."""
        return self.Wplz / self.Welz

    @property
    def radius_of_gyration_y(self) -> float:
        """Raio de giracao em torno do eixo local y: ``sqrt(Iy/A)`` (mm).

        Usado, por exemplo, na limitacao (recomendada, nao obrigatoria)
        do indice de esbeltez de barras tracionadas/comprimidas (NBR
        8800:2024, 5.2.8/5.3.7: ``L/r``)."""
        return math.sqrt(self.Iy / self.A)

    @property
    def radius_of_gyration_z(self) -> float:
        """Raio de giracao em torno do eixo local z: ``sqrt(Iz/A)`` (mm).

        Ver :attr:`radius_of_gyration_y`."""
        return math.sqrt(self.Iz / self.A)
