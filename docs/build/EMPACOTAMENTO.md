# Empacotamento do executável desktop (`openstruct3d-gui`)

Ver `docs/decisions/ADR-003-gui-arquitetura.md` para o contexto da
decisão de empacotar via PyInstaller.

## ⚠ LIMITAÇÃO DE PLATAFORMA — leia antes de gerar o `.exe`

**O PyInstaller NÃO faz cross-compilation.** Ele empacota o Python e
as bibliotecas nativas *da máquina onde é executado* — não existe
opção de "gerar um `.exe` Windows a partir de um Linux" (nem
vice-versa). Isso significa:

| Você quer gerar... | Precisa rodar o PyInstaller em... |
|---|---|
| `openstruct3d-gui.exe` (Windows) | uma máquina/runner **Windows** |
| `openstruct3d-gui` (Linux ELF) | uma máquina/runner **Linux** |
| `openstruct3d-gui.app` (macOS) | uma máquina/runner **macOS** |

O `.spec` (`packaging/openstruct3d-gui.spec`) é **o mesmo arquivo**
nos três casos — só muda o sistema operacional onde `pyinstaller
packaging/openstruct3d-gui.spec` é executado.

Este ambiente de desenvolvimento (sandbox Linux) só pode gerar e
validar o binário **Linux**. O `.exe` Windows é gerado automaticamente
por CI (runner `windows-latest`, ver "Build automático (CI)" abaixo) —
não é necessário rodar o PyInstaller manualmente para obter o `.exe`
de distribuição.

## 📥 Baixar o `.exe` mais recente

**Link fixo, sempre a versão mais atual gerada a partir de `main`:**

👉 https://github.com/Marcos170202/dimensionamento-estrutural/releases/tag/openstruct3d-gui-latest

Baixe `openstruct3d-gui.exe`, salve em qualquer pasta e execute — não
precisa instalar Python nem nenhuma dependência. Esse Release é
**substituído automaticamente** (mesma URL, novo arquivo) a cada push
em `main` que toque `src/openstruct/**`, `packaging/**` ou
`pyproject.toml` (ver `.github/workflows/build-gui-exe.yml`) — basta
voltar a esse link depois de cada atualização para pegar a versão mais
nova. A data/hora do Release e a nota de descrição mostram de qual
commit e versão (`openstruct.__version__`) ele foi gerado.

## Build local

```bash
# a partir da raiz do repositorio
pip install -e ".[gui,build]"
pyinstaller packaging/openstruct3d-gui.spec
```

Gera:
- Linux: `dist/openstruct3d-gui` (executável ELF, `chmod +x` já
  aplicado pelo PyInstaller).
- Windows: `dist/openstruct3d-gui.exe`.
- macOS: `dist/openstruct3d-gui`.

O executável é **onefile** (todo o Python + PySide6/Qt + numpy/scipy
embutidos em um único arquivo) — não precisa de Python instalado na
máquina de destino, mas o primeiro início é mais lento (descompacta
para um diretório temporário antes de rodar).

### Por que `packaging/entrypoint.py` em vez de `src/openstruct/gui/app.py` diretamente?

`app.py` usa import relativo (`from .main_window import MainWindow`),
o que só funciona quando o módulo é importado como parte do pacote
`openstruct.gui`. O PyInstaller roda o script passado a `Analysis()`
como módulo `__main__` de top-level (sem pacote), e isso quebra
imports relativos com `ImportError: attempted relative import with no
known parent package` (erro reproduzido e corrigido nesta fase).
`packaging/entrypoint.py` existe só para dar ao PyInstaller um ponto
de entrada que importa `openstruct.gui.app` do jeito normal (absoluto,
como pacote) antes de chamar `main()` — não duplica nenhuma lógica da
GUI.

## Verificação feita nesta fase (sandbox Linux)

Build e execução testados manualmente neste ambiente (não faz parte
da suíte automatizada — requer um binário já compilado, que não é
versionado no git):

```bash
pyinstaller packaging/openstruct3d-gui.spec --distpath packaging/dist --workpath packaging/build --noconfirm
QT_QPA_PLATFORM=offscreen ./packaging/dist/openstruct3d-gui
```

Resultado: build concluído sem erros (apenas avisos esperados sobre
bibliotecas X11 do sistema — `libxcb-*`/`libxkbcommon-x11` —
irrelevantes em modo `offscreen`, necessárias só para exibir em um
display X11 real); o executável inicia e permanece rodando sem crash
até ser encerrado.

`packaging/dist/` e `packaging/build/` **não são versionados**
(cobertos por `dist/`/`build/` no `.gitignore` da raiz) — são
artefatos de build, gerados sob demanda, não código-fonte.

## Build automático (CI)

`.github/workflows/build-gui-exe.yml` — job `build-windows`, roda em
`runs-on: windows-latest`, disparado por push em `main` (tocando
`src/openstruct/**`, `packaging/**` ou `pyproject.toml`) ou
manualmente (`workflow_dispatch`). Passos:

1. `pip install -e ".[gui,build]"` + `pyinstaller
   packaging/openstruct3d-gui.spec` (os mesmos comandos do build
   local acima, só que numa máquina Windows de verdade);
2. publica `dist/openstruct3d-gui.exe` como artifact do workflow
   (`actions/upload-artifact`, retenção padrão — útil para depuração
   de um build específico, mas expira e exige login no GitHub para
   baixar);
3. **publica/atualiza um GitHub Release com tag fixa
   `openstruct3d-gui-latest`** (`gh release delete` só quando o
   Release já existe, seguido de `gh release create ... --target
   <sha>` — a própria `gh` recria a tag no commit certo, sem precisar
   de `git tag`/`git push` manuais) — esse é o mecanismo pensado para
   "instalar e ir recebendo atualizações": a URL do Release NUNCA
   muda, só o arquivo por trás dela. Marcado `--prerelease` (não é uma
   versão numerada oficial do projeto, é sempre "o build mais recente
   de `main`").

Requer `permissions: contents: write` no workflow (para o
`GITHUB_TOKEN` poder criar/apagar releases e a tag) — já configurado
no arquivo. Um `concurrency:` de grupo único serializa execuções
concorrentes (dois pushes próximos em `main`), evitando que builds
paralelos se intercalem e deixem o link servindo um binário errado.

**Este mecanismo NÃO publica o `.exe` Windows a partir deste sandbox
Linux** — o download em si continua bloqueado pela política de rede
deste ambiente (artefatos do Actions são servidos por um redirect para
armazenamento de blob do Azure, fora da lista de hosts permitidos); é
o **runner Windows do GitHub Actions** que gera e publica o arquivo
inteiramente dentro da infraestrutura do GitHub, sem passar pelo
sandbox — por isso o link de Release funciona para qualquer pessoa com
acesso ao repositório, independente de onde esta sessão está rodando.
