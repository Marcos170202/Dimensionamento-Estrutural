"""OpenStruct 3D — nucleo de analise estrutural 3D.

Ver AGENTS_MASTER.md e PROGRAM_MASTER.md na raiz do repositorio para a
especificacao completa.

Fases ja implementadas:

- FOUNDATION + CORE STRUCTURAL MODEL: DOF, Node, Material, Section,
  Element (base), Element3D.
- SOLVER V1 ("3D FRAME SOLVER V1", PROGRAM_MASTER secao 25): Support,
  Load/NodalLoad/LoadCase/LoadCombination (incluindo
  DistributedLoad/PointLoad/self_weight_loads), AnalysisModel,
  Assembly, BoundaryConditions, solver linear e :func:`run_analysis`.
- NORMATIVE ENGINE (PROGRAM_MASTER secao 30, inicio): modulo NBR 8800
  em ``openstruct.normative.nbr8800`` — verificacao de barras
  tracionadas (5.2). Arquitetura de plugin, deliberadamente FORA do
  namespace `openstruct` de topo (ver docstring de
  ``openstruct.normative``) — o nucleo de analise permanece agnostico
  de norma.

GUI, IA, P-Delta, flambagem e o restante do dimensionamento de
elementos metalicos (compressao, flexao, cisalhamento, combinacao de
esforcos) permanecem fases futuras — ver docs/decisions/ADR-002 e
docs/normative/NBR8800-RULES.md para o escopo normativo exato ja
coberto.
"""

from .results import AnalysisResult, run_analysis

__version__ = "0.3.0"

__all__ = ["AnalysisResult", "run_analysis"]
