# ADR-001 — Estrutura de pacotes e separação Element / Element3D

**Status:** Aceita
**Data:** 2026-09-07
**Agente responsável:** ARCHITECT AGENT (via ORCHESTRATOR, fase FOUNDATION + CORE STRUCTURAL MODEL)

## Contexto

PROGRAM_MASTER.md §2 exige separar as camadas `DOMAIN, CORE, ANALYSIS,
SOLVER, RESULTS, POSTPROCESSING, NORMATIVE, REPORTS, GUI, AI, IO` sem
dependência circular. PROGRAM_MASTER §3 lista `Node, Element, Material,
Section, Support, Load, LoadCase, LoadCombination, AnalysisModel,
AnalysisResult` como o "CORE ESTRUTURAL". PROGRAM_MASTER §7 descreve um
elemento concreto ("ELEMENTO 3D", pórtico espacial, 12 DOFs) mas cita
apenas "Element" como item genérico em §3, sem detalhar se deveria
existir uma classe abstrata separada.

O escopo desta fase (instrução explícita do usuário) é restrito a:
estrutura do projeto, configuração Python, `Node`, `DOF`, `Material`,
`Section`, `Element` base e `Element3D` — sem `Support`/`Load`/
`Assembly`/`Solver`, que ficam para fases seguintes.

## Decisão

1. **Camada de domínio isolada em `src/openstruct/domain/`**, sem
   dependência de nenhuma outra camada futura (`core/analysis/solver/…`
   ainda não existem — serão criadas quando as fases correspondentes
   chegarem, evitando módulos vazios "só para bater com o diagrama").
2. **`Element` como classe abstrata (ABC)** com o contrato comum
   (`id`, `nodes`, `material`, `section`, `num_dofs`,
   `local_stiffness_matrix()`, `transformation_matrix()`), e
   `global_stiffness_matrix()` **implementado uma única vez na base**
   como a transformação congruente genérica `T.T @ K_local @ T`
   (válida para qualquer elemento linear do método da rigidez direta,
   não apenas para pórtico espacial).
3. **`Element3D` como única subclasse concreta desta fase**,
   implementando o elemento de pórtico espacial de Euler-Bernoulli
   (axial + flexão Y + flexão Z + torção) exigido por PROGRAM_MASTER §7.

## Alternativas consideradas

- **Uma única classe `Element` já concreta para pórtico 3D** (sem
  hierarquia): mais simples agora, mas contradiz o princípio de
  extensibilidade do ARCHITECT AGENT (AGENTS_MASTER.md §5) — um futuro
  elemento de treliça (sem rigidez à flexão) ou elemento de casca
  exigiria duplicar `global_stiffness_matrix()` ou quebrar a interface
  existente. Rejeitada.
- **`global_stiffness_matrix()` abstrato, reimplementado em cada
  subclasse**: permitido pelo contrato do PROGRAM_MASTER, mas é código
  idêntico (`T.T @ K @ T`) em toda subclasse futura — viola DRY sem
  ganho, e o NUMERICAL METHODS AGENT teria de auditar N cópias em vez
  de uma. Rejeitada em favor da implementação única na base.

## Consequências

- Fases futuras (`Support`, `Load`, `Assembly`, `Solver`) podem
  depender de `domain.Element`/`domain.Node` sem que o inverso ocorra
  — mantém a ausência de dependência circular exigida por
  PROGRAM_MASTER §2.
- Um novo tipo de elemento (ex.: treliça 3D, 2 nós, 6 DOFs) se encaixa
  implementando apenas `local_stiffness_matrix()` e
  `transformation_matrix()`, sem tocar em `global_stiffness_matrix()`.
- `Element3D` fixa a convenção de 2 nós; um elemento com mais nós
  (ex.: elemento de casca) exigirá revisão desta ADR quando a fase
  correspondente chegar — registrado aqui para não ser esquecido.
