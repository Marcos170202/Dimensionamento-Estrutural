# VAL-0002 — Pipeline SOLVER V1 (Assembly + BoundaryConditions + Solver + AnalysisResult)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `AnalysisModel`, `Assembly`, `BoundaryConditions`, `solve_linear_system`, `run_analysis`/`AnalysisResult`
**Data:** 2026-09-08
**Execução:** `pytest tests/validation/test_solver_v1_benchmark.py -v` (6 passed)

## Descrição

VAL-0001 validou `Element3D` isoladamente. VAL-0002 valida a **montagem
e resolução do sistema global** — a parte que só existe quando há mais
de um elemento e/ou apoios reais, isto é, exatamente o que a fase
SOLVER V1 acrescentou. **Não envolve nenhuma norma técnica.**

## Referência

1. Para uma viga prismática uniforme sob carga apenas nodal (sem carga
   distribuída), o elemento de viga de Euler-Bernoulli de 2 nós é a
   solução **exata** da equação diferencial — subdividir o vão não pode
   mudar o resultado em nenhum ponto. Fórmula da curva de deflexão
   (viga em balanço, carga `P` na ponta, `x` medido a partir do
   engaste): `v(x) = P·x²·(3L−x) / (6EI)`, `θ(x) = P·x·(2L−x) / (2EI)`
   (Hibbeler, Timoshenko & Gere — mecânica dos materiais clássica).
2. Equilíbrio de corpo rígido: `Σ F = 0`, `Σ M = 0` sobre qualquer
   ponto — válido para qualquer estrutura em equilíbrio,
   independentemente de sua formulação interna.
3. Para uma estrutura em "árvore" (sem malha fechada) com um único
   apoio engastado, a reação nesse apoio é determinada inteiramente
   por estática: `R = −F_aplicada`, `M_R = −(r × F_aplicada + M_aplicado)`.

## Hipóteses

- Mesmo material/seção de VAL-0001 (`ASTM A572 Gr. 50` / `W310x21`).
- Elementos `Element3D` (já validados individualmente em VAL-0001) —
  esta validação assume a formulação do elemento correta e foca na
  camada de montagem/solução.
- Sem recalque de apoio, sem carga distribuída/peso próprio (fora do
  escopo desta fase).

## Resultados (executados em 2026-09-08)

### Caso 1 — cadeia de 2 elementos (2000+2000mm) vs. fórmula fechada de 4000mm

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Flecha na ponta (nó 3) | 2.8828828829e+01 mm | 2.8828828829e+01 mm | 6.16e-16 | **APROVADO** |
| Rotação na ponta (nó 3) | 1.0810810811e-02 rad | 1.0810810811e-02 rad | 8.02e-16 | **APROVADO** |
| Flecha no nó interior (nó 2, x=L/2) | 9.0090090090e+00 mm | 9.0090090090e+00 mm | 5.92e-16 | **APROVADO** |
| Rotação no nó interior (nó 2) | 8.1081081081e-03 rad | 8.1081081081e-03 rad | 6.42e-16 | **APROVADO** |

### Caso 2 — equilíbrio global (3 nós, 2 elementos, 2 apoios, carga geral em 2 nós)

| Grandeza | Valor obtido | Tolerância | Status |
|---|---:|---:|:---:|
| `Σ Força` (deveria ser 0) | `[-2.3e-13, 3.6e-12, 0.0]` N | 1e-6 | **APROVADO** |
| `Σ Momento` sobre a origem (deveria ser 0) | `[-1.1e-08, 0.0, -1.9e-09]` N·mm | 1e-3 | **APROVADO** |
| Resíduo de equilíbrio nos DOFs livres (`K·u − F`) | 1.12e-08 | — | **APROVADO** (ruído de ponto flutuante) |

### Caso 3 — estrutura em árvore, apoio único (reação = estática pura)

| Componente | Referência (estática) | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Fx | -1.000000e+03 N | -1.000000e+03 N | 2.28e-13 | **APROVADO** |
| Fy | 2.000000e+03 N | 2.000000e+03 N | 8.43e-13 | **APROVADO** |
| Fz | 5.000000e+03 N | 5.000000e+03 N | 1.82e-16 | **APROVADO** |
| Mx | -6.300000e+06 N·mm | -6.300000e+06 N·mm | 8.03e-13 | **APROVADO** |
| My | -1.535000e+07 N·mm | -1.535000e+07 N·mm | 4.47e-14 | **APROVADO** |
| Mz | 4.920000e+06 N·mm | 4.920000e+06 N·mm | 7.32e-13 | **APROVADO** |

### Caso 4 — detecção de mecanismo

Modelo com elemento sem nenhum apoio: `run_analysis` propaga
`ModelInstabilityError` em vez de devolver um resultado silenciosamente
errado. **APROVADO.**

### Caso 5 — esforços internos (`element_forces`) para elemento alinhado com eixo global

Elemento único (4000mm, alinhado com X, `local == global`), carga
geral em todos os 6 componentes no nó livre. Os esforços internos nas
extremidades têm significado físico direto e verificável sem fórmula
extra: no nó engastado, devem ser exatamente iguais à reação de apoio
(Caso 3); no nó carregado, exatamente iguais à carga externa aplicada.

| Nó | Componente | Referência | OpenStruct 3D | Status |
|---|---|---:|---:|:---:|
| i (engaste) | Fx..Mz (6 componentes) | = `reactions[1]` | idêntico | **APROVADO** (6/6, tol. 1e-9) |
| j (carregado) | Fx..Mz (6 componentes) | = carga aplicada | idêntico | **APROVADO** (6/6, tol. 1e-9) |

Este caso fecha a lacuna apontada pelo CODE REVIEW AGENT: até então
`element_forces` só era verificado quanto à forma (shape), nunca
numericamente.

Todos os erros relativos ficam na ordem de `1e-13` a `1e-16`
(arredondamento de ponto flutuante) — esperado, já que os Casos 1 e 3
comparam contra soluções **exatas** (não há erro de discretização a
reduzir).

## Conclusão

`Assembly` monta corretamente `K_global`/`F_global` por sobreposição
nodal (Caso 1: o nó compartilhado entre 2 elementos não introduz
nenhum erro). `BoundaryConditions` particiona o sistema corretamente
e detecta mecanismo (Caso 4). `solve_linear_system` resolve o sistema
restrito corretamente. `run_analysis`/`AnalysisResult` calculam
deslocamentos, reações e (implicitamente, via equilíbrio) esforços
internos de forma fisicamente consistente (Casos 2 e 3 — equilíbrio
global e estática pura).

**STATUS GERAL: APROVADO.**

Fora do escopo desta validação (fases futuras): carga distribuída,
peso próprio, P-Delta, flambagem, qualquer verificação normativa.
