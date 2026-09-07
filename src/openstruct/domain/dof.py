"""Graus de liberdade (DOF) nodais.

Fonte: PROGRAM_MASTER.md secao 4 ("NO"). Cada no possui 6 graus de
liberdade no espaco 3D: 3 translacoes e 3 rotacoes.

Convencao de eixos: sistema global dextrogiro X, Y, Z. As rotacoes
seguem a regra da mao direita em torno do eixo correspondente.

A ordem declarada em ``DOF`` (UX, UY, UZ, RX, RY, RZ) e a ordem
canonica usada em qualquer vetor/matriz indexado por grau de liberdade
neste projeto (ex.: os 12 DOFs de ``Element3D`` sao
``[no_i: UX,UY,UZ,RX,RY,RZ, no_j: UX,UY,UZ,RX,RY,RZ]``).
"""

from __future__ import annotations

from enum import IntEnum, unique


@unique
class DOF(IntEnum):
    """Um grau de liberdade nodal.

    O valor inteiro e o indice (0-based) do DOF dentro do bloco de 6
    graus de liberdade de um unico no — util para montar offsets em
    vetores/matrizes sem repetir "magic numbers".
    """

    UX = 0
    """Translacao na direcao X global."""
    UY = 1
    """Translacao na direcao Y global."""
    UZ = 2
    """Translacao na direcao Z global."""
    RX = 3
    """Rotacao em torno do eixo X global."""
    RY = 4
    """Rotacao em torno do eixo Y global."""
    RZ = 5
    """Rotacao em torno do eixo Z global."""

    @property
    def is_translation(self) -> bool:
        """``True`` para UX/UY/UZ, ``False`` para os DOFs rotacionais."""
        return self in (DOF.UX, DOF.UY, DOF.UZ)

    @property
    def is_rotation(self) -> bool:
        """``True`` para RX/RY/RZ, ``False`` para os DOFs de translacao."""
        return not self.is_translation


#: Numero de graus de liberdade por no em um modelo 3D completo.
DOFS_PER_NODE = 6

#: Ordem canonica dos DOFs de um unico no, usada em toda indexacao de
#: vetores/matrizes deste projeto.
NODE_DOF_ORDER: tuple[DOF, ...] = (
    DOF.UX,
    DOF.UY,
    DOF.UZ,
    DOF.RX,
    DOF.RY,
    DOF.RZ,
)
