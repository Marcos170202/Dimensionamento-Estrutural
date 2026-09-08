# VAL-0005 — Carga concentrada fora dos nós (`PointLoad`)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `PointLoad`
**Data:** 2026-09-08
**Execução:** `pytest tests/validation/test_point_load_benchmark.py -v` (6 passed)

## Descrição

Valida `PointLoad` (PROGRAM_MASTER.md §10, "point loads" — item ainda faltando da lista de cargas: nodal ✓, distributed ✓, self weight ✓, point ✓ agora), que representa uma força concentrada em posição **arbitrária** ao longo do vão de um `Element3D` (não apenas nos nós, diferença central para `NodalLoad`). **Não envolve nenhuma norma técnica** — apenas estática básica e fórmulas fechadas clássicas de resistência dos materiais.

## Referência

- **Estática pura** (mesma técnica de VAL-0002/VAL-0003/VAL-0004): viga em balanço com carga concentrada `P` a uma distância `a` do engaste — `R = -P`, `M = -P·a` (equilíbrio de forças/momentos no engaste). Independe da rigidez do elemento.
- **Fórmulas fechadas** de viga em balanço sob carga concentrada em `x=a` (Hibbeler, *Mecânica dos Materiais*; Timoshenko/Gere, *Mecânica dos Materiais* — tabelas clássicas):

  ```
  v(L) = P·a²·(3L-a) / (6EI)      theta(L) = P·a² / (2EI)
  ```

- **Casos limite**: `PointLoad(position=0)` e `PointLoad(position=L)` devem reduzir **exatamente** (não apenas aproximadamente) a uma `NodalLoad` equivalente no nó correspondente — consequência direta das funções de forma de Hermite valerem `(1,0,0,0)`/`(0,0,1,0)` nos extremos do elemento (já verificado simbolicamente via SymPy antes da implementação, ver docstring de `PointLoad`).

## Hipóteses

- Mesmo material/seção de VAL-0001 a VAL-0004 (`W310x21`, aço `ASTM A572 Gr. 50`).
- Viga em balanço de 4000 mm, engastada em um nó, carga aplicada em posição interior arbitrária do vão.

## Resultados (executados em 2026-09-08)

### Caso 1 — carga transversal (fy) em posição interior (a=1500 mm, P=-10000 N)

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Reação Fy (estática pura, `-P`) | 10000.0 N | 10000.0 N | 0.0 | **APROVADO** |
| Reação Mz (estática pura, `-P·a`) | 15000000.0 N·mm | 15000000.0 N·mm | 0.0 | **APROVADO** |
| Flecha na ponta (`v(L)=Pa²(3L-a)/6EI`) | -5.320945945945946 mm | -5.320945945945945 mm | 1.9e-16 | **APROVADO** |
| Rotação na ponta (`θ(L)=Pa²/2EI`) | -0.0015202702702702704 rad | -0.0015202702702702695 rad | 5.9e-16 | **APROVADO** |

Resíduo de equilíbrio: 1.86e-9.

### Caso 2 — carga axial (fx) em posição interior (a=1000 mm, P=5000 N)

| Grandeza | Referência | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Reação Fx (estática pura, `-P`) | -5000.0 N | -5000.0 N | **APROVADO** |
| Deslocamento axial na ponta (`u=Pa/EA`) | 0.009328358208955223 mm | 0.009328358208955225 mm | **APROVADO** |

Confirma o alongamento constante além do ponto de aplicação (nenhuma força axial adicional atua entre `a` e `L`).

### Caso 3 — par UZ/RY (fz) em posição interior (a=2000 mm, P=-6000 N)

| Grandeza | Referência | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Reação Fz (estática pura, `-P`) | 6000.0 N | 6000.0 N | **APROVADO** |
| Reação My (estática pura, `+P·a`) | -12000000.0 N·mm | -12000000.0 N·mm | **APROVADO** |

Confirma que o sinal invertido do termo de momento no par UZ/RY (mesma convenção já validada para `DistributedLoad` em VAL-0003) também vale para `PointLoad`.

### Caso 4 — limite `a→L` (posição no nó final) vs. `NodalLoad`

| Grandeza | Diferença máxima | Status |
|---|---:|:---:|
| Reações (vetor completo) | 0.0 | **APROVADO** |
| Deslocamentos (vetor completo) | 0.0 | **APROVADO** |

### Caso 5 — limite `a→0` (posição no nó inicial) vs. `NodalLoad`

| Grandeza | Diferença máxima | Status |
|---|---:|:---:|
| Reações (vetor completo) | 0.0 | **APROVADO** |
| Deslocamentos (vetor completo) | 0.0 | **APROVADO** |

Confirma que `PointLoad` generaliza `NodalLoad` de forma consistente: nos extremos do vão, os dois produzem resultados numericamente **idênticos** (diferença exatamente zero, não apenas dentro de tolerância), como esperado das funções de forma de Hermite avaliadas nos nós.

## Conclusão

`PointLoad` calcula o vetor de carga nodal equivalente ("fixed-end forces") corretamente para os três eixos locais (axial, e os dois pares de flexão UY/RZ e UZ/RY, com o sinal invertido esperado no segundo par), confirmado contra estática pura e fórmulas fechadas clássicas de viga em balanço, com erros relativos entre 0 e 5.9e-16 (arredondamento de ponto flutuante). Os casos limite (`a→0`, `a→L`) reduzem exatamente a `NodalLoad`, confirmando a consistência entre as duas classes de carga.

**STATUS GERAL: APROVADO.**

Fora do escopo desta validação (fases futuras): momento concentrado fora dos nós (ver limitação documentada em `PointLoad`), GUI (PySide6), IA, P-Delta, flambagem, qualquer módulo normativo (incluindo NBR 8800) e dimensionamento.
