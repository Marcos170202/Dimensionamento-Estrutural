---
description: Prepara uma release do OpenStruct 3D (RELEASE AGENT) — testes finais, versao e changelog.
---

Atue como o **RELEASE AGENT** (ver `.claude/agents/release.md`).

1. Rode a suite de testes completa e confirme `PASS` de fato
   (`.venv/bin/python -m pytest -v`) — nunca declare uma release
   pronta sem essa execucao.
2. Confirme a versao em `pyproject.toml` (`[project].version`) e
   decida o proximo numero de versao (semver) com base no que mudou
   desde a ultima release (`git log`/`git tag`).
3. Atualize ou crie um `CHANGELOG.md` na raiz do repositorio,
   descrevendo o que foi entregue nesta versao em termos de
   funcionalidade (nao de commits individuais).
4. **Nao** gere o executavel (`OpenStruct3D.exe`) nesta fase a menos
   que explicitamente solicitado e que a GUI (PySide6) ja exista —
   empacotamento e um marco posterior ao "SEGUNDO MARCO" do
   PROGRAM_MASTER.md.
5. Reporte o estado final: versao, testes (passou/falhou com
   numeros reais), o que ficou de fora do escopo desta release.
