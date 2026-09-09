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

## RULE-ID: NBR8800-COMP-001

- **SOURCE:** NBR 8800:2024, 5.3.1 "No dimensionamento dessas barras,
  deve ser atendida a condição: Nc,Sd ≤ Nc,Rd" e 5.3.2 "Força axial
  resistente de cálculo", página 45.
- **DESCRIPTION:** Força axial de compressão resistente de cálculo,
  associada aos estados-limite últimos de instabilidade (por flexão,
  torção ou flexo-torção) e de instabilidade local:
  `Nc,Rd = χ·Aef·fy / γa1`. A condição de dimensionamento exige
  `Nc,Sd ≤ Nc,Rd`.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.check_compression_member`
  (`CompressionCheckResult.nc_rd`, `CompressionCheckResult.is_ok`).
- **TEST:** `tests/unit/test_nbr8800_compression.py`,
  `tests/validation/test_nbr8800_compression_benchmark.py` (VAL-0007).

## RULE-ID: NBR8800-COMP-002

- **SOURCE:** NBR 8800:2024, 5.3.3.1 "Fator de redução χ", página 45.
- **DESCRIPTION:** Fator de redução associado à resistência à
  compressão: `χ = 0,658^(λ0²)` para `λ0 ≤ 1,5`; `χ = 0,877/λ0²` para
  `λ0 > 1,5`.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.reduction_factor`.
- **TEST:** `tests/unit/test_nbr8800_compression.py`.

## RULE-ID: NBR8800-COMP-003

- **SOURCE:** NBR 8800:2024, 5.3.3.2, página 45.
- **DESCRIPTION:** Índice de esbeltez reduzido: `λ0 = sqrt(Ag·fy/Ne)`.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.slenderness_parameter`.
- **TEST:** `tests/unit/test_nbr8800_compression.py`.

## RULE-ID: NBR8800-COMP-004

- **SOURCE:** NBR 8800:2024, 5.3.4.1, página 46: "A área efetiva da
  seção transversal, Aef, deve ser considerada igual à área bruta, Ag,
  se todos os elementos componentes da seção transversal possuírem
  relação entre largura e espessura (b/t) igual ou inferior ao valor
  (b/t)lim, dado na Tabela 4."
- **DESCRIPTION:** Caso particular (sem flambagem local) da área
  efetiva usada em NBR8800-COMP-001: `Aef = Ag`.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.effective_area_without_local_buckling`.
- **TEST:** `tests/unit/test_nbr8800_compression.py`.

## RULE-ID: NBR8800-COMP-005

- **SOURCE:** NBR 8800:2024, 5.3.5.1 "Seções com dupla simetria ou
  simétricas em relação a um ponto", casos a) e b), página 48: "para
  flambagem por flexão em relação ao eixo central de inércia x [...]:
  Nex = π²EIx/Lx²" (e analogamente para o eixo y, `Ney`).
- **DESCRIPTION:** Força axial de flambagem elástica por flexão em
  torno de um eixo principal de inércia. **LIMITAÇÃO DE SEGURANÇA
  REGISTRADA**: 5.3.5.1 exige `Ne = min(Nex, Ney, Nez)`, onde `Nez`
  (flambagem por torção, caso c) não é implementado nesta fase — requer
  a constante de empenamento `Cw`, ainda não exposta por `Section`.
  Seções monossimétricas/assimétricas (5.3.5.2/5.3.5.3, flexo-torção)
  também não são implementadas. Usar apenas `min(Nex, Ney)` como `Ne`
  é seguro somente quando torção/flexo-torção não governam (seções
  fechadas, ou I/H com dupla simetria e travamento lateral adequado);
  para seções abertas de parede fina onde esses modos podem governar,
  o chamador deve calcular `Nez`/`Neyz` externamente e incluir no
  mínimo antes de usar `check_compression_member` — ver ATENÇÃO na
  docstring do módulo `compression.py`.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.flexural_buckling_force`.
- **TEST:** `tests/unit/test_nbr8800_compression.py`.

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
- **5.3.4.2/5.3.4.3** (página 46-48): área efetiva reduzida por
  flambagem local (larguras efetivas, Tabela 4 de `(b/t)lim` por grupo
  de elemento AA/AL, Tabela 5 de fatores `c1`/`c2`). Requer
  classificação de cada elemento da seção (alma, mesa, aba de
  cantoneira etc.) em um grupo da Tabela 4 e sua razão `b/t`, que
  `Section` não expressa (armazena apenas propriedades agregadas da
  seção — `A`, `Iy`, `Iz`, etc. — não a geometria detalhada de cada
  elemento).
- **5.3.5.1-c)/5.3.5.2/5.3.5.3** (página 48-49): flambagem por torção
  e flexo-torção. Requer a constante de empenamento `Cw` da seção
  (ainda não exposta por `Section`) — ver LIMITAÇÃO DE SEGURANÇA
  registrada em NBR8800-COMP-005 acima.
- **5.3.5.4** (página 50-51): comprimento destravado equivalente para
  cantoneiras simples conectadas por uma aba.
- **5.3.6** (página 51-52): requisitos específicos para barras
  compostas (perfis múltiplos trabalhando em conjunto).
- **5.3.7** (página 52): limitação do índice de esbeltez de barras
  comprimidas (`ℓ/r ≤ 200`) — mesmo status de 5.2.8 (recomendação, não
  estado-limite obrigatório; depende de `Section` expor raio de
  giração).
- **5.4 em diante**: flexão, cisalhamento, combinação de esforços —
  próximos incrementos desta mesma fase normativa.
