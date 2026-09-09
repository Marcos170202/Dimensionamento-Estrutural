# VAL-0010 — Força cortante resistente de cálculo (NBR 8800:2024 §5.4.1.3/§5.4.3.1)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.shear`
**Data:** 2026-09-09
**Execução:** `pytest tests/validation/test_nbr8800_shear_benchmark.py -v` (5 passed)

## Descrição

Valida a força cortante resistente de cálculo, `Vrd`, de barras I/H/U fletidas em relação ao eixo perpendicular à alma (o caso mais comum), conforme ABNT NBR 8800:2024, §5.4.1.3 (condição de dimensionamento) e §5.4.3.1 (curva em 3 trechos: plastificação, flambagem inelástica e flambagem elástica por cisalhamento). Rastreabilidade em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-SHEAR-001` a `004`).

## Referência

- `λ = h/tw`; `λp = 1,10·sqrt(kv·E/fy)`; `λr = 1,37·sqrt(kv·E/fy)` (§5.4.3.1.1);
- `Vrd = Vpℓ/γa1` (`λ≤λp`); `Vrd = (λp/λ)·Vpℓ/γa1` (`λp<λ≤λr`); `Vrd = 1,24·(λp/λ)²·Vpℓ/γa1` (`λ>λr`);
- `Vpℓ = 0,60·Aw·fy`, `Aw = d·tw` (§5.4.3.1.2);
- `kv = 5,34` para almas sem enrijecedores transversais ou para `a/h>3`; `kv = 5,0+5/(a/h)²` nos demais casos (§5.4.3.1.1).

## Nota sobre a geometria usada

Ao contrário de `Ag`/`Iy`/`Iz`/`J` (valores de catálogo reais do perfil W310x21 usados em VAL-0001 a VAL-0009), as dimensões de alma (`d=400mm`, `h=350mm`, `tw` variável) usadas abaixo são **hipotéticas** — não são valores catalográficos certificados para nenhum perfil específico (mesma disciplina de VAL-0008 com `Cw`). O objetivo é confirmar que a fórmula está implementada corretamente para os três trechos da curva, não fornecer um valor de projeto real para um perfil específico. Aço hipotético com `fy=345MPa`, `E=200000MPa`, `γa1=1,10` (classe de combinação normal).

## Resultados (executados em 2026-09-09)

### Caso 1 — alma espessa (`tw=8mm`): ramo plástico

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `Aw = d·tw` | 3200,00 mm² | 3200,00 mm² | — |
| `Vpℓ = 0,60·Aw·fy` | 662400,00 N | 662400,00 N | — |
| `kv` (sem enrijecedores) | 5,3400 | 5,3400 | — |
| `λ = h/tw` | 43,7500 | 43,7500 | — |
| `λp` | 61,2024 | 61,2024 | — |
| `λr` | 76,2249 | 76,2249 | — |
| `Vrd` (`λ≤λp` → `Vpℓ/γa1`) | 602181,82 N | 602181,82 N | **APROVADO** |

Confirma o ramo de plastificação total da alma por cisalhamento (`λ` bem abaixo de `λp`).

### Caso 2 — alma intermediária (`tw=5mm`): ramo de flambagem inelástica

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ = h/tw` | 70,0000 | 70,0000 | — |
| `λp` / `λr` | 61,2024 / 76,2249 | — | — |
| `Vrd` (`λp<λ≤λr` → `(λp/λ)·Vpℓ/γa1`) | 329062,49 N | 329062,49 N | **APROVADO** |

Confirma que `λ=70` cai estritamente entre `λp` e `λr`, disparando o segundo ramo (redução linear em `1/λ`).

### Caso 3 — alma fina (`tw=2,5mm`): ramo de flambagem elástica

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ = h/tw` | 140,0000 | 140,0000 | — |
| `Vrd` (`λ>λr` → `1,24·(λp/λ)²·Vpℓ/γa1`) | 44594,45 N | 44594,45 N | **APROVADO** |

Confirma o terceiro ramo (redução quadrática, flambagem elástica da alma por cisalhamento antes do escoamento).

### Caso 4 — efeito dos enrijecedores transversais (`tw=5mm`, `a/h=1`)

| Grandeza | Sem enrijecedores | Com enrijecedores (`a/h=1`) |
|---|---:|---:|
| `kv` | 5,3400 | 10,0000 |
| `λp` | 61,2024 | 83,7526 |
| `Vrd` | 329062,49 N (ramo inelástico) | 376363,64 N (ramo plástico) |

`Vrd` aumenta **14,37%** com enrijecedores próximos (`a/h=1`) em relação ao caso sem enrijecedores, para a mesma alma fina — o `kv` maior desloca `λp`/`λr` para cima, o suficiente para a mesma alma (`λ=70`) sair do ramo inelástico e entrar no ramo plástico. Ambos os valores batem exatamente com o cálculo manual (`ValidationRecord` **APROVADO** no teste correspondente).

### Caso 5 — componentes intermediários isolados (`Aw`, `Vpℓ`, `kv`, `Vrd` via `shear_resistance`)

Todos batem exatamente (erro relativo 0) com o cálculo manual — ver `test_val0010_intermediate_quantities_match_manual_calculation`.

## Conclusão

`effective_shear_area_major_axis`, `plastic_shear_force`, `shear_buckling_coefficient`, `shear_resistance` e `check_shear_major_axis` reproduzem exatamente (erro relativo 0) as fórmulas de §5.4.3.1 lidas diretamente da NBR 8800:2024, nos três trechos da curva de `Vrd` (plástico, inelástico e elástico) e considerando o efeito de enrijecedores transversais em `kv`.

**STATUS GERAL: APROVADO**, dentro do escopo implementado (seções I, H e U fletidas em relação ao eixo perpendicular à alma).

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **§5.4.2** (momento fletor resistente de cálculo, `Msd≤Mrd`) **não é implementado** — remete aos Anexos D/E (classificação da seção compacta/semicompacta/esbelta e flambagem lateral com torção), substancialmente mais complexo; a condição de dimensionamento completa de §5.4.1.3 (`Msd≤Mrd` E `Vsd≤Vrd`) só está parcialmente coberta (apenas a parte de cisalhamento).
- **§5.4.3.2 a §5.4.3.6** (força cortante resistente para seções tubulares/caixão, T, cantoneiras duplas, I/H/U fletidas em torno do eixo fraco, e tubulares circulares) **não são implementadas** — mesma estrutura de fórmula de §5.4.3.1, mas com `kv`/área efetiva de cisalhamento diferentes; `shear_resistance` foi escrita de forma genérica o suficiente para ser reaproveitada por esses casos futuramente.
- **§5.4.3.1.3** (requisitos construtivos para dimensionamento dos próprios enrijecedores transversais — soldas, relação largura/espessura, momento de inércia mínimo) **não é implementado** — a distância `a` é recebida como parâmetro de entrada, não verificada/dimensionada.
- **§5.4.4** (chapas de reforço/lamelas) e **§5.4.5** (requisitos para seções soldadas) **não são implementados**.
- **§5.5** (combinação de momento fletor, força cortante, força axial e momento de torção) **não é implementado** — fase normativa futura, depende de §5.4.2 (flexão) estar completo.
- **Fora do escopo** (fases normativas futuras): flexo-torção em seções monossimétricas/assimétricas (§5.3.5.2/5.3.5.3), área efetiva reduzida por flambagem local (§5.3.4.2/5.3.4.3), coeficiente de redução `Ct` em tração (§5.2.3/5.2.5), ligações metálicas (§6), qualquer outra norma.
