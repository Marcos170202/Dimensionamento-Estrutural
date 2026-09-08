"""Modelo de dominio estrutural (PROGRAM_MASTER.md secao 3, "CORE ESTRUTURAL").

Fase FOUNDATION + CORE STRUCTURAL MODEL implementou: :class:`DOF`,
:class:`Node`, :class:`Material`, :class:`Section` e a hierarquia de
elementos (:mod:`.elements`). Fase SOLVER V1 acrescenta:
:class:`Support`, :class:`~openstruct.domain.loads.Load` (e
:class:`~openstruct.domain.loads.NodalLoad`,
:class:`~openstruct.domain.loads.LoadCase`,
:class:`~openstruct.domain.loads.LoadCombination`) e
:class:`AnalysisModel`.
"""

from .dof import DOF, DOFS_PER_NODE, NODE_DOF_ORDER
from .elements.base import Element
from .elements.frame3d import Element3D
from .loads import (
    DistributedLoad,
    ElementLoad,
    Load,
    LoadCase,
    LoadCombination,
    NodalLoad,
    PointLoad,
    self_weight_loads,
)
from .material import Material
from .model import AnalysisModel
from .node import Node
from .section import Section
from .support import Support

__all__ = [
    "DOF",
    "DOFS_PER_NODE",
    "NODE_DOF_ORDER",
    "AnalysisModel",
    "DistributedLoad",
    "Element",
    "Element3D",
    "ElementLoad",
    "Load",
    "LoadCase",
    "LoadCombination",
    "Material",
    "Node",
    "NodalLoad",
    "PointLoad",
    "Section",
    "Support",
    "self_weight_loads",
]
