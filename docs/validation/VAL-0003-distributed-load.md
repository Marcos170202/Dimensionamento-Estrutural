# VAL-0003 — Carga distribuída (`DistributedLoad`)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `DistributedLoad`, `ElementLoad.apply_to`, `LoadCase/LoadCombination.fixed_end_forces_local_for`, extração de `element_forces` em `run_analysis`
**Data:** 2026-09-08
**Execução:** `pytest tests/validation/test_distributed_load_benchmark.py -v` (8 passed)

## Descrição

Valida a carga uniformemente distribuída ao longo do vão de um `Element3D`, introduzida como extensão da fase SOLVER V1 (PROGRAM_MASTER §10: "Implementar: nodal loads, point loads, distributed loads, self weight" — nodal já validado em VAL-0001/0002, distribuída validada aqui). **Não envolve nenhuma norma técnica.**

## Referência

- **Estática pura** (independente de rigidez, mesma técnica de VAL-0002 Caso 3): para uma viga em balanço sob carga uniforme `w` (N/mm) em todo o vão `L`, a resultante `wL` atua no centroide (`x=L/2`); reação de força = `-wL`, reação de momento = `-wL²/2`.
- **Fórmulas fechadas clássicas** (Hibbeler; Timoshenko & Gere): balanço sob UDL — flecha na ponta `v = wL⁴/(8EI)`, rotação na ponta `θ = wL³/(6EI)`; viga simplesmente apoiada sob UDL — rotação em cada apoio `θ = wL³/(24EI)` (sinais opostos, por simetria).
- **Derivação do vetor de carga nodal equivalente** ("consistent load vector", trabalho virtual com as funções de forma cúbicas de Hermite — o mesmo método que gera a matriz de rigidez clássica): resultado padrão de qualquer livro-texto de elementos finitos (Logan; Cook/Malkus/Plesha), documentado em `domain/loads.py`.

## Hipóteses

- Mesmo material/seção de VAL-0001/0002 (`ASTM A572 Gr. 50` / `W310x21`).
- `Element3D` já validado isoladamente (VAL-0001) e em conjunto (VAL-0002) — esta validação foca especificamente na carga distribuída.
- Um único elemento por caso (permite comparação direta contra fórmula fechada); a propriedade de **superconvergência nodal** (resultados exatos nos nós mesmo sob carga distribuída, com um único elemento) é confirmada numericamente, não presumida.

## Resultados (executados em 2026-09-08)

### Caso 1 — balanço sob UDL, plano x-y (`wy`)

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Reação Fy (estática pura) | -2.0000e+04 N | -2.0000e+04 N | 0.0 | **APROVADO** |
| Reação Mz (estática pura) | -4.0000e+07 N·mm | -4.0000e+07 N·mm | 1.86e-16 | **APROVADO** |
| Flecha na ponta (fechada) | 2.16216e+01 mm | 2.16216e+01 mm | 3.29e-16 | **APROVADO** |
| Rotação na ponta (fechada) | 7.20721e-03 rad | 7.20721e-03 rad | 4.81e-16 | **APROVADO** |
| Esforço interno no nó livre (deveria ser 0) | 0 | 1.86e-09 | — | **APROVADO** |

### Caso 2 — balanço sob UDL, plano x-z (`wz`, par com sinal invertido)

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Reação Fz | -2.0000e+04 N | -2.0000e+04 N | 1.82e-16 | **APROVADO** |
| Reação My | 4.0000e+07 N·mm | 4.0000e+07 N·mm | 0.0 | **APROVADO** |
| Flecha na ponta | 2.11082e+02 mm | 2.11082e+02 mm | 0.0 | **APROVADO** |
| Rotação na ponta | -7.03606e-02 rad | -7.03606e-02 rad | 0.0 | **APROVADO** |

### Caso 3 — viga simplesmente apoiada sob UDL

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Reação Fy, apoio 1 (`wL/2`) | -1.0000e+04 N | -1.0000e+04 N | 0.0 | **APROVADO** |
| Reação Fy, apoio 2 (`wL/2`) | -1.0000e+04 N | -1.0000e+04 N | 0.0 | **APROVADO** |
| Rotação apoio 1 (`+wL³/24EI`) | 1.80180e-03 rad | 1.80180e-03 rad | 1.20e-16 | **APROVADO** |
| Rotação apoio 2 (`-wL³/24EI`) | -1.80180e-03 rad | -1.80180e-03 rad | 1.20e-16 | **APROVADO** |

Este caso confirma a **superconvergência nodal**: mesmo com um único elemento sob carga distribuída (situação onde a solução exata é uma quártica e a interpolação do elemento é cúbica), os valores **nos nós** — inclusive as rotações, que são graus de liberdade livres, não apoios — batem com a fórmula fechada à precisão de ponto flutuante.

### Caso 4 — equilíbrio global com carga nodal + distribuída combinadas

| Grandeza | Valor obtido | Status |
|---|---:|:---:|
| `Σ Força` (deveria ser 0) | `[0, 0, -1.8e-12]` N | **APROVADO** |
| `Σ Momento` sobre nó 1 (deveria ser 0) | `[0, 1.9e-09, 0]` N·mm | **APROVADO** |
| Resíduo de equilíbrio nos DOFs livres | 7.45e-09 | **APROVADO** |

## Conclusão

O vetor de carga nodal equivalente de `DistributedLoad` (derivado por trabalho virtual, ver `domain/loads.py`) e sua adição a `F_global` (`ElementLoad.apply_to`) e subtração na extração de `element_forces` (`run_analysis`) estão corretos nos dois planos de flexão (incluindo a inversão de sinal do termo de momento entre `UY/RZ` e `UZ/RY`, já estabelecida em VAL-0001 para a matriz de rigidez e agora confirmada também para o vetor de carga). Erros relativos entre 0 e 4.8e-16 (arredondamento de ponto flutuante) em todos os casos.

**STATUS GERAL: APROVADO.**

Fora do escopo desta validação (fases futuras): carga concentrada fora dos nós, peso próprio automático, qualquer verificação normativa.
