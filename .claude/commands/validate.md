---
description: Executa a validacao estrutural (STRUCTURAL VALIDATION AGENT) de um componente contra referencia analitica/benchmark.
---

Atue como o **STRUCTURAL VALIDATION AGENT** (ver
`.claude/agents/validation.md`).

Alvo desta validacao: `$ARGUMENTS` (se vazio, valide os componentes
do core estrutural que ainda nao tenham um `docs/validation/VAL-*.md`
correspondente, ou re-execute os existentes).

1. Identifique a referencia correta: solucao analitica fechada,
   exemplo de livro-texto, benchmark publicado ou resultado
   previamente validado. **Nunca invente uma referencia** — se nao
   houver uma disponivel, diga isso explicitamente em vez de aprovar.
2. Execute a comparacao numerica de fato
   (`.venv/bin/python -m pytest tests/validation -v`, ou escreva um
   novo teste em `tests/validation/` se o caso ainda nao existir).
3. Para cada caso, registre:

   ```
   PROBLEMA
   REFERENCIA
   HIPOTESES
   RESULTADO DE REFERENCIA
   RESULTADO DO OPENSTRUCT
   ERRO ABSOLUTO
   ERRO RELATIVO
   TOLERANCIA
   STATUS (APROVADO / REPROVADO)
   ```

4. Escreva ou atualize `docs/validation/VAL-XXXX-<slug>.md` com o
   resultado (use o proximo numero VAL- disponivel).
5. Se REPROVADO em qualquer caso, **nao aprove** — reporte ao SOLVER
   AGENT com o erro medido e pare.

Nunca aprove um resultado apenas porque "parece razoavel"
(AGENTS_MASTER.md secao 7).
