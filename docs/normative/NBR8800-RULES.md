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

## RULE-ID: NBR8800-TRAC-004

- **SOURCE:** NBR 8800:2024, 5.2.8.1, página 44: "Recomenda-se que o
  índice de esbeltez das barras tracionadas, considerado como a maior
  relação entre o comprimento destravado e o raio de giração
  correspondente, excetuando-se tirantes de barras redondas
  pré-tensionadas ou outras barras que tenham sido montadas com
  pré-tensão, não supere 300 (ver 5.2.8.3)."
- **DESCRIPTION:** Limitação RECOMENDADA (não estado-limite último
  obrigatório) do índice de esbeltez de uma barra tracionada
  individual: `ℓ/r ≤ 300`, tomando o maior valor entre os dois eixos
  principais. Não implementa 5.2.8.2 (requisito adicional para barras
  compostas) nem modela tirantes pré-tensionados (exceção citada no
  texto). 5.2.8.3 (responsável técnico pode estabelecer novos limites
  se a recomendação não for adotada) não é uma regra numérica —
  refletida apenas na semântica de `is_within_recommended_limit`
  (`False` não significa "reprovado").
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.slenderness.check_tension_slenderness`
  (`TENSION_SLENDERNESS_LIMIT`, `slenderness_ratio`).
- **TEST:** `tests/unit/test_nbr8800_slenderness.py`,
  `tests/validation/test_nbr8800_slenderness_benchmark.py` (VAL-0009).

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
  torno de um eixo principal de inércia. **LIMITAÇÃO DE SEGURANÇA —
  STATUS ATUALIZADO**: 5.3.5.1 exige `Ne = min(Nex, Ney, Nez)`. `Nez`
  (flambagem por torção, caso c) **agora está implementado** — ver
  `NBR8800-COMP-006`/`NBR8800-COMP-007` abaixo — completando `Ne` para
  seções com dupla simetria ou simétricas em relação a um ponto. A
  parte da limitação que **continua valendo**: seções monossimétricas/
  assimétricas (5.3.5.2/5.3.5.3, flexo-torção `Neyz` ou equação
  cúbica) ainda não são implementadas — para essas, `min(Nex, Ney,
  Nez)` NÃO é a fórmula correta (ver ATENÇÃO na docstring do módulo
  `compression.py`), e usá-la seria não conservador.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.flexural_buckling_force`.
- **TEST:** `tests/unit/test_nbr8800_compression.py`.

## RULE-ID: NBR8800-COMP-006

- **SOURCE:** NBR 8800:2024, 5.3.5.1, caso c), página 48: "para
  flambagem por torção em relação ao eixo longitudinal z (que passa
  pelo centro de cisalhamento): Nez = (1/r0²)[π²ECw/Lz² + GJ]".
- **DESCRIPTION:** Força axial de flambagem elástica por torção em
  relação ao eixo longitudinal da barra. Válida apenas para seções com
  dupla simetria ou simétricas em relação a um ponto (`x0=y0=0` em
  `r0`, ver `NBR8800-COMP-007`) — ver ATENÇÃO de segurança na
  docstring do módulo `compression.py` sobre seções monossimétricas/
  assimétricas.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.torsional_buckling_force`.
- **TEST:** `tests/unit/test_nbr8800_compression.py`,
  `tests/validation/test_nbr8800_torsional_buckling_benchmark.py`
  (VAL-0008).

## RULE-ID: NBR8800-COMP-007

- **SOURCE:** NBR 8800:2024, 5.3.5.1, página 49: "r0 é o raio de
  giração polar da seção bruta em relação ao centro de cisalhamento
  [...]: r0 = sqrt(rx²+ry²+x0²+y0²) [...] Para seções com dupla
  simetria ou simétrica em relação a um ponto, x0=y0=0."
- **DESCRIPTION:** Raio de giração polar em relação ao centro de
  cisalhamento, caso particular `x0=y0=0`: `r0 = sqrt(ry²+rz²)`. Usado
  como entrada de `Nez` (`NBR8800-COMP-006`).
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.compression.polar_radius_of_gyration`.
- **TEST:** `tests/unit/test_nbr8800_compression.py`,
  `tests/validation/test_nbr8800_torsional_buckling_benchmark.py`
  (VAL-0008).

## RULE-ID: NBR8800-COMP-008

- **SOURCE:** NBR 8800:2024, 5.3.7.1, página 52: "Recomenda-se que o
  índice de esbeltez das barras comprimidas, incluindo as barras
  compostas atuando como uma unidade, considerado como a maior relação
  entre o comprimento destravado associado à flexão e o raio de
  giração correspondente, não supere 200."
- **DESCRIPTION:** Limitação RECOMENDADA (não estado-limite último
  obrigatório) do índice de esbeltez de uma barra comprimida
  individual: `ℓ/r ≤ 200`, tomando o maior valor entre os dois eixos
  principais. Ao contrário de 5.2.8, esta cláusula não tem uma
  subseção equivalente a 5.2.8.3 (não há escape explícito para novos
  limites) — mesmo assim, `is_within_recommended_limit=False` não é
  tratado como reprovação normativa (é uma recomendação, não `Nc,Sd
  <= Nc,Rd`).
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.slenderness.check_compression_slenderness`
  (`COMPRESSION_SLENDERNESS_LIMIT`, `slenderness_ratio`).
- **TEST:** `tests/unit/test_nbr8800_slenderness.py`,
  `tests/validation/test_nbr8800_slenderness_benchmark.py` (VAL-0009).

## RULE-ID: NBR8800-SHEAR-001

- **SOURCE:** NBR 8800:2024, 5.4.1.3, página 53: "No dimensionamento
  das barras submetidas a momento fletor e força cortante, devem ser
  atendidas as seguintes condições: MSd ≤ MRd; VSd ≤ VRd".
- **DESCRIPTION:** Condição de dimensionamento ao cisalhamento:
  `Vsd ≤ Vrd`. A condição equivalente de momento fletor (`Msd ≤ Mrd`,
  5.4.2) **não é implementada nesta fase** — ver "Fora do escopo"
  abaixo.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.shear.check_shear_major_axis`
  (`ShearCheckResult.is_ok`).
- **TEST:** `tests/unit/test_nbr8800_shear.py`,
  `tests/validation/test_nbr8800_shear_benchmark.py` (VAL-0010).

## RULE-ID: NBR8800-SHEAR-002

- **SOURCE:** NBR 8800:2024, 5.4.3.1.2, página 57-58: "A força cortante
  correspondente à plastificação da alma por cisalhamento é calculada
  conforme a seguinte equação: Vpℓ = 0,60 Aw fy. Nessa equação, Aw é a
  área efetiva de cisalhamento, que deve ser considerada igual a:
  Aw = d.tw, onde d é a altura total da seção transversal; tw é a
  espessura da alma."
- **DESCRIPTION:** Força cortante correspondente à plastificação da
  alma por cisalhamento (`Vpℓ = 0,60·Aw·fy`) e área efetiva de
  cisalhamento para seções I, H e U fletidas em relação ao eixo
  perpendicular à alma (`Aw = d·tw`).
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.shear.plastic_shear_force`,
  `openstruct.normative.nbr8800.shear.effective_shear_area_major_axis`.
- **TEST:** `tests/unit/test_nbr8800_shear.py`.

## RULE-ID: NBR8800-SHEAR-003

- **SOURCE:** NBR 8800:2024, 5.4.3.1.1, página 57: "Em seções I, H e U
  fletidas em relação ao eixo central de inércia perpendicular à alma
  (eixo de maior momento de inércia), a força cortante resistente de
  cálculo, VRd, é calculada conforme a seguir: para λ ≤ λp: VRd =
  Vpℓ/γa1; para λp < λ ≤ λr: VRd = (λp/λ)(Vpℓ/γa1); para λ > λr: VRd =
  1,24(λp/λ)²(Vpℓ/γa1); onde λ = h/tw; λp = 1,10·sqrt(kv·E/fy); λr =
  1,37·sqrt(kv·E/fy); h é a altura da alma, considerada igual à
  distância entre as faces internas das mesas nos perfis soldados e
  igual a esse valor subtraindo os dois raios de concordância entre
  mesa e alma nos perfis laminados."
- **DESCRIPTION:** Força cortante resistente de cálculo `Vrd` em 3
  trechos (plastificação / flambagem inelástica / flambagem elástica
  por cisalhamento), aplicável apenas ao caso de seções I, H e U
  fletidas em relação ao eixo perpendicular à alma (eixo de maior
  momento de inércia — o caso mais comum). Nota: distinção crítica
  entre `h` (altura livre da alma, usada aqui e em `kv`) e `d` (altura
  total da seção, usada em `Aw`, NBR8800-SHEAR-002) — ver ATENÇÃO na
  docstring de `shear_buckling_coefficient`. Há uma pequena
  descontinuidade (~0,4% relativo) em `λ=λr`, pois `λr/λp =
  1,37/1,10 = 1,24545...` não é exatamente `1,24` — característica da
  fórmula empírica da norma (mesma natureza da descontinuidade de
  NBR8800-COMP-002 em `λ0=1,5`), não um erro de implementação.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.shear.shear_resistance`,
  `openstruct.normative.nbr8800.shear.check_shear_major_axis`.
- **TEST:** `tests/unit/test_nbr8800_shear.py`,
  `tests/validation/test_nbr8800_shear_benchmark.py` (VAL-0010).

## RULE-ID: NBR8800-SHEAR-004

- **SOURCE:** NBR 8800:2024, 5.4.3.1.1, página 57: "kv = 5,34, para
  almas sem enrijecedores transversais e para a/h > 3; kv = 5,0 +
  5/(a/h)², para todos os outros casos [...] a é a distância entre as
  linhas de centro de dois enrijecedores transversais adjacentes."
- **DESCRIPTION:** Coeficiente de flambagem por cisalhamento `kv`,
  usado em `λp`/`λr` (NBR8800-SHEAR-003). Não implementa 5.4.3.1.3
  (requisitos construtivos para dimensionamento dos próprios
  enrijecedores transversais — a distância `a` é recebida como
  parâmetro, não verificada/dimensionada).
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.shear.shear_buckling_coefficient`.
- **TEST:** `tests/unit/test_nbr8800_shear.py`.

## RULE-ID: NBR8800-FLEX-001

- **SOURCE:** NBR 8800:2024, 5.4.1.3, página 53 (condição
  `MSd ≤ MRd`, já registrada em `NBR8800-SHEAR-001`) e 5.4.2.1, página
  54: "O momento fletor resistente de cálculo, MRd, deve ser
  determinado de acordo com os Anexos D ou E, o que for aplicável
  [...] Devem ser considerados, conforme o caso, os estados-limite
  últimos de flambagem lateral com torção (FLT), flambagem local da
  mesa comprimida (FLM), flambagem local da alma (FLA), flambagem
  local da aba, flambagem local da parede do tubo e escoamento da mesa
  tracionada."
- **DESCRIPTION:** Condição de dimensionamento ao momento fletor,
  `Msd ≤ Mrd`, onde `Mrd` deve ser o MENOR valor entre todos os
  estados-limite aplicáveis à seção (mesmo princípio de
  `Ne=min(Nex,Ney,Nez)` em `NBR8800-COMP-005`). **LIMITAÇÃO DE
  SEGURANÇA**: apenas FLT está implementado nesta fase — ver
  `NBR8800-FLEX-004`.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.flexure.check_lateral_torsional_buckling`
  (`FlexureCheckResult.is_ok`).
- **TEST:** `tests/unit/test_nbr8800_flexure.py`,
  `tests/validation/test_nbr8800_flexure_benchmark.py` (VAL-0011).

## RULE-ID: NBR8800-FLEX-002

- **SOURCE:** NBR 8800:2024, 5.4.2.3-a, página 54: "em todos os casos,
  excluindo os descritos em 5.4.2.3-b) e 5.4.2.3-c): Cb = 12,5*Mmax /
  (2,5*Mmax + 3*MA + 4*MB + 3*MC) * Rm [...] Rm [é] 1,0 para todas as
  seções duplamente simétricas, para seções I com um eixo de simetria,
  fletidas em relação ao eixo que não é de simetria, submetidas à
  curvatura simples, e seções U, fletidas em relação ao eixo de
  simetria."
- **DESCRIPTION:** Fator de modificação para diagrama de momento
  fletor não uniforme, `Cb`, caso geral (`Rm=1,0`, único caso coberto
  — a fórmula de `Rm` para seções monossimétricas com curvatura
  reversa, `0,5+2*(Iy,m/Iy)²`, não está implementada). Não implementa
  5.4.2.3-b)/c) (balanços) nem 5.4.2.4/5.4.2.5 (fórmulas alternativas
  de `Cb` para seções I/U com uma mesa livre para se deslocar
  lateralmente).
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.flexure.moment_gradient_factor_doubly_symmetric`.
- **TEST:** `tests/unit/test_nbr8800_flexure.py`.

## RULE-ID: NBR8800-FLEX-003

- **SOURCE:** NBR 8800:2024, Anexo D, Tabela D.1 (primeira linha,
  coluna FLT) e D.2.8-a, páginas 144-145: "λr = (1,38*Cb*sqrt(Iy*J) /
  (ry*J*β1)) * sqrt(1 + sqrt(1 + 27*Cw*β1²/(Cb²*Iy))); Mcr =
  (Cb*π²*E*Iy/Lb²) * sqrt((Cw/Iy)*(1 + 0,039*J*Lb²/Cw)); onde β1 =
  (fy-σr)*W/(E*J)"; e página 146, item e): "A tensão residual de
  compressão nas mesas, σr, deve ser considerada igual a 30% da
  resistência ao escoamento do aço utilizado."
- **DESCRIPTION:** Momento fletor crítico de flambagem elástica por
  FLT (`Mcr`), parâmetro de esbeltez correspondente ao início do
  escoamento (`λr`) e momento fletor de plastificação/momento
  correspondente ao início do escoamento (`Mpl=fy*Z`,
  `Mr=(fy-0,3*fy)*W`), para seções I, H com dois eixos de simetria e
  seções U não sujeitas a momento de torção, fletidas em relação ao
  eixo de maior momento de inércia (Tabela D.1, primeira linha) —
  `λp=1,76*sqrt(E/fy)` (D.2.1). Curva de 3 trechos de `Mrd` conforme
  D.2.1 (mesma estrutura conceitual de `NBR8800-SHEAR-003`), com uma
  pequena descontinuidade (~0,18% relativo) em `λ=λr` documentada no
  código (mesma natureza das descontinuidades já registradas em
  `NBR8800-COMP-002`/`NBR8800-SHEAR-003`). Também implementa
  `Cw=Iy*(d-tf)²/4` para seções I (D.2.8-a), útil quando `Section.Cw`
  não está disponível.
- **IMPLEMENTATION:**
  `openstruct.normative.nbr8800.flexure.lateral_torsional_buckling_moment`,
  `openstruct.normative.nbr8800.flexure.lateral_torsional_buckling_slenderness_limit`,
  `openstruct.normative.nbr8800.flexure.flexural_resistance`,
  `openstruct.normative.nbr8800.flexure.warping_constant_i_section`,
  `openstruct.normative.nbr8800.flexure.check_lateral_torsional_buckling`.
- **TEST:** `tests/unit/test_nbr8800_flexure.py`,
  `tests/validation/test_nbr8800_flexure_benchmark.py` (VAL-0011).

## RULE-ID: NBR8800-FLEX-004

- **SOURCE:** NBR 8800:2024, 5.4.2.1, página 54 (ver `NBR8800-FLEX-001`).
- **DESCRIPTION:** **LIMITAÇÃO DE SEGURANÇA IMPORTANTE**: 5.4.2.1 exige
  que `Mrd` considere, conforme o caso, TODOS os estados-limite
  aplicáveis (FLT, FLM, FLA, flambagem local da aba, flambagem local
  da parede do tubo, escoamento da mesa tracionada), tomando o MENOR
  valor entre os que se aplicam. Esta fase implementa **apenas FLT**
  (`NBR8800-FLEX-001/002/003`). Para uma seção real, se FLM ou FLA
  governar (típico de mesas ou almas muito esbeltas), o `Mrd` retornado
  por `check_lateral_torsional_buckling` seria NÃO CONSERVADOR se
  tratado como o `Mrd` completo da barra — deve ser interpretado
  apenas como a parcela de FLT. Também não implementado: 5.4.2.2
  (limite `Mrd ≤ 1,50*W*fy/γa1` para garantir validade da análise
  elástica — a ser aplicado pelo chamador ao `Mrd` GOVERNANTE final,
  quando FLM/FLA existirem) e 5.4.2.6 (furos na mesa tracionada).
- **IMPLEMENTATION:** N/A (limitação documentada, não uma regra
  implementada) — ver docstring do módulo
  `openstruct.normative.nbr8800.flexure`.
- **TEST:** N/A.

**Nota adicional (achado do CODE REVIEW AGENT):** `FlexureCheckResult.is_ok`/`utilization`
(herdados de `CheckResult`) comparam `msd` diretamente contra `mrd`
(sempre positivo), sem valor absoluto — a condição normativa de
5.4.1.3 é sobre a MAGNITUDE do momento (`|Msd|<=Mrd`). Um `msd`
negativo grande (momento no sentido oposto, comum em vigas contínuas
ou combinações com inversão de sinal) faria `is_ok` retornar `True` de
forma NÃO CONSERVADORA. **O chamador é responsável por passar
`abs(msd)`** — mesma responsabilidade já documentada para `Vsd` em
`ShearCheckResult` (ver docstring de `FlexureCheckResult` e teste
`test_flexure_check_result_is_ok_ignores_sign_caller_must_pass_magnitude`).

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
- **5.2.8.2** (página 44): requisito adicional de esbeltez para barras
  COMPOSTAS tracionadas (`ℓ/rmin` de cada perfil componente entre
  ligações adjacentes). A verificação de 5.2.8.1 para barra individual
  já está implementada (`NBR8800-TRAC-004`) — falta a modelagem de
  barras compostas em si (múltiplos perfis com ligações
  intermediárias).
- **5.3.4.2/5.3.4.3** (página 46-48): área efetiva reduzida por
  flambagem local (larguras efetivas, Tabela 4 de `(b/t)lim` por grupo
  de elemento AA/AL, Tabela 5 de fatores `c1`/`c2`). Requer
  classificação de cada elemento da seção (alma, mesa, aba de
  cantoneira etc.) em um grupo da Tabela 4 e sua razão `b/t`, que
  `Section` não expressa (armazena apenas propriedades agregadas da
  seção — `A`, `Iy`, `Iz`, etc. — não a geometria detalhada de cada
  elemento).
- **5.3.5.2/5.3.5.3** (página 49): flambagem por flexo-torção em seções
  monossimétricas (`Neyz`) e a equação cúbica de seções assimétricas.
  `Nez` (5.3.5.1-c) em si já está implementado (`NBR8800-COMP-006`) —
  o que falta é a combinação não linear de `Ney`/`Nez` com a
  excentricidade do centro de cisalhamento (`x0`/`y0` não nulos nesses
  casos), que `polar_radius_of_gyration` desta fase não calcula (só o
  caso `x0=y0=0`). A LIMITAÇÃO DE SEGURANÇA registrada em
  NBR8800-COMP-005 continua valendo para esses dois casos.
- **5.3.5.4** (página 50-51): comprimento destravado equivalente para
  cantoneiras simples conectadas por uma aba.
- **5.3.6** (página 51-52): requisitos específicos para barras
  compostas (perfis múltiplos trabalhando em conjunto).
- **5.4.2.2** (página 54): limite `Mrd ≤ 1,50*W*fy/γa1` para garantir
  validade da análise elástica — deve ser aplicado ao `Mrd` GOVERNANTE
  final (mínimo entre FLT/FLM/FLA/etc.), não implementado ainda porque
  só FLT está implementado (ver `NBR8800-FLEX-004`).
- **5.4.2.3-b)/c), 5.4.2.4, 5.4.2.5** (páginas 54-55): `Cb` para
  balanços e para seções I/U com uma mesa livre para se deslocar
  lateralmente — apenas o caso geral duplamente simétrico (5.4.2.3-a)
  está implementado (`NBR8800-FLEX-002`).
- **5.4.2.6** (página 55): dimensionamento ao momento fletor com furos
  na mesa tracionada.
- **Anexo D, demais linhas da Tabela D.1** (páginas 137-146): FLM e FLA
  para seções I/H/U duplamente simétricas (mesma linha da Tabela D.1
  cujo FLT já está implementado — ver LIMITAÇÃO DE SEGURANÇA em
  `NBR8800-FLEX-004`), seções I/H monossimétricas, seções I/H/U
  fletidas no eixo de menor momento de inércia, seções-caixão/
  tubulares retangulares, seções T, cantoneiras duplas e seções
  sólidas circulares/retangulares.
- **Anexo E** (páginas 148-151): momento fletor resistente de cálculo
  de vigas de ALMA ESBELTA — substitui o Anexo D inteiramente quando a
  seção não satisfaz D.1.2 (`λ` da alma para FLA maior que `λr`), um
  requisito de aplicabilidade que `check_lateral_torsional_buckling`
  não verifica (responsabilidade do chamador nesta fase).
- **Anexos F, G, H, I**: aberturas em almas de vigas, barras de seção
  variável, fadiga e vibrações em pisos, respectivamente.
- **5.4.3.2 a 5.4.3.6** (páginas 58-60): força cortante resistente
  para seções tubulares/caixão, T, cantoneiras duplas, I/H/U fletidas
  em torno do eixo fraco, e tubulares circulares — mesma estrutura de
  fórmula de 5.4.3.1 (`NBR8800-SHEAR-002/003`), com `kv`/área efetiva
  de cisalhamento diferentes.
- **5.4.3.1.3** (página 58): requisitos construtivos para
  dimensionamento dos próprios enrijecedores transversais (ver
  `NBR8800-SHEAR-004`).
- **5.4.4/5.4.5**: chapas de reforço/lamelas e requisitos para seções
  soldadas.
- **5.5**: combinação de momento fletor, força cortante, força axial e
  momento de torção — próximo incremento desta mesma fase normativa,
  apos FLM/FLA fecharem a limitação de `NBR8800-FLEX-004`.
