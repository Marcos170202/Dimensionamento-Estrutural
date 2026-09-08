---
description: Executa a suite de testes do OpenStruct 3D (TEST AGENT) e reporta o resultado real.
---

Atue como o **TEST AGENT** (ver `.claude/agents/testing.md`).

1. Execute a suite de testes completa: `.venv/bin/python -m pytest -v`
   (ajuste o caminho do interpretador se o venv estiver em outro
   lugar; nunca presuma o resultado sem executar).
2. Se `$ARGUMENTS` especificar um caminho, arquivo ou marcador
   (`-k`, `-m`), rode apenas esse subconjunto, mas deixe claro no
   relatorio que foi um subconjunto.
3. Rode tambem com cobertura: `.venv/bin/python -m pytest --cov=openstruct --cov-report=term-missing`.
4. Reporte, colando a saida real:
   - quantos testes rodaram, quantos passaram, quantos falharam;
   - cobertura por modulo;
   - para cada falha: o traceback completo, nao um resumo.
5. Se algo falhar, NAO conclua a tarefa como concluida — aponte a
   falha ao SOLVER AGENT (ou ao agente responsavel pelo arquivo) e
   pare, aguardando correcao.

Nunca afirme "todos os testes passam" sem ter executado o comando
nesta sessao (AGENTS_MASTER.md secao 26).
