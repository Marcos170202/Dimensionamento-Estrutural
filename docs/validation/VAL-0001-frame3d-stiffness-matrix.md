# VAL-0001 — Matriz de rigidez do `Element3D`

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componente validado:** `openstruct.domain.elements.frame3d.Element3D`
**Data:** 2026-09-07
**Execução:** `pytest tests/validation/test_frame3d_stiffness_benchmark.py -v` (5 passed)

## Descrição

Valida `local_stiffness_matrix()`, `transformation_matrix()` e
`global_stiffness_matrix()` de `Element3D` (elemento de pórtico
espacial de Euler-Bernoulli, 12 DOFs) contra soluções fechadas
clássicas de Resistência dos Materiais para uma barra em balanço
(cantilever). **Não envolve nenhuma norma técnica** — é verificação de
método numérico contra mecânica dos materiais, não contra a NBR 8800.

## Referência

Solução fechada de viga de Euler-Bernoulli para barra em balanço
(engastada em uma extremidade, carga concentrada na extremidade
livre), padrão em qualquer livro-texto de Mecânica dos Materiais
(p.ex. Hibbeler; Timoshenko & Gere):

| Solicitação | Fórmula |
|---|---|
| Alongamento axial | `u = P·L / (E·A)` |
| Rotação de torção | `φ = T·L / (G·J)` |
| Flecha em flexão (plano x-y) | `v = P·L³ / (3·E·Iz)` |
| Rotação na ponta (plano x-y) | `θz = P·L² / (2·E·Iz)` |
| Flecha em flexão (plano x-z) | `w = P·L³ / (3·E·Iy)` |
| Rotação na ponta (plano x-z) | `θy = −P·L² / (2·E·Iy)` |

## Hipóteses

- Elemento prismático, seção constante, material elástico-linear.
- Sem deformação por cisalhamento (Euler-Bernoulli, não Timoshenko).
- Nó 1 totalmente engastado (os 6 DOFs = 0); solução obtida resolvendo
  diretamente o sistema condensado `K[6:,6:]·u₂ = F₂` com
  `numpy.linalg.solve` — não depende de nenhum componente de
  Assembly/BoundaryConditions/Solver (ainda não implementados nesta
  fase).
- Material: `ASTM A572 Gr. 50` (E=200000 MPa, G=77000 MPa, ν=0.3).
- Seção: `W310x21` (A=2680 mm², Iy=3.79e6 mm⁴, Iz=37.0e6 mm⁴, J=52.8e3 mm⁴).
- Comprimento do balanço: L = 4000 mm (casos axis-aligned).

## Resultados (executados em 2026-09-07)

| Caso | Referência | OpenStruct 3D | Erro relativo | Tolerância | Status |
|---|---:|---:|---:|---:|:---:|
| Axial `u` (P=50000 N) | 3.7313432836e-01 mm | 3.7313432836e-01 mm | 0.0e+00 | 1e-9 | **APROVADO** |
| Torção `φ` (T=3e6 N·mm) | 2.9515938607e+00 rad | 2.9515938607e+00 rad | 0.0e+00 | 1e-9 | **APROVADO** |
| Flexão x-y, flecha `v` (P=10000 N) | 2.8828828829e+01 mm | 2.8828828829e+01 mm | 0.0e+00 | 1e-9 | **APROVADO** |
| Flexão x-y, rotação `θz` | 1.0810810811e-02 rad | 1.0810810811e-02 rad | 0.0e+00 | 1e-9 | **APROVADO** |
| Flexão x-z, flecha `w` (P=10000 N) | 2.8144239226e+02 mm | 2.8144239226e+02 mm | 0.0e+00 | 1e-9 | **APROVADO** |
| Flexão x-z, rotação `θy` | -1.0554089710e-01 rad | -1.0554089710e-01 rad | 0.0e+00 | 1e-9 | **APROVADO** |
| Orientação 3D arbitrária (dx,dy,dz)=(1000,2000,1500) mm — solução via sistema global vs. via sistema local transformado | ‖u‖ = referência (ver teste) | erro relativo 1.95e-13 | 1.95e-13 | 1e-8 | **APROVADO** |

Todos os erros relativos são de ordem de arredondamento de ponto
flutuante (`1e-13` a `0.0`) — esperado, já que a solução de um único
elemento de viga sob carga de extremidade é a solução **exata** da
equação diferencial de Euler-Bernoulli (não há erro de discretização a
reduzir nesse caso).

## Conclusão

`Element3D.local_stiffness_matrix()` reproduz exatamente (dentro de
precisão de ponto flutuante) as soluções clássicas de viga em balanço
para os quatro modos de deformação exigidos por PROGRAM_MASTER §7
(axial, flexão Y, flexão Z, torção). `transformation_matrix()` e
`global_stiffness_matrix()` são consistentes entre si e com
`local_stiffness_matrix()` para uma orientação 3D arbitrária.

**STATUS GERAL: APROVADO.**

Fora do escopo desta validação (fases futuras): efeito de
deformação por cisalhamento (viga de Timoshenko), P-Delta, flambagem,
e qualquer verificação normativa (NBR 8800) — nenhuma delas foi
avaliada aqui.
