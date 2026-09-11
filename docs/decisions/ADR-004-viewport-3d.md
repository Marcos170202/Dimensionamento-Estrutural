# ADR-004 — Viewport 3D (PyVista/VTK) na GUI desktop

**Status:** Aceita
**Data:** 2026-09-11
**Agente responsável:** ARCHITECT AGENT (via ORCHESTRATOR, fase VIEWPORT 3D)

## Contexto

`PROGRAM_MASTER.md` §16 ("GUI") descreve a tela principal do aplicativo
com um **VIEWPORT 3D** como área central, e §17 ("MODELAGEM 3D") lista
operações interativas futuras sobre esse viewport (criar/mover nó,
criar/apagar elemento, atribuir material/seção/apoio/carga clicando no
desenho). §27 ("TERCEIRO MARCO — DESKTOP GUI") junta os dois: "PySide6
+ viewport 3D".

A fase anterior (ADR-003, PR #14) implementou a GUI desktop
**explicitamente sem viewport 3D** — decisão do usuário via
`AskUserQuestion`, para entregar antes um aplicativo funcional simples
(tabelas + formulários). Esta fase ("continue com os processos 3D",
instrução do usuário) fecha essa lacuna: adiciona o viewport 3D de
visualização.

## Decisão

1. **Biblioteca: PyVista + `pyvistaqt`** (ambas construídas sobre VTK).
   Alternativas descartadas:
   - **VTK puro** (`vtkmodules` diretamente): API muito mais verbosa e
     de baixo nível para montar `vtkPoints`/`vtkCellArray`/
     `vtkPolyData`/`vtkActor`/`vtkMapper` manualmente — PyVista já
     encapsula esse padrão em `pv.PolyData`/`plotter.add_mesh` com uma
     API Pythonic, sem perder acesso ao VTK subjacente quando
     necessário.
   - **OpenGL direto (`QOpenGLWidget` + shaders próprios)**: exigiria
     reimplementar do zero picking, câmera orbital, iluminação —
     trabalho de um mini-motor gráfico só para desenhar linhas e
     pontos. Rejeitado por esforço muito maior sem ganho para o escopo
     atual (visualização de arame/pontos, não renderização
     fotorrealista).
   - **`matplotlib` 3D (`mpl_toolkits.mplot3d`)**: não é interativo em
     tempo real com a fluidez de uma cena 3D real (sem aceleração por
     GPU, câmera limitada) — adequado para um gráfico estático, não
     para um viewport de modelagem.

   `pyvistaqt.QtInteractor` é um `QWidget` que já embute a cena VTK
   dentro do layout do PySide6 (a mesma classe funciona com
   PyQt5/PySide2/PySide6), com câmera orbital/zoom/pan por mouse
   prontos — não há nada disso para implementar manualmente.

2. **Viabilidade offscreen confirmada nesta fase**: `pyvista`/
   `pyvistaqt`/`vtk` renderizam e constroem `QtInteractor` corretamente
   sob `QT_QPA_PLATFORM=offscreen` neste sandbox Linux (mesmo mecanismo
   já usado para os testes da GUI desde o ADR-003) — verificado por
   smoke test antes de qualquer código de produção ser escrito. Isso
   permite manter os testes de `viewport_3d.py` na mesma suíte
   `tests/gui/` (offscreen, sem exigir display real), sem infraestrutura
   de teste adicional.

3. **Escopo: SOMENTE visualização nesta fase** — a nova aba
   "Visualização 3D" desenha:
   - a estrutura (nós como pontos, elementos como segmentos de reta
     ligando os nós — sem a curvatura real de Hermite entre nós,
     aproximação de desenho aceitável para uma primeira versão);
   - apoios (marcados com uma cor distinta, sem diferenciar
     visualmente engaste/pino/apoio parcial nesta fase);
   - cargas nodais (`NodalLoad`, uma seta por força não-nula, com
     comprimento visual fixo — proporcional ao tamanho do modelo, NÃO
     à magnitude real da força, que pode variar em ordens de grandeza
     entre modelos);
   - a forma deformada da última análise executada, sobreposta e
     escalável por um fator ajustável pelo usuário (deslocamentos reais
     em mm são pequenos demais para aparecer na escala da estrutura sem
     ampliação).

   Camada FINA sobre `domain`/`results` — nenhuma fórmula de engenharia
   nem lógica de montagem de modelo é duplicada; a montagem continua
   inteiramente em `ModelTab.build_model_and_load_case` (já validada),
   reaproveitada sem alteração pelo botão "Atualizar visualização".

4. **Integração**: nova aba entre "Modelo e Análise" e "Verificações
   NBR 8800" na `MainWindow`, recebendo uma referência a `ModelTab` (não
   o contrário) — decisão de dependência unidirecional para não criar
   acoplamento circular entre os módulos da GUI. `ModelTab` ganhou um
   atributo público `last_result` (cache do último `AnalysisResult` bem
   sucedido), consumido pelo viewport para sobrepor a deformada sem
   reexecutar a análise.

## Fora do escopo (PROGRAM_MASTER §17 — "Futuramente")

O próprio `PROGRAM_MASTER.md` marca as operações de modelagem
interativa como "Futuramente" — não implementadas nesta fase:

- criar/mover nó, criar/apagar elemento clicando no viewport;
- atribuir material/seção/apoio/carga pelo desenho (picking de
  elementos/nós);
- desenho da curvatura real de Hermite entre nós na forma deformada
  (hoje é uma aproximação por segmentos de reta ligando nós
  deslocados);
- diferenciação visual entre tipos de apoio (engaste/pino/apoio
  parcial) — hoje todo nó com qualquer DOF restringido usa o mesmo
  marcador;
- visualização de momentos concentrados (`mx`/`my`/`mz` de
  `NodalLoad`) — só forças (`fx`/`fy`/`fz`) geram seta nesta fase;
- exportação de imagem/screenshot do viewport;
- edição do layout da janela principal para o esquema do
  PROGRAM_MASTER §16 (viewport central + árvore do modelo + painel de
  propriedades nas laterais) — a estrutura atual (abas) permanece;
  reorganizar em um layout de painéis fica para quando a modelagem
  interativa (§17) justificar a árvore de modelo lateral.

## Consequências

- O extra opcional `gui` (`pip install -e ".[gui]"`) cresce
  significativamente (VTK é uma dependência nativa grande) — quem só
  usa a biblioteca (`pip install -e ".[dev]"`) continua sem essa
  dependência.
- O executável empacotado (`packaging/openstruct3d-gui.spec`, PR #14)
  fica bem maior (VTK adiciona dezenas de MB de bibliotecas nativas) —
  ver `docs/build/EMPACOTAMENTO.md` para o tamanho medido nesta fase e
  a confirmação de que o PyInstaller empacota corretamente via os hooks
  de `vtkmodules` já inclusos em `pyinstaller-hooks-contrib`
  (dependência transitiva de `pyinstaller`, nenhum hook adicional
  precisou ser escrito).
- Uma futura modelagem interativa (§17) entra como novos métodos em
  `Viewport3D` (captura de clique/arraste via os callbacks de picking
  do VTK/PyVista) sem precisar recriar o widget do zero.
