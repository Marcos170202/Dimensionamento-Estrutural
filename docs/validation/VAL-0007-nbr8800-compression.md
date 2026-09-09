# VAL-0007 — Barras comprimidas (`check_compression_member`, NBR 8800:2024 §5.3)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.compression`
**Data:** 2026-09-09
**Execução:** `pytest tests/validation/test_nbr8800_compression_benchmark.py -v` (4 passed)

## Descrição

Segundo módulo normativo do OpenStruct 3D (continuação do marco "NORMATIVE ENGINE"). Valida a verificação de barras prismáticas comprimidas conforme ABNT NBR 8800:2024, §5.3.1/5.3.2 (força axial resistente de cálculo), §5.3.3 (fator de redução χ), §5.3.4.1 (área efetiva sem flambagem local) e §5.3.5.1-a)/b) (força axial de flambagem por flexão). Rastreabilidade completa em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-COMP-001` a `005`).

**Lembrete de escopo importante**: esta fase implementa apenas flambagem por **flexão** (`Nex`, `Ney`). Flambagem por **torção** e **flexo-torção** (§5.3.5.1-c/5.3.5.2/5.3.5.3) não são implementadas — ver a limitação de segurança registrada em `NBR8800-COMP-005`. Os casos abaixo usam um perfil I com dupla simetria, onde essa omissão é adequada.

## Referência

Mesmo método de VAL-0006: cálculo manual independente de cada termo das fórmulas lidas diretamente do PDF fornecido pelo usuário —

- `Nc,Rd = χ·Aef·fy/γa1` (§5.3.2);
- `χ = 0,658^(λ0²)` para `λ0 ≤ 1,5`; `χ = 0,877/λ0²` para `λ0 > 1,5` (§5.3.3.1);
- `λ0 = sqrt(Ag·fy/Ne)` (§5.3.3.2);
- `Ne = π²EI/L²` (§5.3.5.1-a/b, flambagem por flexão).

## Hipóteses

- Perfil `W310x21` (`Ag = 2680 mm²`, `Iy = 3,79×10⁶ mm⁴`, `Iz = 37,0×10⁶ mm⁴`) e aço `ASTM A572 Gr. 50` (`fy = 345 MPa`, `E = 200000 MPa`) — mesmos valores de catálogo de VAL-0001 a VAL-0006.
- `Aef = Ag` (sem flambagem local, §5.3.4.1) em todos os casos.
- `Ne = min(Nex, Ney)` (sem torção/flexo-torção, ver lembrete de escopo acima).

## Resultados (executados em 2026-09-09)

### Caso 1 — coluna curta (`L = 1500 mm`), ramo `λ0 ≤ 1,5`

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ0 = sqrt(Ag·fy/Ne)` | 0,527332 | 0,527332 | **APROVADO** |
| `Nc,Rd = χ·Aef·fy/γa1` | 748193,15 N | 748193,15 N | **APROVADO** |

`χ = 0,890128` (coluna curta, próxima da resistência plena de escoamento). `is_ok = True` para `Nc,Sd = 200000 N` (utilização 0,267).

### Caso 2 — coluna esbelta (`L = 8000 mm`), ramo `λ0 > 1,5`

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ0 = sqrt(Ag·fy/Ne)` | 2,812435 | 2,812435 | **APROVADO** |
| `Nc,Rd = χ·Aef·fy/γa1` (ramo `λ0>1,5`) | 93195,70 N | 93195,70 N | **APROVADO** |

`χ = 0,110875` (coluna esbelta, flambagem domina — resistência bem abaixo do escoamento pleno).

### Caso 3 — descontinuidade conhecida em `λ0 = 1,5`

| Grandeza | Valor | 
|---|---:|
| `χ` pelo primeiro ramo (`0,658^λ0²`) | 0,3899494 |
| `χ` pelo segundo ramo (`0,877/λ0²`) | 0,3897778 |
| Diferença | 0,0001716 (~0,044%) |

`reduction_factor(1,5)` usa o **primeiro** ramo (a norma define o limite com `≤`), reproduzindo exatamente `0,3899494`. A pequena diferença entre os dois ramos no ponto de transição é uma característica conhecida desta curva empírica (mesma família de curvas do AISC 360), não um erro de implementação — confirmado numericamente aqui para não ser confundido com um bug em revisões futuras.

### Caso 4 — invariante fundamental: `Nc,Rd` nunca excede o escoamento puro

Para 5 comprimentos diferentes (500 mm a 20000 mm), `Nc,Rd` calculado sempre satisfez `Nc,Rd ≤ Ag·fy/γa1 = 840545,45 N` — consequência direta de `χ ≤ 1` (§5.3.3.1) e `Aef ≤ Ag` (§5.3.4), confirmando que a compressão nunca é "mais generosa" que o escoamento puro por tração da mesma seção.

## Conclusão

`check_compression_member` reproduz exatamente (erro relativo 0) as fórmulas de §5.3.1/5.3.2/5.3.3/5.3.5.1 lidas diretamente da NBR 8800:2024, em ambos os ramos do fator de redução χ (incluindo a transição em `λ0=1,5`), para colunas curtas e esbeltas.

**STATUS GERAL: APROVADO**, dentro do escopo implementado (flambagem por flexão apenas).

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **Flambagem por torção e flexo-torção não são calculadas** (§5.3.5.1-c, §5.3.5.2, §5.3.5.3) — requer a constante de empenamento `Cw`, ainda não exposta por `Section`. Para seções abertas de parede fina onde esses modos podem governar (cantoneiras, seções T, Z, C, seções monossimétricas ou assimétricas), usar `check_compression_member` sem incluir esses modos no `Ne` fornecido pode produzir um resultado **não conservador**. Os casos acima usam um perfil I com dupla simetria e travamento lateral típico, onde essa omissão é adequada — ver `NBR8800-COMP-005`.
- **Área efetiva reduzida por flambagem local não é calculada** (§5.3.4.2/5.3.4.3, Tabelas 4 e 5) — apenas o caso `Aef = Ag` (§5.3.4.1) tem fórmula implementada.
- Não implementado nesta fase: cantoneiras simples (§5.3.5.4), barras compostas (§5.3.6), limitação do índice de esbeltez (§5.3.7 — recomendação, não estado-limite obrigatório).
- **Fora do escopo** (fases normativas futuras): flexão e cisalhamento (§5.4), combinação de esforços (§5.5), ligações metálicas (§6), e qualquer outra norma (NBR 6120, NBR 8681).
