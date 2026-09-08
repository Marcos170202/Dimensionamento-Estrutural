"""Montagem da matriz de rigidez e do vetor de forcas globais.

Fonte: PROGRAM_MASTER.md secao 8 ("ASSEMBLY"): "Criar montagem da
matriz global. K_global e vetor F_global."

``Assembly`` nao contem nenhuma logica de elemento finito propria —
delega inteiramente a ``element.global_stiffness_matrix()``
(``domain/elements``) e a ``load_source.apply_to()``
(``domain/loads``). O unico trabalho desta classe e a indexacao:
descobrir, para cada elemento/carga, quais linhas/colunas do sistema
global elas afetam, usando ``AnalysisModel.dof_index``.
"""

from __future__ import annotations

import numpy as np

from ..domain.dof import NODE_DOF_ORDER
from ..domain.elements.base import Element
from ..domain.loads import LoadSource
from ..domain.model import AnalysisModel


class Assembly:
    """Monta ``K_global`` e ``F_global`` a partir de um :class:`AnalysisModel`."""

    def __init__(self, model: AnalysisModel) -> None:
        self.model = model

    def global_stiffness_matrix(self) -> np.ndarray:
        """``K_global``, array ``(model.num_dofs, model.num_dofs)``, simetrica."""
        n = self.model.num_dofs
        k_global = np.zeros((n, n))
        for element in self.model.elements.values():
            idx = self.element_dof_indices(element)
            k_global[np.ix_(idx, idx)] += element.global_stiffness_matrix()
        return k_global

    def global_load_vector(self, load_source: LoadSource) -> np.ndarray:
        """``F_global``, array ``(model.num_dofs,)``, a partir de um LoadCase/LoadCombination."""
        f_global = np.zeros(self.model.num_dofs)
        load_source.apply_to(f_global, self.model.dof_index)
        return f_global

    def element_dof_indices(self, element: Element) -> list[int]:
        """Indices globais dos DOFs do elemento, na mesma ordem de ``element.nodes``.

        Generico para qualquer ``Element`` (nao apenas ``Element3D``):
        cada no contribui com seus 6 DOFs na ordem canonica
        (``NODE_DOF_ORDER``), na ordem em que os nos aparecem em
        ``element.nodes`` — que e exatamente a ordem assumida por
        ``element.local_stiffness_matrix()``/``transformation_matrix()``.
        """
        return [
            self.model.dof_index(node.id, dof)
            for node in element.nodes
            for dof in NODE_DOF_ORDER
        ]
