# VAL-0009 — Limitação do índice de esbeltez (NBR 8800:2024 §5.2.8.1/5.3.7.1)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.slenderness`
**Data:** 2026-09-09
**Execução:** `pytest tests/validation/test_nbr8800_slenderness_benchmark.py -v` (3 passed)

## Descrição

Valida a verificação (recomendada, **não** um estado-limite último obrigatório) do índice de esbeltez de barras tracionadas e comprimidas individuais, conforme ABNT NBR 8800:2024, §5.2.8.1 (limite 300) e §5.3.7.1 (limite 200). Rastreabilidade em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-TRAC-004`, `NBR8800-COMP-008`).

## Referência

- `ratio = ℓ/r` (índice de esbeltez, o maior entre os dois eixos principais);
- §5.2.8.1: "recomenda-se que o índice de esbeltez das barras tracionadas [...] não supere 300";
- §5.3.7.1: "recomenda-se que o índice de esbeltez das barras comprimidas [...] não supere 200".

## Hipóteses

Perfil `W310x21` (mesma geometria real de VAL-0001 a VAL-0008 — `Ag=2680mm²`, `Iy=3,79×10⁶mm⁴`, `Iz=37,0×10⁶mm⁴`). Ao contrário de VAL-0008 (que usou um `Cw` hipotético), aqui nenhum dado é hipotético — o raio de giração é derivado diretamente (`sqrt(I/A)`) das propriedades catalográficas já usadas nas validações anteriores.

## Resultados (executados em 2026-09-09)

### Caso 1 — índice de esbeltez bate com o cálculo manual

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| `ry = sqrt(Iy/Ag)` | 37,60557 mm | 37,60557 mm | — |
| `rz = sqrt(Iz/Ag)` | 117,49881 mm | 117,49881 mm | — |
| `L/ry` (`L=4000mm`, eixo fraco) | 106,36721 | 106,36721 | **APROVADO** |
| `L/rz` (`L=4000mm`, eixo forte) | 34,04290 | 34,04290 | **APROVADO** |

Confirma que o eixo fraco (menor raio de giração) governa (maior `L/r`), como esperado fisicamente.

### Caso 2 — coluna de 4m (esbeltez usual) fica dentro de ambos os limites

| Verificação | Índice (`L/r` governante) | Limite | Dentro da recomendação? |
|---|---:|---:|:---:|
| Tração (§5.2.8.1) | 106,36721 | 300 | **Sim** |
| Compressão (§5.3.7.1) | 106,36721 | 200 | **Sim** |

### Caso 3 — comprimento intermediário (9m) discrimina os dois limites diferentes

| Verificação | Índice (`L/r`) | Limite | Dentro da recomendação? |
|---|---:|---:|:---:|
| Tração (§5.2.8.1) | 239,32623 | 300 | **Sim** |
| Compressão (§5.3.7.1) | 239,32623 | 200 | **Não** |

A mesma barra física (mesma seção, mesmo comprimento) passa na recomendação de tração mas não na de compressão — confirma que os dois limites são aplicados corretamente e de forma independente, não um valor único reaproveitado por engano.

## Conclusão

`slenderness_ratio`/`check_tension_slenderness`/`check_compression_slenderness` reproduzem exatamente (erro relativo 0) o índice de esbeltez e os limites recomendados lidos diretamente da NBR 8800:2024. O Caso 3 confirma que os dois limites (300 para tração, 200 para compressão) são distintos e aplicados corretamente.

**STATUS GERAL: APROVADO**, dentro do escopo implementado.

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **Esta é uma recomendação, não uma verificação de estado-limite obrigatória** — `is_within_recommended_limit=False` não significa "reprovado" no sentido de `check_tension_member`/`check_compression_member`; a própria norma (§5.2.8.3) prevê que o responsável técnico estabeleça novos limites justificados quando a recomendação não for adotada.
- **Barras compostas** (§5.2.8.2, e a parte correspondente de §5.3.6 para compressão) **não são cobertas** — exigem modelagem de múltiplos perfis com ligações intermediárias, ainda ausente do domínio geométrico atual.
- **Fora do escopo** (fases normativas futuras): flexo-torção em seções monossimétricas/assimétricas (§5.3.5.2/5.3.5.3), área efetiva reduzida por flambagem local (§5.3.4.2/5.3.4.3), coeficiente de redução `Ct` em tração (§5.2.3/5.2.5), flexão e cisalhamento (§5.4), combinação de esforços (§5.5), ligações metálicas (§6), qualquer outra norma.
