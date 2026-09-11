# OpenStruct 3D

Software de engenharia estrutural para analise e dimensionamento de
estruturas metalicas em 3D. Ver `AGENTS_MASTER.md` (sistema
multiagente de desenvolvimento) e `PROGRAM_MASTER.md` (especificacao
completa do programa) para o escopo integral do projeto.

## Estado atual: SOLVER V1 ("3D FRAME SOLVER V1") + NORMATIVE ENGINE + GUI DESKTOP V1

### Fase FOUNDATION + CORE STRUCTURAL MODEL (modelo de dominio)

- `DOF` — os 6 graus de liberdade nodais (UX, UY, UZ, RX, RY, RZ);
- `Node` — no estrutural (id, coordenadas, DOFs);
- `Material` — material elastico-linear (E, G, density, fy, fu, poisson);
- `Section` — secao transversal (A, Iy, Iz, J, Wply/z, Wely/z, Cw
  opcional, dimensions), com raio de giracao (`radius_of_gyration_y/z`)
  computado — preparado para flambagem por torcao/flexo-torcao e
  limitacao de esbeltez da NBR 8800 (ainda nao implementadas, ver
  `docs/normative/NBR8800-RULES.md`);
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
- `PointLoad` — forca concentrada em posicao ARBITRARIA ao longo do
  vao de um `Element3D` (nao apenas nos nos, diferenca para
  `NodalLoad`), com vetor de carga nodal equivalente por trabalho
  virtual (funcoes de forma de Hermite avaliadas no ponto de
  aplicacao); validado em VAL-0005 contra estatica pura, formula
  fechada de deflexao e os casos limite (`position=0`/`=comprimento`
  reduzem exatamente a uma `NodalLoad`). **Nao suporta momento
  concentrado fora dos nos** nesta fase;
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

**Fora do escopo desta fase** (fases futuras do PROGRAM_MASTER):
momento concentrado fora dos nos, GUI (PySide6), IA, P-Delta e
flambagem.

### Fase NORMATIVE ENGINE (início — NBR 8800)

Arquitetura de plugin (`openstruct.normative.nbr8800`), deliberadamente
fora do núcleo de análise (`domain`/`analysis`/`solver`/`results`
permanecem agnósticos de norma — ver `.claude/agents/normative.md`).
Rastreabilidade completa de cada regra em
`docs/normative/NBR8800-RULES.md`.

- `check_tension_member` — verificação de barras prismáticas
  tracionadas (NBR 8800:2024, 5.2.1.2/5.2.2): força axial resistente
  de cálculo por escoamento da seção bruta e por ruptura da seção
  líquida, taxa de utilização e estado-limite governante; validado em
  VAL-0006 por cálculo manual independente das fórmulas lidas
  diretamente do texto normativo;
- `check_compression_member` — verificação de barras prismáticas
  comprimidas (NBR 8800:2024, 5.3.1/5.3.2/5.3.3/5.3.5.1): força axial
  resistente de cálculo (`χ·Aef·fy/γa1`), com o fator de redução χ
  (curva de flambagem) e a força axial de flambagem elástica por
  flexão (`Nex`/`Ney`) **e por torção** (`Nez`, via
  `torsional_buckling_force`/`polar_radius_of_gyration`) em torno de
  cada eixo principal, para seções com dupla simetria ou simétricas em
  relação a um ponto; validado em VAL-0007/VAL-0008 (o Caso 2 de
  VAL-0008 demonstra numericamente uma redução de ~40% em `Nc,Rd` ao
  incluir `Nez` num cenário onde a torção governa). **⚠️ Limitação de
  segurança remanescente**: seções monossimétricas (perfis U/C, T) ou
  assimétricas (cantoneiras de abas desiguais) precisam da força de
  flambagem por flexo-torção (`Neyz`, não implementada) em vez de
  `min(Nex, Ney, Nez)` — ver RULE-ID `NBR8800-COMP-005` em
  `docs/normative/NBR8800-RULES.md` antes de usar nessas seções;
- `steel_resistance_factors` — coeficientes de ponderação da
  resistência do aço estrutural (γa1/γa2) por classe de combinação de
  ações (NBR 8800:2024, 4.9.2, Tabela 3);
- `check_tension_slenderness`/`check_compression_slenderness` —
  limitação RECOMENDADA (não estado-limite último obrigatório) do
  índice de esbeltez de barras individuais tracionadas (`ℓ/r ≤ 300`,
  5.2.8.1) e comprimidas (`ℓ/r ≤ 200`, 5.3.7.1); validado em VAL-0009,
  incluindo um caso onde a mesma barra passa na recomendação de tração
  mas não na de compressão (os dois limites são independentes);
- `check_shear_major_axis` — força cortante resistente de cálculo de
  seções I, H e U fletidas em relação ao eixo perpendicular à alma
  (NBR 8800:2024, 5.4.1.3/5.4.3.1): curva em 3 trechos (plastificação
  da alma / flambagem inelástica / flambagem elástica por
  cisalhamento), com o coeficiente `kv` considerando enrijecedores
  transversais opcionais; validado em VAL-0010 por cálculo manual
  independente dos três trechos;
- `check_lateral_torsional_buckling` — flambagem lateral com torção
  (FLT) isolada de seções I, H com dois eixos de simetria e seções U
  não sujeitas a momento de torção, fletidas em relação ao eixo de
  maior momento de inércia (NBR 8800:2024, 5.4.1.3/Anexo D, D.2.8-a):
  curva em 3 trechos (plastificação / escoamento com tensão residual /
  flambagem elástica), com o fator de modificação `Cb` (caso geral,
  5.4.2.3-a) e `Cw` calculável para seções I; validado em VAL-0011;
- `check_flexural_resistance_major_axis` — momento fletor resistente
  de cálculo COMPLETO (`Mrd = min(Mrd_FLT, Mrd_FLM, Mrd_FLA)`, com o
  limite de 5.4.2.2) para o mesmo tipo de seção/eixo acima, incluindo
  agora flambagem local da mesa comprimida (FLM, perfis laminados e
  soldados com o coeficiente `kc`) e da alma (FLA); valida a
  precondição de aplicabilidade do Anexo D (D.1.2 — recusa vigas de
  alma esbelta com `ValueError`); validado em VAL-0012. **Fecha a
  limitação de segurança antes registrada em `NBR8800-FLEX-004`** para
  este tipo de seção/eixo — use esta função (não
  `check_lateral_torsional_buckling` isoladamente) para o `Mrd`
  completo de 5.4.2.1;
- `check_axial_and_bending_interaction` — interação entre força axial
  (tração ou compressão, a que for aplicável) e momento fletor biaxial
  para barras SEM torção (NBR 8800:2024, 5.5.1.2): as duas equações de
  interação (conforme `Nsd/Nrd` maior/igual ou menor que 0,2); validado
  em VAL-0013. Força cortante em um único eixo (5.5.1.3) não precisa
  de fórmula adicional — remete diretamente a `check_shear_major_axis`
  (5.4.3).

**Fora do escopo desta fase**: cálculo do coeficiente de redução da
área líquida em tração (`Ct`, depende de modelagem de furos/soldas/
parafusos ainda não implementada), chapas ligadas por pino, barras
rosqueadas, requisito de esbeltez para barras COMPOSTAS (apenas barras
individuais estão cobertas), área efetiva reduzida por flambagem local
em compressão, flambagem por flexo-torção em seções
monossimétricas/assimétricas, cantoneiras simples, barras compostas,
vigas de alma esbelta (Anexo E — apenas detectado e recusado, não
calculado), demais linhas da Tabela D.1 do Anexo D (seções
monossimétricas, tubulares/caixão, T, cantoneiras duplas, sólidas, e
flexão no eixo de menor momento de inércia), força cortante resistente
para seções tubulares/caixão/T/cantoneiras duplas/I-H-U em torno do
eixo fraco/tubulares circulares (5.4.3.2 a 5.4.3.6), seções tubulares
submetidas a momento de torção combinado com força axial/momentos
fletores/força cortante (5.5.2, inclui `Trd` de torção pura — nunca
implementado), e ligações — ver `docs/normative/NBR8800-RULES.md` para
a lista completa do que foi conscientemente adiado.

### Fase GUI DESKTOP V1

Aplicativo desktop `openstruct.gui` (PySide6), decidido explicitamente
pelo usuário como **sem viewport 3D** nesta fase — ver
`docs/decisions/ADR-003-gui-arquitetura.md`. Camada fina sobre
`domain`/`results`/`normative`: nenhuma fórmula de engenharia é
duplicada na GUI, cada botão chama diretamente a função já validada
correspondente.

- Aba **"Modelo e Análise"** — tabelas editáveis de nós, materiais,
  seções, elementos, apoios e cargas nodais (com opção de incluir peso
  próprio automaticamente), botão "Rodar Análise" que chama
  `run_analysis` e mostra deslocamentos/reações/esforços internos;
- Aba **"Verificações NBR 8800"** — um formulário por verificação já
  implementada (tração, compressão, cisalhamento, flexão completa
  FLT+FLM+FLA, combinação N+M biaxial), mostrando `is_ok`/utilização;
- Extra opcional: `pip install -e ".[gui]"` (PySide6 não é dependência
  obrigatória do núcleo);
- Empacotável como executável desktop via PyInstaller (`pip install -e
  ".[build]"`, ver `docs/build/EMPACOTAMENTO.md`) — **⚠️ o `.exe`
  Windows só pode ser gerado rodando o PyInstaller em uma máquina
  Windows** (sem cross-compilation; testado nesta fase gerando um
  binário Linux equivalente);
- Testes em modo `offscreen` (`tests/gui/`, sem exigir display real —
  mesmo mecanismo usado pelo CI).

**Fora do escopo desta fase**: viewport 3D (PyVista/VTK), edição
visual do modelo (arrastar nós, desenhar elementos), geração de
relatórios a partir da GUI, undo/redo, salvar/carregar modelo em
arquivo.

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

# opcional: GUI desktop (PySide6) e empacotamento (PyInstaller)
uv pip install -e ".[gui,build]" --python .venv/bin/python
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
.venv/bin/python -m pytest tests/gui -v                 # GUI (offscreen, requer extra "gui")
.venv/bin/python -m pytest --cov=openstruct --cov-report=term-missing
```

Os testes da GUI (`tests/gui/`) rodam em modo `offscreen`
(`QT_QPA_PLATFORM=offscreen`), sem exigir um display real — o mesmo
mecanismo usado no CI. São pulados automaticamente
(`pytest.importorskip`) se o extra `gui` não estiver instalado.

## Executando a GUI desktop

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m openstruct.gui   # modo offscreen (sandbox/CI)
.venv/bin/python -m openstruct.gui                              # modo normal (com display)
# ou, apos `pip install -e ".[gui]"`:
.venv/bin/openstruct3d-gui
```

### 📥 Baixar o `.exe` (Windows) — sem instalar Python

O executável Windows é gerado automaticamente a cada atualização de
`main` (CI, `windows-latest`) e publicado sempre no mesmo link:

👉 **https://github.com/Marcos170202/dimensionamento-estrutural/releases/tag/openstruct3d-gui-latest**

Baixe `openstruct3d-gui.exe` e execute — nada mais a instalar. Volte a
esse mesmo link depois de cada atualização do projeto para pegar a
versão mais recente (o Release é substituído automaticamente, nunca
muda de URL). Detalhes do mecanismo em `docs/build/EMPACOTAMENTO.md`.

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
│   ├── loads.py                  # Load/ElementLoad (ABC), NodalLoad, DistributedLoad,
│   │                                PointLoad, LoadCase, LoadCombination, self_weight_loads
│   ├── model.py                  # AnalysisModel
│   └── elements/
│       ├── base.py                # Element (ABC)
│       └── frame3d.py             # Element3D
├── analysis/                  # ANALYSIS (deriva matrizes/vetores do modelo)
│   ├── assembly.py              # Assembly (K_global, F_global)
│   └── boundary_conditions.py    # BoundaryConditions, ModelInstabilityError
├── solver/                    # SOLVER (algebra linear pura)
│   └── linear.py                # solve_linear_system
├── results/                   # RESULTS (orquestracao + saida)
│   └── analysis_result.py       # AnalysisResult, run_analysis, EquilibriumResidualError
├── normative/                 # NORMATIVE (plugin architecture, agnostico do nucleo)
│   └── nbr8800/                  # ABNT NBR 8800:2024
│       ├── resistance_factors.py   # LoadCombinationClass, SteelResistanceFactors (Tabela 3)
│       ├── tension.py               # check_tension_member (5.2 — barras tracionadas)
│       ├── compression.py           # check_compression_member (5.3 — barras comprimidas)
│       ├── slenderness.py           # esbeltez recomendada (5.2.8.1/5.3.7.1)
│       ├── shear.py                 # check_shear_major_axis (5.4.1.3/5.4.3.1 — cisalhamento)
│       ├── flexure.py               # check_flexural_resistance_major_axis (5.4.1.3/5.4.2/Anexo D — FLT+FLM+FLA)
│       └── combined_forces.py       # check_axial_and_bending_interaction (5.5.1.2 — N+M biaxial)
└── gui/                       # GUI DESKTOP (PySide6, extra opcional "gui")
    ├── widgets.py               # EditableTable (tabela editavel generica)
    ├── model_tab.py             # ModelTab (modelo/analise)
    ├── checks_tab.py            # ChecksTab (verificacoes NBR 8800)
    ├── main_window.py           # MainWindow
    ├── app.py                   # main(), ponto de entrada
    └── __main__.py              # `python -m openstruct.gui`

tests/
├── unit/                    # testes unitarios por classe
├── validation/               # comparacao contra solucoes analiticas/estatica pura/norma
└── gui/                      # testes da GUI (offscreen, requer extra "gui")

docs/
├── validation/               # VAL-XXXX.md — registros de validacao de engenharia
├── normative/                 # NBR8800-RULES.md — rastreabilidade RULE-ID de cada regra
├── decisions/                 # ADR-XXX.md — decisoes arquiteturais
└── build/                     # EMPACOTAMENTO.md — geracao do executavel desktop

packaging/
├── openstruct3d-gui.spec     # spec do PyInstaller (executavel onefile)
└── entrypoint.py              # ponto de entrada usado so pelo PyInstaller

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
`REPORT ENGINE`, `AI COPILOT`, `OPTIMIZATION`). `DESKTOP GUI` teve sua
primeira fase (sem viewport 3D) implementada — viewport 3D
(PyVista/VTK), edição visual do modelo e geração de relatórios pela
GUI permanecem futuros.
