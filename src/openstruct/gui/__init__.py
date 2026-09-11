"""GUI desktop do OpenStruct 3D (PySide6 + PyVista/VTK).

Marco 3 do PROGRAM_MASTER.md ("DESKTOP GUI"): interface grafica
permitindo montar um modelo (nos/materiais/secoes/elementos/apoios/
cargas), visualiza-lo em 3D, rodar a analise
(:func:`openstruct.run_analysis`) e executar as verificacoes
normativas ja implementadas em ``openstruct.normative.nbr8800``, tudo
por formularios — sem precisar escrever Python. Modelagem 3D
INTERATIVA (PROGRAM_MASTER secao 17 — criar/mover no, atribuir
material/apoio/carga clicando no viewport) fica para uma fase futura.

Arquitetura (ver ``docs/decisions/ADR-003-gui-arquitetura.md`` e
``docs/decisions/ADR-004-viewport-3d.md``): a GUI e uma camada FINA
sobre ``domain``/``results``/``normative`` — nenhuma formula de
engenharia, validacao normativa ou logica de montagem de modelo e
duplicada aqui. Os widgets apenas coletam/exibem dados e chamam
diretamente as funcoes/classes ja implementadas e validadas nos
modulos correspondentes.

Modulos deste pacote:

- ``widgets`` — ``EditableTable``, utilitario reutilizado pelas
  tabelas de nos/materiais/secoes/elementos/apoios/cargas.
- ``model_tab`` — ``ModelTab``: montagem do modelo e execucao da
  analise, com tabelas de resultados (deslocamentos/reacoes/esforcos).
- ``viewport_3d`` — ``Viewport3D``: desenho 3D (PyVista/VTK) do modelo
  montado em ``ModelTab``, com forma deformada opcional da ultima
  analise executada.
- ``checks_tab`` — ``ChecksTab``: verificacoes normativas NBR 8800
  (tracao, compressao, cisalhamento, flexao completa, combinacao
  N+M), uma por formulario dinamico.
- ``main_window`` — ``MainWindow``: janela principal, agrega as abas.
- ``app`` — ``main()``, ponto de entrada (``python -m openstruct.gui``
  ou o script ``openstruct3d-gui`` instalado via ``pip install -e
  ".[gui]"``).

Este pacote SO e importavel se o extra opcional ``gui`` estiver
instalado (``PySide6``/``pyvista``/``pyvistaqt`` nao sao dependencias
obrigatorias do nucleo — ver ``pyproject.toml``,
``[project.optional-dependencies].gui``).
"""

from __future__ import annotations
