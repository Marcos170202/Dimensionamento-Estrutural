---
description: Roda uma analise estrutural do OpenStruct 3D (equivalente futuro de "openstruct analyze", PROGRAM_MASTER.md secao 23).
---

**Estado atual do projeto (verifique antes de agir):** a fase
FOUNDATION + CORE STRUCTURAL MODEL implementa apenas o modelo de
dominio (`Node`, `Material`, `Section`, `Element`, `Element3D`).
**Nao existe ainda** `AnalysisModel`, `Assembly`, `BoundaryConditions`
nem `Solver` (PROGRAM_MASTER.md secoes 8-12) — ou seja, ainda nao e
possivel "rodar uma analise" no sentido de resolver `K u = F` para um
modelo completo com apoios e cargas.

Se `$ARGUMENTS` pedir uma analise completa:

1. Confirme o estado real do codigo (`Glob`/`Grep` em
   `src/openstruct/`) antes de responder — nunca presuma que Assembly/
   Solver existem so porque estao descritos no PROGRAM_MASTER.
2. Se realmente nao existirem ainda, diga isso explicitamente ao
   usuario e ofereca as alternativas que **ja** funcionam nesta fase:
   - construir `Node`/`Material`/`Section`/`Element3D` diretamente em
     Python e inspecionar `local_stiffness_matrix()`,
     `transformation_matrix()`, `global_stiffness_matrix()`;
   - rodar as validacoes existentes (`/validate`) para conferir que o
     elemento se comporta como esperado.
3. Se Assembly/Solver ja tiverem sido implementados em uma fase
   posterior a esta, siga o fluxo real do codigo (leia
   `src/openstruct/` antes de generalizar) e execute a analise
   pedida, reportando deslocamentos, reacoes e esforcos internos
   reais (nunca inventados).

Nunca afirme que uma analise foi executada sem ter rodado o codigo de
fato (AGENTS_MASTER.md secao 26).
