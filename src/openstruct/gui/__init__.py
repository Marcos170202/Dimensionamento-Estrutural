"""GUI desktop do OpenStruct 3D (PySide6).

Marco 3 do PROGRAM_MASTER.md ("DESKTOP GUI"), primeira fase: interface
grafica SIMPLES (sem viewport 3D — PyVista/VTK fica para uma fase
futura), permitindo montar um modelo (nos/materiais/secoes/elementos/
apoios/cargas), rodar a analise (:func:`openstruct.run_analysis`) e
executar as verificacoes normativas ja implementadas em
``openstruct.normative.nbr8800``, tudo por formularios — sem precisar
escrever Python.

Arquitetura (ver ``docs/decisions/ADR-003-gui-arquitetura.md``): a GUI
e uma camada FINA sobre ``domain``/``results``/``normative`` — nenhuma
formula de engenharia, validacao normativa ou logica de montagem de
modelo e duplicada aqui. Os widgets apenas coletam/exibem dados e
chamam diretamente as funcoes/classes ja implementadas e validadas
nos modulos correspondentes.

Modulos deste pacote:

- ``widgets`` — ``EditableTable``, utilitario reutilizado pelas
  tabelas de nos/materiais/secoes/elementos/apoios/cargas.
- ``model_tab`` — ``ModelTab``: montagem do modelo e execucao da
  analise, com tabelas de resultados (deslocamentos/reacoes/esforcos).
- ``checks_tab`` — ``ChecksTab``: verificacoes normativas NBR 8800
  (tracao, compressao, cisalhamento, flexao completa, combinacao
  N+M), uma por formulario dinamico.
- ``main_window`` — ``MainWindow``: janela principal, agrega as abas.
- ``app`` — ``main()``, ponto de entrada (``python -m openstruct.gui``
  ou o script ``openstruct3d-gui`` instalado via ``pip install -e
  ".[gui]"``).

Este pacote SO e importavel se o extra opcional ``gui`` estiver
instalado (``PySide6`` nao e uma dependencia obrigatoria do nucleo —
ver ``pyproject.toml``, ``[project.optional-dependencies].gui``).
"""

from __future__ import annotations
