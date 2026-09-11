# VAL-0012 — Flambagem local da mesa e da alma — FLM/FLA (NBR 8800:2024 §Anexo D, Tabela D.1)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.flexure` (FLM, FLA, `check_flexural_resistance_major_axis`)
**Data:** 2026-09-11
**Execução:** `pytest tests/validation/test_nbr8800_flexure_flm_fla_benchmark.py -v` (6 passed)

## Descrição

Fecha a limitação de segurança registrada em VAL-0011/`NBR8800-FLEX-004`: implementa e valida a flambagem local da mesa comprimida (FLM, perfis laminados e soldados) e a flambagem local da alma (FLA), completando `Mrd = min(Mrd_FLT, Mrd_FLM, Mrd_FLA)` — com o limite de 5.4.2.2 aplicado ao resultado — para seções I, H com dois eixos de simetria e seções U não sujeitas a momento de torção, fletidas em relação ao eixo de maior momento de inércia (Anexo D, Tabela D.1, primeira linha). Rastreabilidade em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-FLEX-005` a `008`).

## Referência

- FLM, perfis laminados: `Mcr = 0,69·E/λ²·Wc`, `λr = 0,83·sqrt(E/(fy-σr))` (D.2.8-f);
- FLM, perfis soldados: `Mcr = 0,90·E·kc/λ²·Wc`, `λr = 0,95·sqrt(E/((fy-σr)/kc))`, `kc = 4/sqrt(h/tw)` limitado a `[0,35; 0,76]` (D.2.8-f, Tabela 4 nota a);
- FLM: `λ = (bf/2)/tf` (D.2.8-h), `λp = 0,38·sqrt(E/fy)`, `Mr = (fy-σr)·W` (D.2.8-e, mesmo `σr=0,3·fy` de FLT);
- FLA: `λ = h/tw`, `λp = 3,76·sqrt(E/fy)`, `λr = 5,70·sqrt(E/fy)`, `Mr = fy·W` (Tabela D.1 — nota: diferente de FLT/FLM);
- FLA, `λ>λr`: remete ao Anexo E (vigas de alma esbelta), fora do escopo — `check_flexural_resistance_major_axis` valida essa precondição (D.1.2) antes de calcular qualquer coisa;
- 5.4.2.2: `Mrd ≤ 1,50·W·fy/γa1` (aplicado ao `Mrd` final, após o `min`).

## Nota sobre a geometria usada

Mesma seção hipotética de VAL-0011 (`Iy=20×10⁶mm⁴`, `J=500×10³mm⁴`, `d=400mm`, `tf=16mm`, `W=900×10³mm³`, `Z=1000×10³mm³`, `ry=60mm`), com dimensões de mesa/alma adicionais também hipotéticas (mesma disciplina de VAL-0008/VAL-0010/VAL-0011) — o objetivo é confirmar as fórmulas dos três estados-limite e da lógica de governo (mínimo), não fornecer um valor de projeto real. Aço hipotético `fy=345MPa`, `E=200000MPa`, `γa1=1,10`, `Lb=1500mm`, `Cb=1,0`.

## Resultados (executados em 2026-09-11)

### Caso 1 — mesa e alma espessas (`bf=200mm, tf=16mm, h=350mm, tw=8mm`): FLT governa

| Estado-limite | Mrd (N·mm) | Ramo |
|---|---:|:---:|
| FLT | 313 636 363,64 | plástico |
| FLM (laminado) | 313 636 363,64 | plástico |
| FLA | 313 636 363,64 | plástico |
| **`Mrd = min(...)`** | **313 636 363,64** | — |

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `Mrd` | 313 636 363,64 N·mm | 313 636 363,64 N·mm | **APROVADO** |

### Caso 2 — mesa fina laminada (`bf=300mm, tf=5mm`): FLM governa, ramo elástico

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ_FLM = (bf/2)/tf` | 30,0000 | 30,0000 | — |
| `Mrd_FLM` (elástico) | 125 454 545,45 N·mm | — | — |
| `Mrd` final (min) | 125 454 545,45 N·mm | 125 454 545,45 N·mm | **APROVADO** |

Confirma que FLM (125,45×10⁶) é muito menor que FLT (313,64×10⁶) e FLA (313,64×10⁶) — FLM de fato governa.

### Caso 3 — mesa fina soldada (`bf=300mm, tf=5mm`, mesma alma do Caso 1): FLM com `kc`, ramo elástico

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `kc = 4/sqrt(h/tw)` (clipado) | 0,604743 | 0,604743 | — |
| `Mrd_FLM` (soldado, elástico) | 98 957 971,12 N·mm | 98 957 971,12 N·mm | **APROVADO** |

Confirma que o perfil soldado (`kc<0,767`) é mais conservador que o laminado equivalente (98,96×10⁶ < 125,45×10⁶ do Caso 2), como esperado fisicamente (tensões residuais de soldagem maiores).

### Caso 4 — alma fina não esbelta (`h=350mm, tw=3mm`): FLA governa, ramo inelástico

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λ_FLA = h/tw` | 116,6667 | 116,6667 | — |
| `λp_FLA` / `λr_FLA` | 90,5302 / 137,2399 | — | — |
| `Mrd_FLA` (inelástico) | 296 086 782,92 N·mm | 296 086 782,92 N·mm | **APROVADO** |

Confirma que `λ_FLA` cai estritamente entre `λp` e `λr` (segundo ramo) e que FLA (296,09×10⁶) governa sobre FLT/FLM (313,64×10⁶ ambos).

### Caso 5 — limite de 5.4.2.2 (`Mrd ≤ 1,50·W·fy/γa1`)

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `1,50·W·fy/γa1` | 423 409 090,91 N·mm | 423 409 090,91 N·mm | **APROVADO** |

Com um módulo plástico artificialmente alto (`Z=10×10⁶mm³`, fator de forma extremo e hipotético), `Mrd` é corretamente limitado por 5.4.2.2 em vez de crescer sem limite com `Mpl`.

### Caso 6 — precondição D.1.2 (viga de alma esbelta → `ValueError`)

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `λr_FLA = 5,70·sqrt(E/fy)` | 137,2399 | 137,2399 | **APROVADO** |

Com `h=1000mm, tw=2mm` (`λ_FLA=500 > λr_FLA=137,24`), `check_flexural_resistance_major_axis` levanta `ValueError` corretamente, recusando calcular FLT/FLM/FLA para uma viga de alma esbelta (fora do escopo do Anexo D — exigiria o Anexo E, não implementado).

## Conclusão

`flange_local_buckling_coefficient_welded`, `flange_local_buckling_moment_rolled`, `flange_local_buckling_moment_welded` e `check_flexural_resistance_major_axis` reproduzem exatamente (erro relativo 0) as fórmulas de D.2.8-e/f/h e da Tabela D.1 lidas diretamente da NBR 8800:2024, para os três estados-limite (FLT, FLM, FLA), a lógica de governo (`min`), o limite de 5.4.2.2 e a precondição de aplicabilidade do Anexo D (D.1.2).

**STATUS GERAL: APROVADO** — a limitação de segurança registrada em VAL-0011/`NBR8800-FLEX-004` está **FECHADA** para seções I, H com dois eixos de simetria e seções U não sujeitas a momento de torção, fletidas em relação ao eixo de maior momento de inércia (Anexo D, Tabela D.1, primeira linha).

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **Demais linhas da Tabela D.1** (seções monossimétricas, tubulares/caixão, T, cantoneiras duplas, sólidas, e flexão em torno do eixo de menor momento de inércia) **não são implementadas**.
- **Anexo E** (vigas de alma esbelta) **não é implementado** — `check_flexural_resistance_major_axis` apenas detecta e recusa esse caso (precondição D.1.2), não o calcula.
- **5.4.2.3, casos b) e c)**, e **5.4.2.4/5.4.2.5** (`Cb` para balanços e seções monossimétricas) **não são implementados** — apenas o caso geral duplamente simétrico (5.4.2.3-a).
- **5.4.2.6** (furos na mesa tracionada) **não é implementado**.
- **⚠️ Atenção sobre sinal de `Msd`** (já registrada em VAL-0011): `FlexureCheckResult.is_ok` não toma o valor absoluto de `msd` — o chamador é responsável por passar `abs(msd)` quando o interesse é a magnitude do momento.
- **Fora do escopo** (fases normativas futuras): combinação de esforços (§5.5, agora desbloqueada por este incremento), ligações metálicas (§6), qualquer outra norma.
