"""Cargas: ``Load``/``ElementLoad`` (base), ``NodalLoad``, ``DistributedLoad``,
``LoadCase``, ``LoadCombination``, ``self_weight_loads``.

Fonte: PROGRAM_MASTER.md secao 3 ("CORE ESTRUTURAL") e secao 10
("LOADS"): "Implementar: nodal loads, point loads, distributed loads,
self weight."

Escopo desta fase: cargas nodais (``NodalLoad``), cargas uniformemente
distribuidas ao longo do vao de um ``Element3D`` (``DistributedLoad``)
e peso proprio automatico (``self_weight_loads``, calculado de
material/secao de cada elemento). Carga concentrada NO MEIO DO VAO
(nao nos nos) fica para uma fase seguinte.

Convencao de unidades: ver ``material.py``/``section.py`` (N, mm, MPa)
— forcas em N, momentos em N.mm, cargas distribuidas em N/mm.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

import numpy as np

from .dof import NODE_DOF_ORDER, DofIndexer
from .elements.base import Element, element_dof_indices
from .elements.frame3d import Element3D
from .model import AnalysisModel


class Load(ABC):
    """Uma carga NODAL que contribui para o vetor de forcas global.

    Subclasses implementam apenas ``apply_to`` — a montagem
    (``Assembly``) nunca soma vetores manualmente, sempre delega a
    este metodo. Para cargas que atuam ao longo de um elemento (nao
    diretamente em um no), ver :class:`ElementLoad`.
    """

    # Sem isso, uma subclasse com @dataclass(slots=True) (ex.:
    # NodalLoad) ainda ganha um __dict__ por instancia herdado desta
    # base — silenciosamente anulando o proposito de slots=True (menos
    # memoria, __setattr__ arbitrario bloqueado) sem levantar nenhum
    # erro (CODE REVIEW AGENT, achado confirmado na fase SOLVER V1).
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


class ElementLoad(ABC):
    """Uma carga que atua AO LONGO de um elemento (nao diretamente em um no).

    Subclasses implementam apenas ``fixed_end_forces_local`` — o
    vetor de 12 forcas/momentos (eixos LOCAIS do elemento) que esta
    carga produziria nas duas extremidades SE ambas fossem
    perfeitamente engastadas (o "consistent load vector" da literatura
    de elementos finitos, obtido por trabalho virtual com as mesmas
    funcoes de forma usadas em ``Element3D.local_stiffness_matrix()``
    — ver docstring de ``DistributedLoad`` para a derivacao).

    A partir dele, ``apply_to`` (implementado uma unica vez aqui,
    igual ao padrao de ``Element.global_stiffness_matrix()`` em
    ``elements/base.py`` — ver ADR-001) faz duas coisas:

    1. Soma ``+T^T @ fef_local`` a ``f_global`` (mesma regra de
       transformacao contravariante de qualquer forca local->global).
    2. NAO calcula esforcos internos aqui — isso e responsabilidade de
       ``run_analysis``, que subtrai ``fixed_end_forces_local`` do
       resultado de ``k_local @ u_local`` (ver
       ``results/analysis_result.py`` e VAL-0003 para a justificativa
       do sinal).
    """

    __slots__ = ()

    #: Id do ``Element`` sobre o qual esta carga atua — toda subclasse
    #: precisa dele (usado por ``LoadCase``/``LoadCombination`` para
    #: resolver o ``Element`` correspondente antes de chamar
    #: ``apply_to``/``fixed_end_forces_local``), entao e declarado
    #: aqui como parte do contrato em vez de reimplementado em cada
    #: subclasse.
    element_id: int

    @abstractmethod
    def fixed_end_forces_local(self, element: Element) -> np.ndarray:
        """Vetor (12,) de forcas/momentos LOCAIS de engastamento perfeito."""
        raise NotImplementedError  # pragma: no cover — corpo de metodo abstrato, nunca executado

    def apply_to(self, f_global: np.ndarray, element: Element, dof_index: DofIndexer) -> None:
        fef_local = self.fixed_end_forces_local(element)
        equivalent_global: np.ndarray = element.transformation_matrix().T @ fef_local
        indices = element_dof_indices(element, dof_index)
        f_global[indices] += equivalent_global


@dataclass(frozen=True, slots=True)
class DistributedLoad(ElementLoad):
    """Carga uniformemente distribuida ao longo do vao de um ``Element3D``.

    Atributos
    ---------
    element_id:
        Id do elemento onde a carga atua.
    wx, wy, wz:
        Intensidade da carga distribuida (N/mm) nas direcoes LOCAIS
        x, y, z do elemento (eixo x = eixo da barra).

    Derivacao (vetor de carga consistente / "fixed-end forces")
    --------------------------------------------------------------
    Via trabalho virtual com as funcoes de forma cubicas de Hermite
    (as mesmas que geram a matriz de rigidez classica de
    ``local_stiffness_matrix()``), o vetor de carga nodal equivalente
    a uma carga uniforme ``w`` no par translacao/rotacao ``(v, theta)``
    com ``dv/dx = +theta`` (nosso par UY/RZ, ver frame3d.py) e:

        f = [w*L/2, w*L^2/12, w*L/2, -w*L^2/12]

    resultado padrao de qualquer livro-texto de elementos finitos
    (p.ex. Logan, "A First Course in the Finite Element Method";
    Cook/Malkus/Plesha, "Concepts and Applications of Finite Element
    Analysis") — nao e um requisito normativo.

    Para o par UZ/RY, a relacao cinematica e invertida
    (``dw/dx = -theta_y``, ver frame3d.py) — substituindo
    ``theta_y = -phi`` (onde ``phi`` e a variavel "padrao" com
    ``dw/dx=+phi``) e usando invariancia do trabalho virtual
    (``f_phi * d(phi) = f_theta_y * d(theta_y)``), o termo de momento
    troca de sinal: ``f_theta_y = -f_phi``.

    Esse vetor e adicionado DIRETAMENTE a ``F_global`` (mesma regra de
    qualquer forca, ``ElementLoad.apply_to``) e SUBTRAIDO na extracao
    de esforcos internos (``run_analysis``) — ambos os sinais validados
    numericamente em VAL-0003 contra vigas simplesmente apoiada e em
    balanco sob carga uniforme.
    """

    element_id: int
    wx: float = 0.0
    wy: float = 0.0
    wz: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.element_id, int) or isinstance(self.element_id, bool):
            raise TypeError(
                f"DistributedLoad.element_id deve ser int, recebido "
                f"{type(self.element_id).__name__}."
            )
        if self.element_id < 0:
            raise ValueError(
                f"DistributedLoad.element_id deve ser nao-negativo, "
                f"recebido {self.element_id!r}."
            )
        for name in ("wx", "wy", "wz"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(
                    f"DistributedLoad.{name} deve ser finito, recebido {value!r}."
                )

    def fixed_end_forces_local(self, element: Element) -> np.ndarray:
        if element.id != self.element_id:
            raise ValueError(
                f"DistributedLoad.element_id={self.element_id!r} nao corresponde "
                f"ao elemento fornecido (id={element.id!r})."
            )
        if not isinstance(element, Element3D):
            raise TypeError(
                f"DistributedLoad so suporta Element3D nesta fase, recebido "
                f"{type(element).__name__}."
            )

        length = element.length
        length_sq = length * length
        fef = np.zeros(12)

        # axial (funcoes de forma lineares, sem ambiguidade de sinal)
        fef[0] += self.wx * length / 2.0
        fef[6] += self.wx * length / 2.0

        # flexao em torno de z (par UY/RZ, dv/dx=+theta_z, ver frame3d.py)
        fef[1] += self.wy * length / 2.0
        fef[5] += self.wy * length_sq / 12.0
        fef[7] += self.wy * length / 2.0
        fef[11] += -self.wy * length_sq / 12.0

        # flexao em torno de y (par UZ/RY, dw/dx=-theta_y -> sinal invertido)
        fef[2] += self.wz * length / 2.0
        fef[4] += -self.wz * length_sq / 12.0
        fef[8] += self.wz * length / 2.0
        fef[10] += self.wz * length_sq / 12.0

        return fef


class LoadSource(Protocol):
    """Qualquer coisa que sabe contribuir para um vetor de forcas global.

    ``LoadCase`` e ``LoadCombination`` implementam este protocolo —
    usado apenas para tipagem (``Assembly.global_load_vector`` aceita
    qualquer um dos dois).
    """

    def apply_to(
        self, f_global: np.ndarray, dof_index: DofIndexer, elements: Mapping[int, Element]
    ) -> None: ...

    def fixed_end_forces_local_for(self, element: Element) -> np.ndarray: ...


#: Mapeamento vazio reutilizado como default para chamadas que nao
#: envolvem nenhum ElementLoad (evita alocar um dict novo a cada
#: chamada e mantem os testes/chamadas antigas — so com NodalLoad —
#: funcionando sem precisar passar `elements` explicitamente).
_NO_ELEMENTS: Mapping[int, Element] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class LoadCase:
    """Um conjunto nomeado de cargas aplicadas simultaneamente.

    Atributos
    ---------
    name:
        Identificacao do caso (ex.: ``"Permanente"``, ``"Vento X"``).
    loads:
        Cargas NODAIS deste caso.
    element_loads:
        Cargas que atuam AO LONGO de um elemento (ex.: ``DistributedLoad``).
    """

    name: str
    loads: tuple[Load, ...] = field(default_factory=tuple)
    element_loads: tuple[ElementLoad, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("LoadCase.name nao pode ser vazio.")
        loads = tuple(self.loads)
        if not all(isinstance(load, Load) for load in loads):
            raise TypeError("LoadCase.loads deve conter apenas instancias de Load.")
        object.__setattr__(self, "loads", loads)

        element_loads = tuple(self.element_loads)
        if not all(isinstance(load, ElementLoad) for load in element_loads):
            raise TypeError(
                "LoadCase.element_loads deve conter apenas instancias de ElementLoad."
            )
        object.__setattr__(self, "element_loads", element_loads)

    def apply_to(
        self,
        f_global: np.ndarray,
        dof_index: DofIndexer,
        elements: Mapping[int, Element] = _NO_ELEMENTS,
    ) -> None:
        for load in self.loads:
            load.apply_to(f_global, dof_index)
        for element_load in self.element_loads:
            element = elements.get(element_load.element_id)
            if element is None:
                raise KeyError(
                    f"LoadCase({self.name!r}): ElementLoad referencia Element "
                    f"id={element_load.element_id!r}, que nao esta no mapeamento "
                    "de elementos fornecido (ver AnalysisModel.add_element)."
                )
            element_load.apply_to(f_global, element, dof_index)

    def fixed_end_forces_local_for(self, element: Element) -> np.ndarray:
        """Soma as ``fixed_end_forces_local`` de todo ``ElementLoad`` deste caso
        que atua sobre ``element`` (vetor (12,) de zeros se nenhum atuar).

        NUMERICAL METHODS AGENT / CODE REVIEW AGENT: esta busca e
        O(len(element_loads)) e ``run_analysis`` chama isto uma vez por
        elemento do modelo, dando O(num_elements x num_element_loads)
        no total. Para os modelos desta fase (dezenas de elementos) o
        custo e irrelevante; agrupar ``element_loads`` por
        ``element_id`` em ``__post_init__`` reduziria para
        O(num_elements), mas fica para quando um modelo real tornar
        isso um gargalo medido — otimizacao especulativa agora
        arriscaria introduzir um bug por um ganho que ninguem sentiria
        (PROGRAM_MASTER.md secao 35: correcao > performance).
        """
        total = np.zeros(element.num_dofs)
        for element_load in self.element_loads:
            if element_load.element_id == element.id:
                total += element_load.fixed_end_forces_local(element)
        return total


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

    def apply_to(
        self,
        f_global: np.ndarray,
        dof_index: DofIndexer,
        elements: Mapping[int, Element] = _NO_ELEMENTS,
    ) -> None:
        for case, factor in self.factors.items():
            case_vector = np.zeros_like(f_global)
            case.apply_to(case_vector, dof_index, elements)
            f_global += factor * case_vector

    def fixed_end_forces_local_for(self, element: Element) -> np.ndarray:
        total = np.zeros(element.num_dofs)
        for case, factor in self.factors.items():
            total += factor * case.fixed_end_forces_local_for(element)
        return total


#: Aceleracao da gravidade padrao — em METROS por segundo ao quadrado
#: (``9.81``), NAO milimetros (``9810``), apesar de todo o resto deste
#: projeto usar mm — ver docstring de ``self_weight_loads`` para a
#: justificativa dimensional completa.
DEFAULT_GRAVITY = 9.81

#: Direcao padrao da gravidade: eixo global Z negativo (convencao
#: "Z para cima", ja usada em todos os exemplos deste projeto — ver
#: VAL-0002/VAL-0003, onde colunas sobem em +Z). Para um modelo que
#: usa outro eixo como vertical, passe ``direction`` explicitamente.
DEFAULT_GRAVITY_DIRECTION = (0.0, 0.0, -1.0)


def self_weight_loads(
    model: AnalysisModel,
    gravity: float = DEFAULT_GRAVITY,
    direction: tuple[float, float, float] = DEFAULT_GRAVITY_DIRECTION,
) -> tuple[DistributedLoad, ...]:
    """Gera uma ``DistributedLoad`` de peso proprio para cada elemento do modelo.

    Nao e uma classe de carga nova — e uma FABRICA que calcula, para
    cada ``Element3D`` do modelo, a intensidade da carga distribuida
    devida ao proprio peso (``material.density * section.A *
    gravity``, projetada nos eixos LOCAIS do elemento) e devolve uma
    ``DistributedLoad`` pronta para entrar em
    ``LoadCase.element_loads`` — exatamente como se cada uma tivesse
    sido escrita a mao.

    Convencao de unidades (ATENCAO — a armadilha classica de peso
    proprio em sistemas mm)
    ------------------------------------------------------------------
    Este projeto usa N, mm, MPa (ver ``material.py``), com
    ``Material.density`` em **kg/mm^3**. Para o peso por unidade de
    comprimento sair diretamente em N/mm (sem nenhum fator de
    conversao extra), ``gravity`` precisa estar em **METROS por
    segundo ao quadrado** (``9.81``), NAO em mm/s^2 (``9810``):

        kg/mm^3 (density) * mm^2 (A) = kg/mm (massa por comprimento)
        kg/mm (massa/comp.) * m/s^2 (gravity) = (kg*m/s^2)/mm = N/mm

    porque ``N = kg*m/s^2`` por definicao (SI) — o "m" de "m/s^2" e o
    mesmo "m" que aparece em N, entao ele cancela corretamente contra
    o "kg" sem precisar converter para mm. Se ``gravity=9810`` fosse
    usado aqui, o resultado sairia 1000x maior que o correto. Este
    calculo foi validado numericamente (perfil ~21 kg/m -> peso
    ~206 N/m) em VAL-0004.

    Parametros
    ----------
    model:
        Modelo cujos elementos receberao peso proprio. Todos os
        elementos devem ser ``Element3D`` (unico tipo suportado nesta
        fase, mesma limitacao de ``DistributedLoad``).
    gravity:
        Aceleracao da gravidade, em m/s^2 (padrao ``9.81``). Deve ser
        positiva — o SENTIDO da gravidade e definido por
        ``direction``, nao pelo sinal de ``gravity``.
    direction:
        Vetor (nao precisa ser unitario) na direcao em que a
        gravidade atua, em coordenadas GLOBAIS. Padrao ``(0,0,-1)``
        (eixo Z global aponta "para cima", convencao usada em todo
        este projeto — ver VAL-0002/VAL-0003).

    Retorna
    -------
    Uma ``DistributedLoad`` por elemento do modelo, na ordem de
    ``model.elements``. Lista vazia se o modelo nao tiver elementos.
    """
    if not math.isfinite(gravity) or gravity <= 0:
        raise ValueError(
            f"self_weight_loads: gravity deve ser positivo e finito, "
            f"recebido {gravity!r} (o sentido da gravidade e definido "
            "por 'direction', nao pelo sinal de 'gravity')."
        )

    direction_vector = np.asarray(direction, dtype=float)
    if direction_vector.shape != (3,) or not np.all(np.isfinite(direction_vector)):
        raise ValueError(
            f"self_weight_loads: direction deve ser um vetor 3D finito, "
            f"recebido {direction!r}."
        )
    norm = np.linalg.norm(direction_vector)
    if norm < 1e-12:
        raise ValueError("self_weight_loads: direction nao pode ser o vetor nulo.")
    direction_unit = direction_vector / norm

    loads: list[DistributedLoad] = []
    for element in model.elements.values():
        if not isinstance(element, Element3D):
            raise TypeError(
                f"self_weight_loads so suporta Element3D nesta fase, "
                f"elemento id={element.id!r} e {type(element).__name__}."
            )
        weight_per_length = element.material.density * element.section.A * gravity
        force_global = weight_per_length * direction_unit
        local_x, local_y, local_z = element.local_axes()
        loads.append(
            DistributedLoad(
                element.id,
                wx=float(np.dot(force_global, local_x)),
                wy=float(np.dot(force_global, local_y)),
                wz=float(np.dot(force_global, local_z)),
            )
        )
    return tuple(loads)
