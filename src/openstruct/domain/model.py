"""``AnalysisModel`` — container do modelo estrutural completo.

Fonte: PROGRAM_MASTER.md secao 3 ("CORE ESTRUTURAL", item
``AnalysisModel``). Reune nos, elementos e apoios, e e responsavel
pela numeracao global de graus de liberdade usada por
``openstruct.analysis.Assembly``.

``AnalysisModel`` NAO monta matrizes nem resolve nada — e apenas o
"documento" que descreve a estrutura (dados), consistente com a
separacao DOMAIN/ANALYSIS de PROGRAM_MASTER.md secao 2 (ver
ADR-002).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from .dof import DOF, DOFS_PER_NODE
from .elements.base import Element
from .node import Node
from .support import Support


class AnalysisModel:
    """Container de nos, elementos e apoios, com numeracao global de DOFs.

    A numeracao global e por ORDEM DE INSERCAO dos nos (nao pelo
    ``Node.id``): o no inserido na posicao ``k`` (0-based) ocupa os
    indices globais ``[6k, 6k+6)`` do vetor/matriz global, na ordem
    canonica de DOF (``UX,UY,UZ,RX,RY,RZ``).
    """

    def __init__(self) -> None:
        self._nodes: dict[int, Node] = {}
        self._node_position: dict[int, int] = {}
        self._elements: dict[int, Element] = {}
        self._supports: dict[int, Support] = {}

    # -- nos ---------------------------------------------------------

    def add_node(self, node: Node) -> None:
        if node.id in self._nodes:
            raise ValueError(f"Ja existe um Node com id={node.id!r} no modelo.")
        self._node_position[node.id] = len(self._nodes)
        self._nodes[node.id] = node

    @property
    def nodes(self) -> Mapping[int, Node]:
        return MappingProxyType(self._nodes)

    @property
    def num_dofs(self) -> int:
        """Numero total de graus de liberdade do modelo (``6 * numero de nos``)."""
        return len(self._nodes) * DOFS_PER_NODE

    def dof_index(self, node_id: int, dof: DOF) -> int:
        """Indice global (0-based) do DOF ``dof`` do no ``node_id``."""
        if node_id not in self._node_position:
            raise KeyError(
                f"Node id={node_id!r} nao pertence a este AnalysisModel."
            )
        return self._node_position[node_id] * DOFS_PER_NODE + dof.value

    def node_dof_indices(self, node_id: int) -> list[int]:
        """Os 6 indices globais do no ``node_id``, na ordem canonica de DOF."""
        base = self._node_position.get(node_id)
        if base is None:
            raise KeyError(
                f"Node id={node_id!r} nao pertence a este AnalysisModel."
            )
        start = base * DOFS_PER_NODE
        return list(range(start, start + DOFS_PER_NODE))

    # -- elementos -----------------------------------------------------

    def add_element(self, element: Element) -> None:
        if element.id in self._elements:
            raise ValueError(f"Ja existe um Element com id={element.id!r} no modelo.")
        for node in element.nodes:
            registered = self._nodes.get(node.id)
            if registered is None:
                raise ValueError(
                    f"Element id={element.id!r} referencia Node id={node.id!r}, "
                    "que nao foi adicionado ao modelo (chame add_node() primeiro)."
                )
            if registered is not node:
                raise ValueError(
                    f"Element id={element.id!r} referencia um objeto Node "
                    f"id={node.id!r} diferente do registrado no modelo — "
                    "mesma id, instancias distintas (possivel divergencia de "
                    "coordenadas). Use a instancia devolvida por "
                    "AnalysisModel.nodes ao construir o elemento."
                )
        self._elements[element.id] = element

    @property
    def elements(self) -> Mapping[int, Element]:
        return MappingProxyType(self._elements)

    # -- apoios -----------------------------------------------------

    def add_support(self, support: Support) -> None:
        if support.node_id not in self._nodes:
            raise ValueError(
                f"Support referencia Node id={support.node_id!r}, que nao foi "
                "adicionado ao modelo (chame add_node() primeiro)."
            )
        if support.node_id in self._supports:
            raise ValueError(
                f"Ja existe um Support para Node id={support.node_id!r} — "
                "combine as restricoes em um unico Support em vez de "
                "adicionar mais de um para o mesmo no."
            )
        self._supports[support.node_id] = support

    @property
    def supports(self) -> Mapping[int, Support]:
        return MappingProxyType(self._supports)
