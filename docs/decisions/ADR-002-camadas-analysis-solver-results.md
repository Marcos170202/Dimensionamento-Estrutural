# ADR-002 — Mapeamento das camadas DOMAIN/ANALYSIS/SOLVER/RESULTS

**Status:** Aceita
**Data:** 2026-09-08
**Agente responsável:** ARCHITECT AGENT (via ORCHESTRATOR, fase SOLVER V1)

## Contexto

PROGRAM_MASTER.md §2 exige separar `DOMAIN, CORE, ANALYSIS, SOLVER,
RESULTS, POSTPROCESSING, NORMATIVE, REPORTS, GUI, AI, IO`, sem
dependência circular. Até a fase anterior (FOUNDATION + CORE
STRUCTURAL MODEL, ADR-001) só existia `domain/` — nenhuma outra
camada tinha código, então não havia decisão a registrar sobre onde
cada nova classe (`Support`, `Load`, `LoadCase`, `LoadCombination`,
`AnalysisModel`, e depois `Assembly`, `BoundaryConditions`, o solver
linear e `AnalysisResult`) deveria morar.

PROGRAM_MASTER.md §3 ("CORE ESTRUTURAL") lista `Support`, `Load`,
`LoadCase`, `LoadCombination`, `AnalysisModel` e `AnalysisResult` no
mesmo grupo de `Node`/`Element`/`Material`/`Section` — não deixa
explícito se `AnalysisModel`/`AnalysisResult` pertencem à camada
DOMAIN ou a outra.

## Decisão

| Camada (PROGRAM_MASTER §2) | Pacote | Conteúdo desta fase |
|---|---|---|
| DOMAIN + CORE | `openstruct.domain` | `DOF`, `Node`, `Material`, `Section`, `Element`/`Element3D`, `Support`, `Load`/`NodalLoad`/`LoadCase`/`LoadCombination`, `AnalysisModel` |
| ANALYSIS | `openstruct.analysis` | `Assembly` (monta `K_global`/`F_global`), `BoundaryConditions` (particiona livre/restrito, detecta mecanismo) |
| SOLVER | `openstruct.solver` | `solve_linear_system` (único ponto de entrada para álgebra linear — trocar para esparso no futuro muda só este módulo) |
| RESULTS | `openstruct.results` | `AnalysisResult` + `run_analysis` (a função que amarra as 4 camadas acima; nenhuma camada inferior conhece as superiores) |

Critério usado: uma classe é **DOMAIN** se ela apenas *descreve* a
estrutura ou a ação sobre ela (dado, sem comportamento de cálculo além
de validação e indexação) — isso inclui `AnalysisModel`, que só
numera DOFs e guarda referências, sem montar nem resolver nada.
Uma classe é **ANALYSIS** se ela *deriva* uma matriz/vetor a partir do
modelo. É **SOLVER** se resolve álgebra linear pura, sem saber o que
os números representam fisicamente (`solve_linear_system` não importa
nada de `domain`). É **RESULTS** a camada que organiza a saída e
orquestra as demais.

Direção de dependência (sem ciclos, confirmado por import real, não
apenas por convenção):

```
results -> analysis -> domain
results -> solver
results -> domain
analysis -> domain
solver   (não depende de domain nem de analysis)
```

## Alternativas consideradas

- **Colocar `Assembly`/`BoundaryConditions` dentro de `domain/`**:
  mais simples, mas mistura "dado" com "comportamento de cálculo
  sobre múltiplos objetos" — dificultaria isolar o NUMERICAL METHODS
  AGENT (que deve poder auditar só `analysis/`+`solver/` sem varrer
  `domain/`). Rejeitada.
- **Um único módulo `engine.py` com tudo (Assembly + BC + Solver +
  Result)**: rejeitada pela mesma razão do ADR-001 — cada
  responsabilidade testável e substituível isoladamente (trocar o
  solver denso por esparso não deveria arriscar `Assembly`).

## Consequências

- Uma futura carga distribuída/peso próprio (fora desta fase) muda
  apenas `domain/loads.py` (novo tipo de `Load`) — `Assembly` não
  precisa saber que esse tipo existe, pois só chama
  `load_source.apply_to(...)`.
- Um futuro solver esparso muda apenas `solver/linear.py`.
- `POSTPROCESSING`, `NORMATIVE`, `REPORTS`, `GUI`, `AI`, `IO` (PROGRAM_MASTER
  §2) continuam sem nenhum código — permanecem reservados para quando
  as fases correspondentes abrirem, evitando pacotes vazios "só para
  bater com o diagrama" (mesmo princípio do ADR-001).
