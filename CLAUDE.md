# Instruções para o Claude Code neste repositório

Este arquivo é lido automaticamente no início de qualquer sessão do
Claude Code neste repositório — é o ponto de entrada rápido. A
especificação completa está em dois documentos que **sempre** devem
ser lidos antes de qualquer trabalho estrutural:

- **`AGENTS_MASTER.md`** — sistema multiagente de desenvolvimento
  (define os agentes, o pipeline obrigatório e as regras contra
  alucinação/afirmações não verificadas).
- **`PROGRAM_MASTER.md`** — especificação completa do programa
  OpenStruct 3D (fases, marcos, escopo de cada uma).

Ver também `README.md` para o estado atual implementado e
`docs/decisions/ADR-*.md`/`docs/validation/VAL-*.md` para decisões de
arquitetura e registros de validação estrutural já concluídos.

## Pipeline obrigatório

Nenhuma funcionalidade estrutural é considerada concluída sem passar
por (ver `AGENTS_MASTER.md` para o detalhe de cada agente):

```
SOLVER AGENT → TEST AGENT → STRUCTURAL VALIDATION AGENT
             → CODE REVIEW AGENT → ENGINEERING QA AGENT → ORCHESTRATOR
```

Nunca afirmar "implementado", "validado" ou "conforme NBR" sem ter
efetivamente rodado o teste/validação correspondente — evidência
numérica real, não presumida.

## Escopo

Seguir estritamente as fases já abertas pelo usuário. Não implementar
adiantado: GUI, IA, P-Delta, flambagem, módulos normativos (incluindo
NBR 8800) ou dimensionamento, a menos que explicitamente solicitado.
Não inventar requisitos normativos ou referências técnicas.

## Política de merge de Pull Requests

Este é um projeto de **manutenção solo** (um único desenvolvedor, sem
outros revisores humanos no fluxo normal). Para não exigir que o
usuário volte ao repositório apenas para clicar em "merge":

- Em um PR aberto **pelo próprio Claude Code** (branch `claude/...`),
  uma vez que o CI esteja **verde** (`pytest + ruff + mypy` com
  sucesso) e o PR esteja **mergeable** (`mergeable_state: clean`, sem
  conflito), **mesclar o PR automaticamente** (`merge_pull_request`,
  método `merge` — mantendo o histórico de merge commits já usado nos
  PRs anteriores deste repositório) sem esperar aprovação manual.
- Isso vale para o fluxo normal de features seguindo o pipeline acima
  (código + testes + validação + code review + QA já executados antes
  do PR ser aberto). Se o CI falhar, ou se o code review encontrar algo
  que exija uma decisão de escopo/arquitetura do usuário, **não
  mesclar** — corrigir e só mesclar depois de verde, ou perguntar se a
  decisão for genuinamente do usuário.
- Depois de mesclar, sincronizar a branch local `main`
  (`git pull --ff-only`) antes de iniciar a próxima branch de feature.

## Pastas ainda não usadas neste projeto

Este repositório ainda não tem pastas de `kb/` (base de conhecimento
normativa) ou `relatorios/` (motor de relatórios) — elas pertencem a
fases futuras do `PROGRAM_MASTER.md` (NORMATIVE ENGINE, REPORT ENGINE)
ainda não abertas. Não criar essas pastas vazias antecipadamente;
criá-las quando a fase correspondente for de fato iniciada.
