"""OpenStruct 3D — nucleo de analise estrutural 3D.

Ver AGENTS_MASTER.md e PROGRAM_MASTER.md na raiz do repositorio para a
especificacao completa.

Fases ja implementadas:

- FOUNDATION + CORE STRUCTURAL MODEL: DOF, Node, Material, Section,
  Element (base), Element3D.
- SOLVER V1 ("3D FRAME SOLVER V1", PROGRAM_MASTER secao 25): Support,
  Load/NodalLoad/LoadCase/LoadCombination, AnalysisModel, Assembly,
  BoundaryConditions, solver linear e :func:`run_analysis`.

GUI, IA, P-Delta, flambagem, modulos normativos e cargas
distribuidas/peso proprio permanecem fases futuras — ver
docs/decisions/ADR-002 e o relatorio de fase para o escopo exato.
"""

from .results import AnalysisResult, run_analysis

__version__ = "0.2.0"

__all__ = ["AnalysisResult", "run_analysis"]
