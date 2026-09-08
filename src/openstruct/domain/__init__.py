"""Modelo de dominio estrutural (PROGRAM_MASTER.md secao 3, "CORE ESTRUTURAL").

Fase atual implementa: :class:`DOF`, :class:`Node`, :class:`Material`,
:class:`Section` e a hierarquia de elementos (:mod:`.elements`).
"""

from .dof import DOF, DOFS_PER_NODE, NODE_DOF_ORDER
from .elements.base import Element
from .elements.frame3d import Element3D
from .material import Material
from .node import Node
from .section import Section

__all__ = [
    "DOF",
    "DOFS_PER_NODE",
    "NODE_DOF_ORDER",
    "Element",
    "Element3D",
    "Material",
    "Node",
    "Section",
]
