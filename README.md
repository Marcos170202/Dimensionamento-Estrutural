# OpenStruct 3D

Software de engenharia estrutural para analise e dimensionamento de
estruturas metalicas em 3D. Ver `AGENTS_MASTER.md` (sistema
multiagente de desenvolvimento) e `PROGRAM_MASTER.md` (especificacao
completa do programa) para o escopo integral do projeto.

## Estado atual: SOLVER V1 ("3D FRAME SOLVER V1")

### Fase FOUNDATION + CORE STRUCTURAL MODEL (modelo de dominio)

- `DOF` — os 6 graus de liberdade nodais (UX, UY, UZ, RX, RY, RZ);
- `Node` — no estrutural (id, coordenadas, DOFs);
- `Material` — material elastico-linear (E, G, density, fy, fu, poisson);
- `Section` — secao transversal (A, Iy, Iz, J, Wply/z, Wely/z, dimensions);
- `Element` — contrato abstrato do metodo da rigidez direta;
- `Element3D` — elemento de portico espacial (12 DOFs: axial, flexao
  Y, flexao Z, torcao), com `local_stiffness_matrix()`,
  `transformation_matrix()` e `global_stiffness_matrix()`.

### Fase SOLVER V1 (montagem, apoios, cargas, resolucao)

- `Support` — restricao de DOF em um no (com presets `fixed`/`pinned`);
- `Load`/`NodalLoad`/`LoadCase`/`LoadCombination` — cargas nodais e
  sua combinacao linear;
- `ElementLoad`/`DistributedLoad` — carga uniformemente distribuida ao
  longo do vao de um `Element3D` (vetor de carga nodal equivalente por
  trabalho virtual, validado contra viga em balanco e simplesmente
  apoiada em VAL-0003);
- `self_weight_loads` — gera automaticamente uma `DistributedLoad` de
  peso proprio por elemento (`density x A x gravity`, projetada nos
  eixos locais; validado em VAL-0004 contra estatica pura e formula
  fechada, incluindo elemento vertical, horizontal e inclinado);
- `AnalysisModel` — container de nos/elementos/apoios com numeracao
  global de DOFs;
- `Assembly` — monta `K_global`/`F_global`;
- `BoundaryConditions` — particiona livre/restrito e detecta
  mecanismo (`ModelInstabilityError`);
- `solve_linear_system` — resolve `K u = F` (SciPy, arquitetura
  trocavel para LU/Cholesky/LDLT/esparso);
- `run_analysis`/`AnalysisResult` — orquestra tudo acima e devolve
  deslocamentos, reacoes e esforcos internos, com uma rede de
  seguranca de equilibrio (`EquilibriumResidualError`) contra
  resultados fisicamente inconsistentes.

**Fora do escopo desta fase** (fases futuras do PROGRAM_MASTER): carga
concentrada fora dos nos, GUI (PySide6), IA, P-Delta, flambagem,
modulos normativos (incluindo NBR 8800) e dimensionamento.

## Convenção de unidades

Sistema consistente **N, mm, MPa** (MPa = N/mm²) em todo o núcleo de
domínio — ver docstrings de `material.py` e `section.py`. A aplicação
formal de um sistema de unidades (conversões, unidades explícitas por
grandeza) é responsabilidade do futuro **UNITS & DATA AGENT**
(AGENTS_MASTER.md seção 12), ainda não implementado.

## Requisitos

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) (recomendado) ou `pip`

## Instalação

```bash
uv venv --python 3.13 .venv
uv pip install -e ".[dev]" --python .venv/bin/python
```

## Exemplo de uso

```python
from openstruct.domain import (
    AnalysisModel, Node, Material, Section, Element3D, Support,
    LoadCase, NodalLoad,
)
from openstruct import run_analysis

steel = Material(name="ASTM A572 Gr. 50", E=200000.0, G=77000.0,
                  density=7.85e-6, fy=345.0, fu=450.0, poisson=0.3)
section = Section(name="W310x21", A=2680.0, Iy=3.79e6, Iz=37.0e6,
                   J=52.8e3, Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3)

model = AnalysisModel()
n1 = Node(1, 0.0, 0.0, 0.0)
n2 = Node(2, 4000.0, 0.0, 0.0)
model.add_node(n1)
model.add_node(n2)
model.add_element(Element3D(1, (n1, n2), steel, section))
model.add_support(Support.fixed(1))  # cantilever engastado no no 1

load = LoadCase("P", (NodalLoad(2, fy=-10_000.0),))  # 10 kN na ponta
result = run_analysis(model, load)

print(result.displacements[2])   # [ux, uy, uz, rx, ry, rz] do no 2
print(result.reactions[1])       # reacao de apoio no no 1
print(result.element_forces[1])  # esforcos internos do elemento 1 (eixos locais)
```

## Testes

```bash
.venv/bin/python -m pytest -v                          # suite completa
.venv/bin/python -m pytest tests/unit -v                # unitarios
.venv/bin/python -m pytest tests/validation -v          # validacao estrutural
.venv/bin/python -m pytest --cov=openstruct --cov-report=term-missing
```

## Estrutura do projeto

```
src/openstruct/
├── __init__.py               # re-exporta AnalysisResult, run_analysis
├── domain/                    # DOMAIN + CORE (dados, sem calculo de matrizes)
│   ├── dof.py                  # DOF (enum), DOFS_PER_NODE, NODE_DOF_ORDER
│   ├── node.py                  # Node
│   ├── material.py              # Material
│   ├── section.py               # Section
│   ├── support.py               # Support
│   ├── loads.py                  # Load (ABC), NodalLoad, LoadCase, LoadCombination
│   ├── model.py                  # AnalysisModel
│   └── elements/
│       ├── base.py                # Element (ABC)
│       └── frame3d.py             # Element3D
├── analysis/                  # ANALYSIS (deriva matrizes/vetores do modelo)
│   ├── assembly.py              # Assembly (K_global, F_global)
│   └── boundary_conditions.py    # BoundaryConditions, ModelInstabilityError
├── solver/                    # SOLVER (algebra linear pura)
│   └── linear.py                # solve_linear_system
└── results/                   # RESULTS (orquestracao + saida)
    └── analysis_result.py       # AnalysisResult, run_analysis, EquilibriumResidualError

tests/
├── unit/                    # testes unitarios por classe
└── validation/               # comparacao contra solucoes analiticas/estatica pura

docs/
├── validation/               # VAL-XXXX.md — registros de validacao de engenharia
└── decisions/                 # ADR-XXX.md — decisoes arquiteturais

.claude/
├── agents/                   # subagentes do Claude Code para este projeto
└── commands/                  # comandos (/validate, /review, /test, /analyze, /release)
```

## Sistema multiagente

Este repositório usa o sistema multiagente descrito em
`AGENTS_MASTER.md`. Nenhuma funcionalidade estrutural é considerada
concluída sem passar por:

```
SOLVER AGENT → TEST AGENT → STRUCTURAL VALIDATION AGENT
             → CODE REVIEW AGENT → ENGINEERING QA AGENT → ORCHESTRATOR
```

Os agentes atualmente definidos em `.claude/agents/` cobrem as fases
já abertas ou em preparação imediata (`orchestrator`, `solver`,
`validation`, `testing`, `code-review`, `engineering-qa`, `numerical`,
`normative`, `modeling`, `gui`, `reporting`, `release`). Os demais
agentes de `AGENTS_MASTER.md` (`architect`, `units-data`,
`postprocessing`, `optimization`, `ai`, `security`) serão adicionados
quando as fases correspondentes forem abertas.

## Próximas fases (não implementadas aqui)

Ver `PROGRAM_MASTER.md` seções 25-34 para a lista completa de marcos
(`3D FRAME SOLVER V1`, `VALIDATED 3D FRAME SOLVER`, `DESKTOP GUI`,
`SECOND ORDER`, `BUCKLING`, `NORMATIVE ENGINE`, `STEEL DESIGN`,
`REPORT ENGINE`, `AI COPILOT`, `OPTIMIZATION`).
