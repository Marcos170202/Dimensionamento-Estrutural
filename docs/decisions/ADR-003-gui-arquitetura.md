# ADR-003 — Arquitetura da GUI desktop (`openstruct.gui`)

**Status:** Aceita
**Data:** 2026-09-11
**Agente responsável:** ARCHITECT AGENT (via ORCHESTRATOR, fase GUI DESKTOP V1)

## Contexto

Ate a fase anterior (NBR 8800 — tracao, compressao, cisalhamento,
flexao FLT+FLM+FLA, combinacao de esforcos N+M) o projeto era usavel
apenas como biblioteca Python (`import openstruct`). O usuario pediu
explicitamente um "aplicativo executavel (o software executavel)"
alem da continuacao normativa (§5.5).

Por instrucao explicita do usuario (`AskUserQuestion`), o escopo desta
fase foi definido como:

- **GUI simples, SEM viewport 3D** (PySide6, formularios/tabelas —
  nao PyVista/VTK/OpenGL neste momento);
- Empacotada como executavel desktop (`.exe` no Windows) via
  PyInstaller;
- Executada SOMENTE apos terminar §5.5 (combinacao de esforcos), que
  foi concluida e mesclada antes desta fase comecar (ver PRs #11, #12,
  #13 no historico do repositorio).

PROGRAM_MASTER.md §2 ja reserva uma camada `GUI` na lista de camadas
do projeto (`DOMAIN, CORE, ANALYSIS, SOLVER, RESULTS, POSTPROCESSING,
NORMATIVE, REPORTS, GUI, AI, IO`), sem detalhar framework ou escopo —
esta decisao preenche essa lacuna.

## Decisao

1. **Framework: PySide6** (bindings oficiais do Qt para Python,
   licenca LGPL — compativel com uso comercial sem exigir GPL no
   codigo do usuario, ao contrario do PyQt5/6 que so oferecem GPL ou
   licenca paga). Alternativas descartadas: Tkinter (widgets pobres
   para tabelas editaveis com validacao), Kivy (voltado a mobile/touch,
   sem tabelas nativas), wxPython (comunidade menor, packaging mais
   fragil com PyInstaller).

2. **Novo pacote `openstruct.gui`**, camada FINA sobre as camadas ja
   existentes e validadas (`domain`, `results`, `normative.nbr8800`) —
   **nenhuma formula normativa ou logica de montagem/solucao e
   reescrita aqui**. Cada widget so faz tres coisas: coletar texto das
   tabelas/campos, converter para os tipos que as funcoes ja
   existentes esperam, e chamar essas funcoes diretamente. Isso
   preserva a garantia central do projeto (cada calculo normativo tem
   exatamente UM ponto de implementacao, testado e validado por
   VAL-XXXX) — a GUI nao pode divergir do resultado da biblioteca
   porque ela NAO calcula nada, so exibe.

   Sub-modulos:
   - `widgets.py` — `EditableTable`, tabela generica reutilizada pelas
     6 tabelas da aba de modelo (evita duplicar o mesmo layout
     add/remove-linha 6 vezes).
   - `model_tab.py` — aba "Modelo e Analise": tabelas de
     nos/materiais/secoes/elementos/apoios/cargas, botao "Rodar
     Analise" que chama `run_analysis` (ja existente) e mostra
     deslocamentos/reacoes/esforcos internos.
   - `checks_tab.py` — aba "Verificacoes NBR 8800": uma pagina de
     formulario por verificacao (`check_tension_member`,
     `check_compression_member`, `check_shear_major_axis`,
     `check_flexural_resistance_major_axis`,
     `check_axial_and_bending_interaction`), cada botao "Verificar"
     chama a funcao correspondente e mostra `is_ok`/`sd`/`rd`/
     `utilization`.
   - `main_window.py` — janela principal, agrega as duas abas.
   - `app.py`/`__main__.py` — pontos de entrada (`python -m
     openstruct.gui` e o script `openstruct3d-gui`).

3. **Sem viewport 3D nesta fase** (decisao explicita do usuario) — a
   estrutura e revisada por tabelas de coordenadas/resultados
   numericos, nao por desenho. Um viewport (PyVista/VTK) fica
   reservado para uma fase futura, sem que isso exija reescrever o
   que foi construido aqui (as abas atuais nao assumem a ausencia de
   viewport de forma que impeca adiciona-lo depois — seria uma nova
   aba/painel).

4. **Dependencias como EXTRAS opcionais** em `pyproject.toml`
   (`gui` para PySide6, `build` para PyInstaller) — quem so usa a
   biblioteca (`pip install -e ".[dev]"`) nao e forcado a instalar Qt.
   `[project.gui-scripts]` registra `openstruct3d-gui` como comando
   instalavel.

5. **Empacotamento via PyInstaller** (`packaging/openstruct3d-gui.spec`
   + `packaging/entrypoint.py`) gerando um executavel ONEFILE. Ver
   `docs/build/EMPACOTAMENTO.md` para o procedimento completo e para a
   limitacao de plataforma (PyInstaller NAO faz cross-compilation — um
   `.exe` Windows so pode ser gerado rodando o PyInstaller em uma
   maquina Windows; o `.spec` e identico nos dois sistemas, so muda
   onde e executado).

6. **Testes offscreen** (`tests/gui/`, `QT_QPA_PLATFORM=offscreen`) —
   o Qt roda sem display real tanto neste sandbox quanto no runner do
   GitHub Actions (`ubuntu-latest` no CI nao tem X server). Mantido o
   mesmo padrao de 100% de cobertura das fases anteriores; os guardas
   `if __name__ == "__main__":` de `app.py`/`__main__.py` sao marcados
   `# pragma: no cover` (chamar `main()` de verdade entra no loop de
   eventos do Qt, que so retorna com uma interacao real — o mesmo
   padrao ja usado no projeto para corpos de metodo abstrato, ver
   `_check_result.py`/`elements/base.py`/`loads.py`).

## Alternativas consideradas

- **Viewport 3D desde o inicio (PyVista/VTK embutido em um
  `QVTKRenderWindowInteractor`)**: rejeitada por decisao explicita do
  usuario nesta fase — adicionaria uma dependencia pesada (VTK) e uma
  superficie de teste muito maior (renderizacao 3D e dificil de
  validar automaticamente) antes de haver qualquer usuario real da
  GUI simples. Fica como evolucao futura natural, nao descartada
  definitivamente.
- **Reimplementar os calculos na GUI para "otimizar" a exibicao**
  (ex.: formatar direto sem passar pelos `*CheckResult`): rejeitada —
  violaria a garantia de fonte unica de calculo; a GUI so deve
  formatar o que os objetos `*CheckResult`/`AnalysisResult` ja
  expoem.
- **`.exe` via `cx_Freeze` ou `Nuitka`**: PyInstaller foi escolhido por
  ser o mais usado com PySide6 (hooks oficiais mantidos pelo proprio
  projeto PyInstaller para `PySide6`/`shiboken6`, confirmado nesta
  fase pelo build de teste) e por gerar um unico arquivo (`--onefile`
  via `EXE(...)` no `.spec`), mais simples de distribuir a um usuario
  final sem Python instalado.

## Consequências

- Qualquer novo `check_*` adicionado a `openstruct.normative.nbr8800`
  no futuro exige uma nova pagina em `checks_tab.py` (mecanico, poucas
  linhas) — nao muda nada em `domain`/`results`/`normative`.
- Um viewport 3D futuro entra como um novo modulo/aba dentro de
  `openstruct.gui`, sem alterar `model_tab.py`/`checks_tab.py`.
- A limitacao de plataforma do PyInstaller (sem cross-compilation)
  significa que o `.exe` Windows distribuivel ao usuario final
  precisa ser gerado numa maquina/runner Windows — este sandbox (Linux)
  so pode validar o empacotamento gerando e testando um binario ELF
  Linux equivalente (feito nesta fase), nao o `.exe` em si. Ver
  `docs/build/EMPACOTAMENTO.md`.
