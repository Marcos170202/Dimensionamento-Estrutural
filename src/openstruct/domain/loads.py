"""Cargas: ``Load`` (base), ``NodalLoad``, ``LoadCase``, ``LoadCombination``.

Fonte: PROGRAM_MASTER.md secao 3 ("CORE ESTRUTURAL") e secao 10
("LOADS"): "Implementar: nodal loads, point loads, distributed loads,
self weight."

Escopo desta fase: **apenas cargas nodais** (``NodalLoad``). Cargas
concentradas/distribuidas ao longo do vao de um elemento e peso
proprio exigem calcular forcas nodais equivalentes (fixed-end forces)
e sao deixadas para uma fase seguinte — a abstracao ``Load`` (com
``apply_to()`` recebendo apenas uma funcao de indexacao de DOF, nao o
modelo inteiro) ja foi desenhada para acomodar esses tipos futuros sem
quebrar API: uma carga distribuida so precisa saber, alem da funcao de
indexacao, os dados do elemento em que atua — o metodo `apply_to` de
tais cargas futuras recebera o elemento como parametro adicional.

Convencao de unidades: ver ``material.py``/``section.py`` (N, mm, MPa)
— forcas em N, momentos em N.mm.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

import numpy as np

from .dof import DOF, NODE_DOF_ORDER

#: Assinatura da funcao de indexacao de DOF global, tipicamente
#: ``AnalysisModel.dof_index`` — mapeia (id do no, DOF) para o indice
#: da linha/coluna correspondente em um vetor/matriz global.
DofIndexer = Callable[[int, DOF], int]


class Load(ABC):
    """Uma carga que contribui para o vetor de forcas global.

    Subclasses implementam apenas ``apply_to`` — a montagem
    (``Assembly``) nunca soma vetores manualmente, sempre delega a
    este metodo, para que um tipo de carga futuro (distribuida,
    termica, peso proprio) baste implementar sua propria regra de
    equivalencia nodal sem alterar ``Assembly``.
    """

    # Sem isso, uma subclasse com @dataclass(slots=True) (ex.:
    # NodalLoad) ainda ganha um __dict__ por instancia herdado desta
    # base — silenciosamente anulando o proposito de slots=True (menos
    # memoria, __setattr__ arbitrario bloqueado) sem levantar nenhum
    # erro (CODE REVIEW AGENT, achado confirmado).
    __slots__ = ()

    @abstractmethod
    def apply_to(self, f_global: np.ndarray, dof_index: DofIndexer) -> None:
        """Soma a contribuicao desta carga em ``f_global`` (in-place).

        ``dof_index(node_id, dof)`` devolve o indice global do DOF —
        esta carga nao precisa (nem deve) conhecer o ``AnalysisModel``
        inteiro.
        """
        raise NotImplementedError  # pragma: no cover — corpo de metodo abstrato, nunca executado


@dataclass(frozen=True, slots=True)
class NodalLoad(Load):
    """Forca/momento aplicado diretamente em um no, em eixos GLOBAIS.

    Atributos
    ---------
    node_id:
        Id do no onde a carga e aplicada.
    fx, fy, fz:
        Forcas nas direcoes globais X, Y, Z (N).
    mx, my, mz:
        Momentos em torno dos eixos globais X, Y, Z (N.mm).
    """

    node_id: int
    fx: float = 0.0
    fy: float = 0.0
    fz: float = 0.0
    mx: float = 0.0
    my: float = 0.0
    mz: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, int) or isinstance(self.node_id, bool):
            raise TypeError(
                f"NodalLoad.node_id deve ser int, recebido {type(self.node_id).__name__}."
            )
        if self.node_id < 0:
            raise ValueError(
                f"NodalLoad.node_id deve ser nao-negativo, recebido {self.node_id!r}."
            )
        for name in ("fx", "fy", "fz", "mx", "my", "mz"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(
                    f"NodalLoad.{name} deve ser finito, recebido {value!r}."
                )

    @property
    def components(self) -> tuple[float, float, float, float, float, float]:
        """Os 6 componentes na ordem canonica de ``NODE_DOF_ORDER``."""
        return (self.fx, self.fy, self.fz, self.mx, self.my, self.mz)

    def apply_to(self, f_global: np.ndarray, dof_index: DofIndexer) -> None:
        for dof, value in zip(NODE_DOF_ORDER, self.components, strict=True):
            if value != 0.0:
                f_global[dof_index(self.node_id, dof)] += value


class LoadSource(Protocol):
    """Qualquer coisa que sabe contribuir para um vetor de forcas global.

    ``LoadCase`` e ``LoadCombination`` implementam este protocolo —
    usado apenas para tipagem (``Assembly.global_load_vector`` aceita
    qualquer um dos dois).
    """

    def apply_to(self, f_global: np.ndarray, dof_index: DofIndexer) -> None: ...


@dataclass(frozen=True, slots=True)
class LoadCase:
    """Um conjunto nomeado de cargas aplicadas simultaneamente.

    Atributos
    ---------
    name:
        Identificacao do caso (ex.: ``"Permanente"``, ``"Vento X"``).
    loads:
        As cargas deste caso.
    """

    name: str
    loads: tuple[Load, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("LoadCase.name nao pode ser vazio.")
        loads = tuple(self.loads)
        if not all(isinstance(load, Load) for load in loads):
            raise TypeError("LoadCase.loads deve conter apenas instancias de Load.")
        object.__setattr__(self, "loads", loads)

    def apply_to(self, f_global: np.ndarray, dof_index: DofIndexer) -> None:
        for load in self.loads:
            load.apply_to(f_global, dof_index)


@dataclass(frozen=True, slots=True)
class LoadCombination:
    """Combinacao linear de ``LoadCase`` (superposicao, valida em analise elastico-linear).

    Atributos
    ---------
    name:
        Identificacao da combinacao (ex.: ``"ELU-1"``).
    factors:
        Mapeamento ``LoadCase -> fator de ponderacao``. A resolucao de
        qual fator normativo usar (ex.: 1.4 para permanente
        desfavoravel) e responsabilidade de uma fase normativa futura
        — aqui os fatores sao apenas numeros ja decididos por quem
        monta o modelo.
    """

    name: str
    # hash=False: MappingProxyType (como dict, que envolve) nao e hasheavel;
    # sem isso, hash(LoadCombination(...)) levantaria TypeError (mesma
    # situacao de Section.dimensions, ver section.py).
    factors: Mapping[LoadCase, float] = field(hash=False)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("LoadCombination.name nao pode ser vazio.")
        if not self.factors:
            raise ValueError(
                f"LoadCombination({self.name!r}) precisa de ao menos um LoadCase."
            )
        for case, factor in self.factors.items():
            if not isinstance(case, LoadCase):
                raise TypeError(
                    "LoadCombination.factors deve mapear LoadCase -> float, "
                    f"chave invalida: {case!r}."
                )
            if not math.isfinite(factor):
                raise ValueError(
                    f"LoadCombination({self.name!r}): fator para "
                    f"{case.name!r} deve ser finito, recebido {factor!r}."
                )
        object.__setattr__(self, "factors", MappingProxyType(dict(self.factors)))

    def apply_to(self, f_global: np.ndarray, dof_index: DofIndexer) -> None:
        for case, factor in self.factors.items():
            case_vector = np.zeros_like(f_global)
            case.apply_to(case_vector, dof_index)
            f_global += factor * case_vector
