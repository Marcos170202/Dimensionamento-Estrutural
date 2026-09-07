# ============================================================
# OPENSTRUCT 3D
# MASTER PROGRAM SPECIFICATION
# ============================================================

## 1. OBJETIVO

Construir um software desktop para análise estrutural 3D, inicialmente
focado em estruturas metálicas.

O programa deve ser:

- offline-first;
- open source;
- modular;
- extensível;
- multiplataforma quando possível;
- inicialmente otimizado para Windows;
- preparado para gerar .EXE.

Tecnologia principal:

Python 3.13+

GUI:

PySide6

Computação:

NumPy
SciPy

Testes:

pytest

Visualização:

PyVista/VTK

Banco:

SQLite

============================================================
2. ARQUITETURA
============================================================

Separar:

DOMAIN
CORE
ANALYSIS
SOLVER
RESULTS
POSTPROCESSING
NORMATIVE
REPORTS
GUI
AI
IO

Nenhum desses módulos deve possuir dependência circular.

============================================================
3. CORE ESTRUTURAL
============================================================

Implementar:

Node
Element
Material
Section
Support
Load
LoadCase
LoadCombination
AnalysisModel
AnalysisResult

============================================================
4. NÓ
============================================================

Node:

id
x
y
z

DOFs:

UX
UY
UZ
RX
RY
RZ

============================================================
5. MATERIAL
============================================================

Material deve possuir inicialmente:

name
E
G
density
fy
fu
poisson

Preparar para:

elastic
plastic
temperature-dependent

============================================================
6. SECTION
============================================================

Section deve possuir:

name
A
Iy
Iz
J
Wply
Wplz
Wely
Welz
dimensions

Preparar para biblioteca futura de perfis.

============================================================
7. ELEMENTO 3D
============================================================

Implementar elemento de pórtico espacial.

12 DOFs.

Deve considerar:

axial
flexão Y
flexão Z
torção

Criar:

local_stiffness_matrix()
transformation_matrix()
global_stiffness_matrix()

============================================================
8. ASSEMBLY
============================================================

Criar montagem da matriz global.

K_global

e vetor:

F_global

============================================================
9. BOUNDARY CONDITIONS
============================================================

Implementar restrições:

UX
UY
UZ
RX
RY
RZ

Detectar modelos instáveis.

============================================================
10. LOADS
============================================================

Implementar:

nodal loads
point loads
distributed loads
self weight

============================================================
11. SOLVER
============================================================

Resolver:

K u = F

Utilizar SciPy.

Preparar arquitetura para:

LU
Cholesky
LDLT
Sparse solvers

============================================================
12. RESULTS
============================================================

Resultados:

displacements
reactions
element_forces

============================================================
13. SECOND ORDER
============================================================

Depois da validação linear:

P-Delta

com:

convergence tolerance
maximum iterations
convergence report

============================================================
14. BUCKLING
============================================================

Criar posteriormente:

eigenvalue analysis

para:

K φ = λ KG φ

============================================================
15. VALIDATION
============================================================

Criar exemplos clássicos.

Cada exemplo:

input
reference
expected
actual
error
tolerance

============================================================
16. GUI
============================================================

PySide6.

Tela principal:

┌─────────────────────────────────────┐
│ File Edit Model Analysis Results    │
├─────────────────────────────────────┤
│                                     │
│             VIEWPORT 3D             │
│                                     │
│                                     │
├──────────────┬──────────────────────┤
│ MODEL TREE   │ PROPERTIES           │
└──────────────┴──────────────────────┘

============================================================
17. MODELAGEM 3D
============================================================

Futuramente:

create node
create element
move node
delete element
assign material
assign section
assign support
assign load

============================================================
18. NORMATIVE
============================================================

Criar plugin architecture.

Não inserir regras normativas diretamente no solver.

Exemplo:

NormativePlugin

NBR8800Plugin

============================================================
19. REPORTS
============================================================

Criar:

ReportEngine

Formatos:

PDF
DOCX
HTML

============================================================
20. AI
============================================================

Criar:

AIService

com:

LocalAIProvider
CloudAIProvider
DisabledProvider

A aplicação deverá continuar funcionando com:

AI = OFF

============================================================
21. AI TOOLS
============================================================

Criar APIs estruturadas:

create_node
create_element
delete_element
assign_material
assign_section
apply_support
apply_load
create_load_case
create_combination
run_analysis
get_displacements
get_reactions
get_element_forces
generate_report

============================================================
22. FORMATO DO PROJETO
============================================================

Extensão:

.openstruct

O formato deverá possuir:

version
model
materials
sections
supports
loads
combinations
analysis_settings

============================================================
23. CLI
============================================================

Implementar:

openstruct validate
openstruct analyze
openstruct test
openstruct example

============================================================
24. TESTES
============================================================

Todo módulo importante deve possuir testes.

Não aceitar:

TODO

como substituto de funcionalidade implementada.

============================================================
25. PRIMEIRO MARCO

O primeiro marco será:

"3D FRAME SOLVER V1"

Deve permitir:

- criar nós;
- criar elementos;
- material;
- seção;
- apoios;
- cargas;
- montar K;
- resolver K u = F;
- calcular reações;
- calcular esforços;
- exportar resultados.

Sem GUI obrigatória nesta fase.

============================================================
26. SEGUNDO MARCO

"VALIDATED 3D FRAME SOLVER"

Todos os principais algoritmos devem possuir:

- testes unitários;
- testes de integração;
- benchmarks;
- validação documentada.

============================================================
27. TERCEIRO MARCO

"DESKTOP GUI"

Adicionar:

PySide6
+
viewport 3D.

============================================================
28. QUARTO MARCO

"SECOND ORDER"

Adicionar:

P-Delta.

============================================================
29. QUINTO MARCO

"BUCKLING"

Adicionar análise de flambagem elástica.

============================================================
30. SEXTO MARCO

"NORMATIVE ENGINE"

Adicionar sistema de normas.

============================================================
31. SÉTIMO MARCO

"STEEL DESIGN"

Adicionar dimensionamento de elementos metálicos.

============================================================
32. OITAVO MARCO

"REPORT ENGINE"

Adicionar:

memorial
relatórios
PDF
DOCX

============================================================
33. NONO MARCO

"AI COPILOT"

Adicionar agentes de IA.

============================================================
34. DÉCIMO MARCO

"OPTIMIZATION"

Adicionar otimização de perfis.

============================================================
35. REGRA FUNDAMENTAL

Nunca sacrificar precisão estrutural para acelerar desenvolvimento.

Prioridade:

CORREÇÃO
↓
VALIDAÇÃO
↓
RASTREABILIDADE
↓
PERFORMANCE
↓
INTERFACE