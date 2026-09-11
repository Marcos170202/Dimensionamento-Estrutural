# VAL-0011 — Flambagem lateral com torção — FLT (NBR 8800:2024 §5.4.1.3/§5.4.2/Anexo D)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.flexure`
**Data:** 2026-09-11
**Execução:** `pytest tests/validation/test_nbr8800_flexure_benchmark.py -v` (5 passed)

## Descrição

Valida o momento fletor resistente de cálculo, `Mrd`, para o estado-limite de flambagem lateral com torção (FLT) de barras I/H com dois eixos de simetria e barras U não sujeitas a momento de torção, fletidas em relação ao eixo de maior momento de inércia — Tabela D.1 (primeira linha) e D.2.8-a do Anexo D. Rastreabilidade em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-FLEX-001` a `004`).

## Referência

- `λ = Lb/ry`; `λp = 1,76·sqrt(E/fy)`; `λr` conforme D.2.8-a;
- `Mrd = Mpl/γa1` (`λ≤λp`); `Mrd = [Mpl-(Mpl-Mr)·(λ-λp)/(λr-λp)]/γa1` (`λp<λ≤λr`); `Mrd = Mcr/γa1` (`λ>λr`);
- `Mpl = fy·Z`; `Mr = (fy-0,3·fy)·W` (§D.2.8-a, item e);
- `Mcr = (Cb·π²·E·Iy/Lb²)·sqrt((Cw/Iy)·(1+0,039·J·Lb²/Cw))` (D.2.8-a);
- `λr = (1,38·Cb·sqrt(Iy·J)/(ry·J·β1))·sqrt(1+sqrt(1+27·Cw·β1²/(Cb²·Iy)))`, `β1=Mr/(E·J)` (D.2.8-a);
- `Cb = 12,5·Mmax/(2,5·Mmax+3·MA+4·MB+3·MC)` (§5.4.2.3-a, `Rm=1,0` para seções duplamente simétricas);
- `Cw = Iy·(d-tf)²/4` para seções I (D.2.8-a).

## Nota sobre a geometria usada

Ao contrário de `Ag`/`Iy`/`Iz`/`J` (valores de catálogo reais do perfil W310x21 usados em VAL-0001 a VAL-0009), as propriedades de seção (`Iy=20×10⁶mm⁴`, `J=500×10³mm⁴`, `d=400mm`, `tf=16mm`, `W=900×10³mm³`, `Z=1000×10³mm³`, `ry=60mm`) usadas abaixo são **hipotéticas** — não são valores catalográficos certificados para nenhum perfil específico (mesma disciplina de VAL-0008 com `Cw` e VAL-0010 com as dimensões de alma). O objetivo é confirmar que as fórmulas dos três trechos da curva de `Mrd` estão implementadas corretamente, não fornecer um valor de projeto real para um perfil específico. Aço hipotético com `fy=345MPa`, `E=200000MPa`, `γa1=1,10` (classe de combinação normal).

## Resultados (executados em 2026-09-11)

### Grandezas de base

| Grandeza | Valor |
|---|---:|
| `Cw = Iy·(d-tf)²/4` | 737 280 000 000 mm⁶ |
| `Mr = 0,7·fy·W` | 217 350 000 N·mm |
| `Mpl = fy·Z` | 345 000 000 N·mm |
| `λp = 1,76·sqrt(E/fy)` | 42,3758 |
| `λr` (Cb=1,0) | 123,1865 |

### Caso 1 — `Lb=1500mm` (curto): ramo plástico

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ = Lb/ry` | 25,0000 | 25,0000 | — |
| `Mrd` (`λ≤λp` → `Mpl/γa1`) | 313 636 363,64 N·mm | 313 636 363,64 N·mm | **APROVADO** |

### Caso 2 — `Lb=4000mm` (intermediário): ramo inelástico

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ = Lb/ry` | 66,6667 | 66,6667 | — |
| `Mrd` (`λp<λ≤λr` → interpolação linear) | 278 754 298,51 N·mm | 278 754 298,51 N·mm | **APROVADO** |

Confirma que `λ=66,67` cai estritamente entre `λp` e `λr`, disparando o segundo ramo.

### Caso 3 — `Lb=12000mm` (longo): ramo elástico

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ = Lb/ry` | 200,0000 | 200,0000 | — |
| `Mcr` (D.2.8-a) | 115 427 028,93 N·mm | 115 427 028,93 N·mm | — |
| `Mrd` (`λ>λr` → `Mcr/γa1`) | 104 933 662,66 N·mm | 104 933 662,66 N·mm | **APROVADO** |

Confirma o terceiro ramo (flambagem elástica por FLT antes do escoamento).

### Caso 4 — efeito do fator `Cb` (`Lb=12000mm`, ramo elástico)

| Grandeza | `Cb=1,0` (momento uniforme) | `Cb=1,75` (momento não uniforme) |
|---|---:|---:|
| `Mrd` | 104 933 662,66 N·mm | 183 633 909,66 N·mm |

`Mrd` aumenta **75,00%** com `Cb=1,75` em relação ao momento uniforme, para o mesmo comprimento destravado — confirma numericamente que a implementação de `Cb` reflete o benefício esperado de um diagrama de momento não uniforme (Cb maior → Mcr maior → Mrd maior no ramo elástico). Ambos os valores batem exatamente com o cálculo manual (`ValidationRecord` **APROVADO** no teste correspondente).

### Caso 5 — componentes intermediários isolados (`Cw`, `Cb`, `Mcr`, `λr`)

Todos batem exatamente (erro relativo 0) com o cálculo manual — ver `test_val0011_intermediate_quantities_match_manual_calculation`.

## Conclusão

`warping_constant_i_section`, `moment_gradient_factor_doubly_symmetric`, `lateral_torsional_buckling_moment`, `lateral_torsional_buckling_slenderness_limit`, `flexural_resistance` e `check_lateral_torsional_buckling` reproduzem exatamente (erro relativo 0) as fórmulas de D.2.8-a e 5.4.2.3-a lidas diretamente da NBR 8800:2024, nos três trechos da curva de `Mrd` (plástico, inelástico e elástico) e considerando o efeito do fator de modificação `Cb`.

**STATUS GERAL: APROVADO**, dentro do escopo implementado (FLT de seções I/H duplamente simétricas e U não sujeitas a torção, fletidas em relação ao eixo de maior momento de inércia).

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **⚠️ LIMITAÇÃO DE SEGURANÇA IMPORTANTE**: NBR 8800:2024, 5.4.2.1 exige que `Mrd` considere, conforme o caso, TODOS os estados-limite aplicáveis (FLT, FLM, FLA, flambagem local da aba, flambagem local da parede do tubo, escoamento da mesa tracionada), tomando o MENOR valor entre os que se aplicam. Esta fase implementa **apenas FLT**. Para uma seção real, se FLM ou FLA governar (típico de mesas ou almas muito esbeltas), o `Mrd` retornado por `check_lateral_torsional_buckling` seria **NÃO CONSERVADOR** se tratado como o `Mrd` completo da barra — deve ser interpretado apenas como a parcela de FLT. Ver `NBR8800-FLEX-004`.
- **5.4.2.2** (limite `Mrd ≤ 1,50·W·fy/γa1` para garantir validade da análise elástica) **não é aplicado** por esta função — deve ser aplicado pelo chamador ao `Mrd` GOVERNANTE final, quando FLM/FLA existirem, para não ser aplicado múltiplas vezes por engano.
- **5.4.2.3, casos b) e c)** (balanços) e **5.4.2.4/5.4.2.5** (fórmulas alternativas de `Cb` para seções I/U com uma mesa livre para se deslocar lateralmente) **não são implementados** — apenas o caso geral duplamente simétrico (5.4.2.3-a) está coberto.
- **Demais linhas da Tabela D.1** (seções monossimétricas, tubulares/caixão, T, cantoneiras duplas, sólidas, e flexão em torno do eixo de menor momento de inércia — onde FLT nem se aplica, D.2.8-g) **não são implementadas**.
- **Anexo E** (vigas de alma esbelta) **não é implementado** — substitui o Anexo D inteiramente quando a seção não satisfaz D.1.2; esta função não verifica esse requisito de aplicabilidade (responsabilidade do chamador nesta fase).
- **Fora do escopo** (fases normativas futuras): FLM/FLA (próximo incremento natural desta mesma fase), combinação de esforços (§5.5), ligações metálicas (§6), qualquer outra norma.
