"""Elemento estrutural — classe base abstrata.

Fonte: PROGRAM_MASTER.md secao 3 ("CORE ESTRUTURAL", item ``Element``)
e secao 7 ("ELEMENTO 3D"), que define o contrato
``local_stiffness_matrix()`` / ``transformation_matrix()`` /
``global_stiffness_matrix()``.

``Element`` e generico o bastante para qualquer elemento linear do
metodo da rigidez direta (2+ nos, material, secao). A implementacao
concreta para porticos espaciais e ``Element3D``
(``elements/frame3d.py``) — decisao de arquitetura registrada em
``docs/decisions/ADR-001-...md``: separar o contrato comum (base) do
elemento de portico 3D (concreto) para permitir, em fases futuras,
outros tipos de elemento (trelica, casca, etc.) sem reescrever a
montagem generica de ``global_stiffness_matrix()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..dof import NODE_DOF_ORDER, DofIndexer
from ..material import Material
from ..node import Node
from ..section import Section


class Element(ABC):
    """Contrato comum a qualquer elemento do metodo da rigidez direta.

    Parametros
    ----------
    id:
        Identificador inteiro nao-negativo, unico dentro do modelo.
    nodes:
        Nos conectados pelo elemento, em ordem (a ordem define a
        orientacao do sistema de eixos locais nas subclasses). Minimo
        de 2 nos, sem repeticao de ``Node.id``.
    material:
        Material do elemento.
    section:
        Secao transversal do elemento.
    """

    def __init__(
        self,
        id: int,
        nodes: tuple[Node, ...],
        material: Material,
        section: Section,
    ) -> None:
        if not isinstance(id, int) or isinstance(id, bool):
            raise TypeError(f"Element.id deve ser int, recebido {type(id).__name__}.")
        if id < 0:
            raise ValueError(f"Element.id deve ser nao-negativo, recebido {id!r}.")

        nodes = tuple(nodes)
        if len(nodes) < 2:
            raise ValueError(
                f"Element requer no minimo 2 nos, recebido {len(nodes)}."
            )
        if not all(isinstance(n, Node) for n in nodes):
            raise TypeError("Element.nodes deve conter apenas instancias de Node.")
        node_ids = [n.id for n in nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError(
                f"Element.nodes contem Node.id duplicado: {node_ids!r}."
            )
        if not isinstance(material, Material):
            raise TypeError("Element.material deve ser uma instancia de Material.")
        if not isinstance(section, Section):
            raise TypeError("Element.section deve ser uma instancia de Section.")

        self._id = id
        self._nodes = nodes
        self._material = material
        self._section = section

    @property
    def id(self) -> int:
        return self._id

    @property
    def nodes(self) -> tuple[Node, ...]:
        return self._nodes

    @property
    def material(self) -> Material:
        return self._material

    @property
    def section(self) -> Section:
        return self._section

    @property
    @abstractmethod
    def num_dofs(self) -> int:
        """Numero total de graus de liberdade locais do elemento."""
        raise NotImplementedError  # pragma: no cover — corpo de metodo abstrato, nunca executado

    @abstractmethod
    def local_stiffness_matrix(self) -> np.ndarray:
        """Matriz de rigidez no sistema de eixos locais do elemento.

        Retorna array ``(num_dofs, num_dofs)``, simetrica.
        """
        raise NotImplementedError  # pragma: no cover — corpo de metodo abstrato, nunca executado

    @abstractmethod
    def transformation_matrix(self) -> np.ndarray:
        """Matriz de transformacao local <- global (``u_local = T @ u_global``).

        Retorna array ``(num_dofs, num_dofs)``, ortogonal
        (``T @ T.T == identidade``).
        """
        raise NotImplementedError  # pragma: no cover — corpo de metodo abstrato, nunca executado

    def global_stiffness_matrix(self) -> np.ndarray:
        """Matriz de rigidez no sistema de eixos globais.

        Implementacao generica e comum a qualquer elemento linear:
        transformacao congruente ``K_global = T^T @ K_local @ T``.
        Subclasses nao precisam (nem devem) sobrescrever este metodo —
        apenas ``local_stiffness_matrix()`` e ``transformation_matrix()``.
        """
        t = self.transformation_matrix()
        k_local = self.local_stiffness_matrix()
        result: np.ndarray = t.T @ k_local @ t
        return result

    def __repr__(self) -> str:
        node_ids = tuple(n.id for n in self._nodes)
        return f"{type(self).__name__}(id={self._id!r}, nodes={node_ids!r})"


def element_dof_indices(element: Element, dof_index: DofIndexer) -> list[int]:
    """Indices globais dos DOFs de ``element``, na mesma ordem de ``element.nodes``.

    Funcao livre (nao metodo) porque e usada tanto por
    ``analysis.Assembly`` quanto por ``domain.loads.ElementLoad`` — a
    camada ``domain`` nao pode depender de ``analysis`` (ver ADR-002),
    entao esta unica implementacao mora aqui e ambas as camadas a
    importam, em vez de cada uma reimplementar o mesmo loop (CODE
    REVIEW AGENT: duplicacao encontrada entre ``Assembly.element_dof_indices``
    e ``ElementLoad.apply_to`` na fase de carga distribuida).
    """
    return [
        dof_index(node.id, dof) for node in element.nodes for dof in NODE_DOF_ORDER
    ]
