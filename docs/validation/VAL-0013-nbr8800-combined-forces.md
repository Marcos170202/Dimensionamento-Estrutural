# VAL-0013 — Interação força axial + momento fletor biaxial (NBR 8800:2024 §5.5.1.2)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.combined_forces`
**Data:** 2026-09-11
**Execução:** `pytest tests/validation/test_nbr8800_combined_forces_benchmark.py -v` (5 passed)

## Descrição

Valida a equação de interação entre força axial (tração ou compressão) e momento fletor biaxial, para barras sem torção, conforme ABNT NBR 8800:2024, §5.5.1.2. Rastreabilidade em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-COMB-001`/`002`).

## Referência

- Para `Nsd/Nrd ≥ 0,2`: `Nsd/Nrd + (8/9)·(Mx,sd/Mx,rd + My,sd/My,rd) ≤ 1,0` (equação a);
- Para `Nsd/Nrd < 0,2`: `Nsd/(2·Nrd) + (Mx,sd/Mx,rd + My,sd/My,rd) ≤ 1,0` (equação b).

## Nota sobre os valores usados

`Nsd`/`Nrd`/`Mx,sd`/`Mx,rd`/`My,sd`/`My,rd` usados abaixo são **hipotéticos** — não são valores catalográficos certificados para nenhum perfil específico (mesma disciplina de VAL-0008/VAL-0010 a VAL-0012). O objetivo é confirmar que as duas equações de interação (e a transição entre elas) estão implementadas corretamente, não fornecer um valor de projeto real.

## Resultados (executados em 2026-09-11)

### Caso 1 — `Nsd/Nrd=0,375` (≥0,2): equação a), dentro do limite

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Razão de interação | 0,778704 | 0,778704 | **APROVADO** |

### Caso 2 — `Nsd/Nrd=0,10` (<0,2): equação b), dentro do limite

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Razão de interação | 0,633333 | 0,633333 | **APROVADO** |

### Caso 3 — barra sobrecarregada (`Nsd/Nrd=0,875`, equação a)

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Razão de interação | 2,282407 | 2,282407 | **APROVADO** |

Razão `>1,0` → `is_ok=False`, confirmando a reprovação corretamente sinalizada.

### Caso 4 — fronteira exata `Nsd/Nrd=0,2`: usa a equação a)

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Razão de interação | 0,718519 | 0,718519 | **APROVADO** |

Confirma que `"≥"` inclui o limite exato na equação a) (não na b), que daria um valor diferente para o mesmo cenário).

### Caso 5 — momento uniaxial (`My,sd=0`)

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Razão de interação | 0,612037 | 0,612037 | **APROVADO** |

Confirma que o termo de `My` desaparece corretamente quando `My,sd=0` (barra sem momento em um dos eixos).

## Conclusão

`axial_bending_interaction_ratio`/`check_axial_and_bending_interaction` reproduzem exatamente (erro relativo 0) as duas equações de interação de §5.5.1.2 lidas diretamente da NBR 8800:2024, incluindo a transição exata entre elas em `Nsd/Nrd=0,2` e o caso de momento uniaxial.

**STATUS GERAL: APROVADO**, dentro do escopo implementado (interação N+M biaxial sem torção, §5.5.1.2).

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **§5.5.1.3** (força cortante) não precisa de nenhuma fórmula nova quando a força cortante atua em um único eixo central de inércia — a norma remete diretamente a §5.4.3 (`check_shear_major_axis`, já implementado); nada a validar aqui além de já registrar essa cláusula como lida (`NBR8800-COMB-002`).
- **§5.5.2** (seções tubulares circulares/retangulares submetidas a momento de torção, força axial, momentos fletores e força cortante — incluindo `Trd` para torção pura) **não é implementado** — requer modelagem de seções tubulares separadas de I/H/U no domínio geométrico (`Section`) e verificação de torção pura (`Trd`), nenhuma das duas ainda aberta neste pacote.
- **`Mx,rd`/`My,rd`**: apenas o eixo de maior momento de inércia tem `Mrd` completo implementado (`check_flexural_resistance_major_axis`, FLT+FLM+FLA) — o eixo de menor momento de inércia permanece com a mesma limitação já registrada em `NBR8800-FLEX-004`/docstring do módulo `flexure`.
- **Fora do escopo** (fases normativas futuras): ligações metálicas (§6), qualquer outra norma.
