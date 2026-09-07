# OpenStruct 3D

Software de engenharia estrutural para analise e dimensionamento de
estruturas metalicas em 3D. Ver `AGENTS_MASTER.md` (sistema
multiagente de desenvolvimento) e `PROGRAM_MASTER.md` (especificacao
completa do programa) para o escopo integral do projeto.

## Estado atual: FOUNDATION + CORE STRUCTURAL MODEL

Esta fase implementa **apenas** o modelo de dominio estrutural:

- `DOF` — os 6 graus de liberdade nodais (UX, UY, UZ, RX, RY, RZ);
- `Node` — no estrutural (id, coordenadas, DOFs);
- `Material` — material elastico-linear (E, G, density, fy, fu, poisson);
- `Section` — secao transversal (A, Iy, Iz, J, Wply/z, Wely/z, dimensions);
- `Element` — contrato abstrato do metodo da rigidez direta;
- `Element3D` — elemento de portico espacial (12 DOFs: axial, flexao
  Y, flexao Z, torcao), com `local_stiffness_matrix()`,
  `transformation_matrix()` e `global_stiffness_matrix()`.

**Fora do escopo desta fase** (fases futuras do PROGRAM_MASTER):
Support, Load, LoadCase, LoadCombination, AnalysisModel, Assembly,
boundary conditions, solver global, resultados, GUI (PySide6), IA,
P-Delta, flambagem, modulos normativos (incluindo NBR 8800) e
dimensionamento.

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
├── __init__.py
└── domain/
    ├── dof.py              # DOF (enum), DOFS_PER_NODE, NODE_DOF_ORDER
    ├── node.py              # Node
    ├── material.py          # Material
    ├── section.py           # Section
    └── elements/
        ├── base.py           # Element (ABC)
        └── frame3d.py        # Element3D

tests/
├── unit/                    # testes unitarios por classe
└── validation/               # comparacao contra solucoes analiticas

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
