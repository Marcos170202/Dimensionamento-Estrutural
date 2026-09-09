# Rastreabilidade de regras — ABNT NBR 8800:2024

Registro obrigatório de toda regra normativa implementada em
`openstruct.normative.nbr8800` (AGENTS_MASTER.md seção 13,
`.claude/agents/normative.md`). Cada entrada segue o formato:

```
RULE-ID:
SOURCE:
DESCRIPTION:
IMPLEMENTATION:
TEST:
```

Fonte de todas as regras abaixo: PDF `NBR 8800 - 2024 - Projeto de
Estruturas de Aço e de Estruturas Mistas de Aço e Concreto de
Edifícios.pdf`, fornecido pelo usuário e já presente na raiz do
repositório (terceira edição, 02.10.2024). Nenhum valor ou fórmula
abaixo foi obtido de memória/treinamento — todos foram extraídos por
leitura direta das páginas citadas (renderização visual das páginas do
PDF, não apenas extração de texto bruto, para evitar erros de
glifo/fonte — ver nota sobre `Ct` abaixo).

## RULE-ID: NBR8800-RES-001

- **SOURCE:** NBR 8800:2024, 4.9.2 "Coeficientes de ponderação das
  resistências no estado-limite último (ELU)", Tabela 3 "Valores dos
  coeficientes de ponderação das resistências dos materiais γm",
  página 25.
- **DESCRIPTION:** Coeficientes de ponderação da resistência do aço
  estrutural, γa1 (escoamento e instabilidade) e γa2 (ruptura), por
  classe de combinação última de ações:
  - Normais: γa1 = 1,10; γa2 = 1,35.
  - Especiais ou de construção: γa1 = 1,10; γa2 = 1,35.
  - Excepcionais: γa1 = 1,00; γa2 = 1,15.

  Escopo: apenas a coluna "Aço estrutural" da Tabela 3. As colunas de
  concreto (γc) e aço das armaduras (γs) não são implementadas — sem
  elementos mistos nesta fase.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.resistance_factors.steel_resistance_factors`
  (`LoadCombinationClass`, `SteelResistanceFactors`).
- **TEST:** `tests/unit/test_nbr8800_resistance_factors.py`.

## RULE-ID: NBR8800-TRAC-001

- **SOURCE:** NBR 8800:2024, 5.2.1.2 "No dimensionamento, deve ser
  atendida a condição: Nt,Sd ≤ Nt,Rd" e 5.2.2 "Força axial resistente
  de cálculo", caso a) "para escoamento da seção bruta", página 39.
- **DESCRIPTION:** Força axial de tração resistente de cálculo por
  escoamento da seção bruta: `Nt,Rd = Ag·fy / γa1`. A condição de
  dimensionamento exige `Nt,Sd ≤ Nt,Rd` (o menor entre este valor e o
  de NBR8800-TRAC-002).
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.tension.check_tension_member`
  (`TensionCheckResult.nt_rd_yield`, `TensionCheckResult.is_ok`).
- **TEST:** `tests/unit/test_nbr8800_tension.py`,
  `tests/validation/test_nbr8800_tension_benchmark.py` (VAL-0006).

## RULE-ID: NBR8800-TRAC-002

- **SOURCE:** NBR 8800:2024, 5.2.2 "Força axial resistente de
  cálculo", caso b) "para ruptura da seção líquida", página 39.
- **DESCRIPTION:** Força axial de tração resistente de cálculo por
  ruptura da seção líquida: `Nt,Rd = Ae·fu / γa2`, onde `Ae` é a área
  líquida efetiva (5.2.3: `Ae = Ct·An`).
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.tension.check_tension_member`
  (`TensionCheckResult.nt_rd_rupture`).
- **TEST:** `tests/unit/test_nbr8800_tension.py`,
  `tests/validation/test_nbr8800_tension_benchmark.py` (VAL-0006).

## RULE-ID: NBR8800-TRAC-003

- **SOURCE:** NBR 8800:2024, 5.2.4.2 "Em regiões em que não existam
  furos, a área líquida, An, deve ser considerada igual à área bruta
  da seção transversal, Ag", página 40.
- **DESCRIPTION:** Caso particular (sem furos) da área líquida usada
  em NBR8800-TRAC-002: `An = Ag`.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.tension.net_area_without_holes`.
- **TEST:** `tests/unit/test_nbr8800_tension.py`.

## Fora do escopo desta fase (não implementado)

Registrado aqui para rastreabilidade do que foi conscientemente
adiado, não esquecido:

- **5.2.3/5.2.5** (página 39-42): cálculo do coeficiente de redução da
  área líquida `Ct` para os casos gerais (ligações parafusadas,
  soldadas, chapas, seções tubulares). Requer modelagem de furos/
  soldas/parafusos que o domínio geométrico atual (`Section`) não
  expressa — fica para quando a fase de ligações (`PROGRAM_MASTER.md`
  seção 6, "Condições específicas para o dimensionamento de ligações
  metálicas") for aberta.

  **Nota de leitura:** o texto extraído da página 40 (5.2.5-a) mostra
  literalmente `Ct = 100`, o que fisicamente não pode estar correto
  para um "coeficiente de redução" (deveria ser ≤ 1). O aviso do
  próprio extrator de texto (`pypdf`) aponta uma fonte customizada
  (`KGXUMD+MyriadPro-Regular`) cuja codificação não é totalmente
  suportada sem a biblioteca `fontTools` — é quase certo que se trata
  de um artefato de renderização da vírgula decimal brasileira
  (`1,00` → `100`), não um valor real da norma. Como este caso (a) não
  é implementado nesta fase, o valor não entrou em nenhum código; esta
  nota existe apenas para não perder o achado ao retomar 5.2.5 no
  futuro — a interpretação (`Ct = 1,00`) deve ser reconfirmada contra
  o texto oficial antes de implementar.
- **5.2.6** (página 43): chapas ligadas por pino.
- **5.2.7** (página 44): barras redondas com extremidades rosqueadas.
- **5.2.8** (página 44): limitação do índice de esbeltez (`ℓ/r ≤ 300`)
  — é uma recomendação ("recomenda-se"), não um estado-limite último
  obrigatório, e depende de `Section` expor raio de giração (ainda não
  implementado).
- **5.3 em diante**: compressão, flexão, cisalhamento, combinação de
  esforços — próximos incrementos desta mesma fase normativa.
