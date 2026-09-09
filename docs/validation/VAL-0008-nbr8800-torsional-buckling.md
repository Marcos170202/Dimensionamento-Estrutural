# VAL-0008 — Flambagem por torção (`torsional_buckling_force`, NBR 8800:2024 §5.3.5.1-c)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.compression.torsional_buckling_force`, `polar_radius_of_gyration`
**Data:** 2026-09-09
**Execução:** `pytest tests/validation/test_nbr8800_torsional_buckling_benchmark.py -v` (3 passed)

## Descrição

Fecha a limitação de segurança registrada em VAL-0007/`NBR8800-COMP-005`: implementa e valida `Nez` (força axial de flambagem por torção, §5.3.5.1-c), completando `Ne = min(Nex, Ney, Nez)` para seções com dupla simetria ou simétricas em relação a um ponto. Rastreabilidade em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-COMP-005/006/007`).

## Referência

- `r0 = sqrt(rx² + ry² + x0² + y0²)`, com `x0=y0=0` para seções com dupla simetria ou simétricas em relação a um ponto (§5.3.5.1);
- `Nez = (1/r0²)·[π²E·Cw/Lz² + G·J]` (§5.3.5.1-c).

## Nota sobre os valores de `Cw` usados

Ao contrário de `Ag`/`Iy`/`Iz`/`J` (valores de catálogo reais do perfil W310x21, já usados em VAL-0001 a VAL-0007), a constante de empenamento `Cw` usada abaixo é **hipotética** — não é um valor catalográfico certificado para este perfil (evitando citar um valor de memória sem fonte confiável, mesma disciplina de `docs/normative/NBR8800-RULES.md`). O objetivo é confirmar que a fórmula está implementada corretamente, não fornecer um valor de projeto real para este perfil específico.

## Resultados (executados em 2026-09-09)

### Caso 1 — `r0` e `Nez` batem com o cálculo manual

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `r0 = sqrt(ry²+rz²)` | 123,36997 mm | 123,36997 mm | **APROVADO** |
| `Nez = (1/r0²)·(π²E·Cw/Lz² + G·J)` | 276846,44 N | 276846,44 N | **APROVADO** |

### Caso 2 — cenário em que a torção governa (demonstração da limitação de segurança fechada)

Com o `Cw` hipotético usado (`Cw=1,2×10⁹ mm⁶`), `Nez` (276846,44 N) é menor que `Ney` (467572,51 N) e `Nex` (4564692,04 N) — **a torção governa**.

| Grandeza | Valor |
|---|---:|
| `Nc,Rd` incluindo `Nez` (`Ne=min(Nex,Ney,Nez)`) | 220722,11 N |
| `Nc,Rd` considerando só flexão (`Ne=min(Nex,Ney)`, como em VAL-0007) | 367377,44 N |
| Redução | **39,92%** |

Confirma numericamente por que a limitação registrada em `NBR8800-COMP-005` era real: para esta seção/comprimento, ignorar `Nez` superestimaria `Nc,Rd` em quase 40% — um resultado **não conservador**.

### Caso 3 — `Cw=0` (seção fechada) reduz `Nez` ao termo de Saint-Venant puro

| Grandeza | Referência (`G·J/r0²`) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `Nez` com `Cw=0` | 267119,59 N | 267119,59 N | **APROVADO** |

Confirma que seções fechadas/tubulares (sem empenamento, `Cw=0`) ainda têm uma capacidade de flambagem torcional finita, vinda inteiramente da rigidez de Saint-Venant (`G·J`).

## Conclusão

`torsional_buckling_force`/`polar_radius_of_gyration` reproduzem exatamente (erro relativo 0) as fórmulas de §5.3.5.1-c lidas diretamente da NBR 8800:2024. O Caso 2 demonstra, com números reais, o motivo concreto da limitação de segurança registrada nas fases anteriores — não apenas uma precaução teórica.

**STATUS GERAL: APROVADO**, dentro do escopo implementado (seções com dupla simetria ou simétricas em relação a um ponto).

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **Seções monossimétricas** (§5.3.5.2, ex.: perfis U/C, T) e **assimétricas** (§5.3.5.3, ex.: cantoneiras de abas desiguais) **continuam fora do escopo** — a norma não permite usar `min(Nex, Ney, Nez)` diretamente nesses casos; exige a força de flambagem por flexo-torção (`Neyz`, combinação não linear com a excentricidade do centro de cisalhamento) ou a raiz de uma equação cúbica, nenhuma das duas implementada.
- Não implementado nesta fase: área efetiva reduzida por flambagem local (§5.3.4.2/5.3.4.3), cantoneiras simples (§5.3.5.4), barras compostas (§5.3.6), limitação de esbeltez (§5.3.7 — recomendação).
- **Fora do escopo** (fases normativas futuras): flexão e cisalhamento (§5.4), combinação de esforços (§5.5), ligações metálicas (§6), e qualquer outra norma.
