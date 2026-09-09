"""Modulos normativos (PROGRAM_MASTER.md secao 18, "NORMATIVE"; marco
"NORMATIVE ENGINE", secao 30).

Arquitetura de plugin: nenhuma regra normativa e inserida no
`domain`/`analysis`/`solver`/`results` (o nucleo de calculo permanece
agnostico de norma, ver `.claude/agents/normative.md` e ADR-002). Cada
norma vive em seu proprio subpacote (ex.: `normative.nbr8800`),
analogo ao `NormativePlugin`/`NBR8800Plugin` citado no PROGRAM_MASTER.

Toda regra normativa implementada aqui tem rastreabilidade obrigatoria
(RULE-ID/SOURCE/DESCRIPTION/IMPLEMENTATION/TEST) documentada em
``docs/normative/NBR8800-RULES.md`` — ver AGENTS_MASTER.md secao 13 e
`.claude/agents/normative.md`. Regra inviolavel: nenhum requisito
normativo e inventado; todo valor/formula vem de leitura direta do
documento normativo fornecido pelo usuario (o PDF da ABNT NBR
8800:2024 na raiz do repositorio).
"""

from __future__ import annotations
