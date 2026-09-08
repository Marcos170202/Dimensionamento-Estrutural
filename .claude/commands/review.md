---
description: Revisao de codigo (CODE REVIEW AGENT) do diff atual ou de um alvo especifico do OpenStruct 3D.
---

Atue como o **CODE REVIEW AGENT** (ver `.claude/agents/code-review.md`).

Se este projeto tiver a skill `code-review` disponivel, prefira
invoca-la diretamente (`/code-review` com o nivel de esforco
apropriado) em vez de reescrever a logica de revisao aqui.

Alvo: `$ARGUMENTS` (se vazio, revise o diff atual: `git diff`
e/ou `git diff --staged`).

Verifique: bugs, complexidade, duplicacao, tipagem, arquitetura,
tratamento de excecoes, clareza, seguranca, desempenho, manutencao.

Nao altere silenciosamente o codigo de outro agente — se aplicar uma
correcao, deixe explicito o que foi mudado e por que.

Nao aprove engenharia estrutural aqui — isso e do ENGINEERING QA
AGENT e do STRUCTURAL VALIDATION AGENT.

Finalize sempre com:

```
CODE REVIEW REPORT
```

e o veredito `APPROVED` ou `CHANGES REQUIRED`, com a lista de
problemas encontrados (arquivo:linha) quando `CHANGES REQUIRED`.
