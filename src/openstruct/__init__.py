"""OpenStruct 3D — nucleo de analise estrutural 3D.

Ver AGENTS_MASTER.md e PROGRAM_MASTER.md na raiz do repositorio para a
especificacao completa. Esta fase (FOUNDATION + CORE STRUCTURAL MODEL)
implementa apenas o modelo de dominio estrutural: DOF, Node, Material,
Section, Element (base) e Element3D. Assembly, boundary conditions,
loads, solver, resultados, GUI, IA e modulos normativos sao fases
futuras — ver docs/decisions/ e o relatorio de fase para o escopo
exato ja implementado.
"""

__version__ = "0.1.0"
