# VAL-0004 — Peso próprio (`self_weight_loads`)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `self_weight_loads`
**Data:** 2026-09-08
**Execução:** `pytest tests/validation/test_self_weight_benchmark.py -v` (5 passed)

## Descrição

Valida o peso próprio automático (PROGRAM_MASTER §10, último item da lista de cargas ainda faltando: "self weight"), calculado a partir de `material.density`, `section.A` e uma aceleração de gravidade, gerando uma `DistributedLoad` por elemento (já validada isoladamente em VAL-0003). **Não envolve nenhuma norma técnica.**

## Referência

- Peso por unidade de comprimento: `w = density × A × gravity`. A armadilha dimensional (e por que `gravity` precisa estar em **m/s²**, não mm/s², apesar de todo o resto do projeto usar mm) está documentada em detalhe na docstring de `self_weight_loads` — resumo: `density[kg/mm³] × A[mm²] = kg/mm` (massa/comprimento); `kg/mm × m/s²` cancela corretamente para `N/mm`, porque `N = kg·m/s²` por definição do SI.
- Estática pura (mesma técnica de VAL-0002/VAL-0003): reação de uma viga em balanço sob carga distribuída de resultante `w·L` no centroide do vão.

## Hipóteses

- Mesmo material/seção de VAL-0001/0002/0003. Perfil `W310x21` tem massa nominal ~21 kg/m — usado como checagem de sanidade da fórmula antes mesmo de rodar o solver (ver commit: `density×A = 21.038 kg/m`, bate com o nome do perfil).
- `gravity = 9.81 m/s²` (padrão de `self_weight_loads`).

## Resultados (executados em 2026-09-08)

`W_SELF = density × A × gravity = 0.20638278 N/mm` (calculado à mão, usado como referência em todos os casos abaixo).

### Caso 1 — viga horizontal em balanço (peso vira carga transversal pura)

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Reação Fz (estática pura, `+wL`) | 825.53112 N | 825.53112 N | 1.38e-16 | **APROVADO** |
| Reação My (estática pura, `-wL²/2`) | -1651062.24 N·mm | -1651062.24 N·mm | 1.41e-16 | **APROVADO** |
| Flecha na ponta (fechada, `-wL⁴/8EI`) | -8.712729 mm | -8.712729 mm | 0.0 | **APROVADO** |

### Caso 2 — coluna vertical (peso vira compressão axial pura, sem flexão)

| Grandeza | Referência | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Reação Fz (`+wL`) | 825.53112 N | 825.53112 N | **APROVADO** |
| Reação Mx (deve ser 0 — sem flexão) | 0 | 0.0 | **APROVADO** |
| Reação My (deve ser 0 — sem flexão) | 0 | 0.0 | **APROVADO** |

Confirma que a projeção do peso nos eixos locais é puramente axial quando o elemento é paralelo à gravidade — nenhum termo espúrio de flexão aparece.

### Caso 3 — pórtico em L (coluna + viga, 2 elementos)

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Reação Fz total (`w×(coluna+viga)`) | 1135.10529 N | 1135.10529 N | 0.0 | **APROVADO** |
| Resíduo de equilíbrio | — | 2.33e-10 | — | **APROVADO** |

Confirma que o peso de **múltiplos elementos** (orientações diferentes) se soma corretamente na reação total.

### Caso 4 — elemento inclinado (3-4-5, 5000mm)

| Grandeza | Referência | OpenStruct 3D | Erro relativo | Status |
|---|---:|---:|---:|:---:|
| Reação Fz (`w×L`) | 1031.9139 N | 1031.9139 N | 2.09e-14 | **APROVADO** |
| Reação Fx, Fy (deveriam ser ~0) | 0 | ~1e-15 | — | **APROVADO** |
| Resíduo de equilíbrio | — | 2.16e-11 | — | **APROVADO** |

## Conclusão

`self_weight_loads` calcula `w = density×A×gravity` corretamente (confirmado contra cálculo manual e contra a massa nominal conhecida do perfil `W310x21`, ~21 kg/m) e projeta esse peso nos eixos locais de cada elemento corretamente para orientação horizontal (carga transversal pura), vertical (carga axial pura, sem contaminação de flexão) e inclinada (equilíbrio global fechado). Erros relativos entre 0 e 2.1e-14 (arredondamento de ponto flutuante) em todos os casos.

**STATUS GERAL: APROVADO.**

Fora do escopo desta validação (fases futuras): carga concentrada fora dos nós, qualquer verificação normativa (a NBR 6120 define valores característicos de peso próprio de materiais de construção — não usada aqui, pois este cálculo é geométrico/físico direto a partir de `Material.density`, não uma tabela normativa).
