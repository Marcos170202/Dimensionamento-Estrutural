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
validar o binário **Linux**. O `.exe` Windows distribuível ao usuário
final precisa ser gerado separadamente, em uma máquina Windows (local
ou um runner `windows-latest` do GitHub Actions — ver seção
"Automatizando no CI" abaixo).

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

## Automatizando no CI (não incluído nesta fase)

Para gerar o `.exe` Windows automaticamente a cada release, seria
necessário um job adicional em `.github/workflows/` rodando em
`runs-on: windows-latest`, com os mesmos dois comandos acima (`pip
install -e ".[gui,build]"` + `pyinstaller
packaging/openstruct3d-gui.spec`), publicando `dist/openstruct3d-gui.exe`
como artefato do workflow (`actions/upload-artifact`) ou anexado a uma
release do GitHub. Isso fica **fora do escopo desta fase** (o CI atual
só roda testes/lint/mypy em `ubuntu-latest`) — registrado aqui para
não ser esquecido quando o projeto precisar de uma distribuição
oficial do `.exe`.
