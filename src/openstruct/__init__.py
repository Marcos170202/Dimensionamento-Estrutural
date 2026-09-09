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
  tracionadas (5.2) e comprimidas (5.3, flambagem por flexao E por
  torcao para secoes com dupla simetria ou simetricas em relacao a um
  ponto — ver limitacao de seguranca em ``compression.py`` sobre
  flexo-torcao em secoes monossimetricas/assimetricas, ainda nao
  implementada), a limitacao RECOMENDADA (nao obrigatoria) do indice
  de esbeltez (5.2.8.1/5.3.7.1) e a forca cortante resistente de
  calculo de secoes I/H/U fletidas em relacao ao eixo perpendicular a
  alma (5.4.1.3/5.4.3.1 — ver ``shear.py`` para o restante de 5.4,
  ainda fora do escopo, em especial 5.4.2/flexao que depende dos
  Anexos D/E). Arquitetura de plugin, deliberadamente FORA do
  namespace `openstruct` de topo (ver docstring de
  ``openstruct.normative``) — o nucleo de analise permanece agnostico
  de norma.

GUI, IA, P-Delta, flambagem e o restante do dimensionamento de
elementos metalicos (flexao resistente de calculo, combinacao de
esforcos, ligacoes) permanecem fases futuras — ver docs/decisions/ADR-002
e docs/normative/NBR8800-RULES.md para o escopo normativo exato ja
coberto.
"""

from .results import AnalysisResult, run_analysis

__version__ = "0.7.0"

__all__ = ["AnalysisResult", "run_analysis"]
