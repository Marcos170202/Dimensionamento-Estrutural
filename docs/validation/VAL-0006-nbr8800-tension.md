# VAL-0006 — Barras tracionadas (`check_tension_member`, NBR 8800:2024 §5.2)

**Agente responsável:** STRUCTURAL VALIDATION AGENT
**Componentes validados:** `openstruct.normative.nbr8800.tension.check_tension_member`,
`openstruct.normative.nbr8800.resistance_factors.steel_resistance_factors`
**Data:** 2026-09-09
**Execução:** `pytest tests/validation/test_nbr8800_tension_benchmark.py -v` (3 passed)

## Descrição

Primeira validação de um módulo **normativo** do OpenStruct 3D — início do marco "NORMATIVE ENGINE" (`PROGRAM_MASTER.md`, seção 30). Valida a verificação de barras prismáticas tracionadas conforme ABNT NBR 8800:2024, 5.2.1.2/5.2.2 (força axial resistente de cálculo) e 4.9.2, Tabela 3 (coeficientes de ponderação da resistência do aço estrutural). Rastreabilidade completa de cada regra em `docs/normative/NBR8800-RULES.md` (RULE-IDs `NBR8800-RES-001`, `NBR8800-TRAC-001/002/003`).

## Referência

Diferente das validações anteriores (VAL-0001 a VAL-0005, que comparam contra estática pura ou fórmulas fechadas de resistência dos materiais), aqui a "fórmula de referência" é a própria fórmula normativa — lida diretamente do PDF da NBR 8800:2024 fornecido pelo usuário (não de memória, ver `docs/normative/NBR8800-RULES.md`):

- `Nt,Rd = min(Ag·fy/γa1, Ae·fu/γa2)` (5.2.2, casos a e b);
- `Nt,Sd ≤ Nt,Rd` (5.2.1.2);
- `γa1 = 1,10`, `γa2 = 1,35` para combinações normais; `γa1 = 1,00`, `γa2 = 1,15` para combinações excepcionais (4.9.2, Tabela 3).

O método de validação é o cálculo manual independente de cada termo da fórmula (mesma técnica de "referência calculada à mão" usada em VAL-0001 a VAL-0005), confirmando que o código reproduz exatamente a aritmética lida do documento — não um "exemplo de livro-texto" da norma (evita citar um valor de memória).

## Hipóteses

- Perfil `W310x21` (`Ag = 2680 mm²`) e aço `ASTM A572 Gr. 50` (`fy = 345 MPa`, `fu = 450 MPa`) — mesmos valores de catálogo já usados em VAL-0001 a VAL-0005.
- Casos 1 e 3: sem furos (`An = Ag`, 5.2.4.2) e ligação direta hipotética (`Ct = 1`, não implementado nesta fase — ver limitação abaixo). Caso 2: área líquida efetiva reduzida artificialmente para exercitar o caso em que a ruptura governa.

## Resultados (executados em 2026-09-09)

### Caso 1 — sem furos, combinação normal, escoamento governa

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Nt,Rd escoamento (`Ag·fy/1,10`) | 840545,4545 N | 840545,4545 N | **APROVADO** |
| Nt,Rd ruptura (`Ae·fu/1,35`) | 893333,3333 N | 893333,3333 N | **APROVADO** |
| Nt,Rd governante (o menor) | 840545,4545 N | 840545,4545 N | **APROVADO** |
| Taxa de utilização (`Nt,Sd=500000 N`) | 0,594852 | 0,594852 | **APROVADO** |

Estado-limite governante: escoamento da seção bruta (confirmado, `840545,45 N < 893333,33 N`). `is_ok = True`.

### Caso 2 — área líquida efetiva reduzida, ruptura governa

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Nt,Rd ruptura (`Ae=900mm², Ae·fu/1,35`) | 300000,0 N | 300000,0 N | **APROVADO** |
| Nt,Rd governante (ruptura) | 300000,0 N | 300000,0 N | **APROVADO** |

Estado-limite governante: ruptura da seção líquida (confirmado, `300000,0 N < 840545,45 N`).

### Caso 3 — combinação excepcional usa coeficientes reduzidos da Tabela 3

| Grandeza | Referência (cálculo manual) | OpenStruct 3D | Status |
|---|---:|---:|:---:|
| Nt,Rd escoamento, excepcional (`Ag·fy/1,00`) | 924600,0 N | 924600,0 N | **APROVADO** |

Confirma que `steel_resistance_factors` consulta a linha correta da Tabela 3 por classe de combinação: `Nt,Rd` da combinação excepcional (924600,0 N) é maior que o da combinação normal (840545,45 N) para o mesmo material/seção — coerente com os coeficientes de ponderação menores (menos conservadores) previstos para combinações excepcionais.

## Conclusão

`check_tension_member` reproduz exatamente (erro relativo 0, aritmética direta sem ponto flutuante acumulado) as fórmulas de 5.2.1.2/5.2.2 lidas diretamente da NBR 8800:2024, e `steel_resistance_factors` reproduz corretamente a Tabela 3 (4.9.2) por classe de combinação. O estado-limite governante (`governing`) e a taxa de utilização (`utilization`) foram confirmados em ambos os sentidos (escoamento e ruptura governando).

**STATUS GERAL: APROVADO**, dentro do escopo implementado.

## Limitações desta fase (não invalidam o resultado acima, delimitam seu uso)

- **Área líquida efetiva (`Ae`) não é calculada pelo software** nesta fase — apenas o caso sem furos (`An = Ag`, 5.2.4.2) tem fórmula implementada (`net_area_without_holes`); o coeficiente de redução `Ct` (5.2.3/5.2.5, que depende do tipo de ligação — soldada, parafusada, chapas, seções tubulares) fica para uma fase futura de ligações metálicas. Nos casos 1 e 3 acima, `Ct = 1` foi assumido apenas para fechar o valor numérico de `Ae` usado na validação — **não é uma regra normativa implementada**, é uma hipótese do teste.
- Não implementado nesta fase: 5.2.6 (chapas ligadas por pino), 5.2.7 (barras redondas com extremidades rosqueadas), 5.2.8 (limitação do índice de esbeltez — recomendação, não estado-limite obrigatório).
- **Fora do escopo** (fases normativas futuras): compressão (5.3), flexão e cisalhamento (5.4), combinação de esforços (5.5), qualquer verificação de ligações (seção 6), e qualquer outra norma (NBR 6120, NBR 8681).
