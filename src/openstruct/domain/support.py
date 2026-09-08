"""Apoio (condicao de contorno) em um no.

Fonte: PROGRAM_MASTER.md secao 3 ("CORE ESTRUTURAL", item ``Support``)
e secao 9 ("BOUNDARY CONDITIONS"): "Implementar restricoes: UX, UY,
UZ, RX, RY, RZ. Detectar modelos instaveis."

Esta classe apenas DECLARA quais graus de liberdade de um no sao
restringidos (deslocamento prescrito = 0). A deteccao de modelo
instavel (mecanismo) e responsabilidade de
``openstruct.analysis.boundary_conditions`` — ``Support`` isolado nao
tem informacao suficiente para isso (precisa do modelo inteiro).

Fase atual: apenas apoios com deslocamento prescrito NULO (engaste
perfeito ou liberacao total do DOF). Apoio com recalque (deslocamento
prescrito != 0) e elastico (mola) sao preparados para fase futura —
ver nota em ``restrained_dofs()``.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dof import DOF, NODE_DOF_ORDER


@dataclass(frozen=True, slots=True)
class Support:
    """Restricoes de deslocamento em um no.

    Atributos
    ---------
    node_id:
        Id do no restringido (deve existir no ``AnalysisModel`` ao ser
        adicionado — nao verificado aqui isoladamente).
    ux, uy, uz, rx, ry, rz:
        ``True`` se o respectivo grau de liberdade e restringido
        (deslocamento/rotacao prescrito = 0), ``False`` se livre.
    """

    node_id: int
    ux: bool = False
    uy: bool = False
    uz: bool = False
    rx: bool = False
    ry: bool = False
    rz: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, int) or isinstance(self.node_id, bool):
            raise TypeError(
                f"Support.node_id deve ser int, recebido {type(self.node_id).__name__}."
            )
        if self.node_id < 0:
            raise ValueError(
                f"Support.node_id deve ser nao-negativo, recebido {self.node_id!r}."
            )
        if not any(self.restrained_flags):
            raise ValueError(
                f"Support(node_id={self.node_id!r}) nao restringe nenhum DOF — "
                "isso nao e um apoio, e um no-op. Se a intencao e nao ter "
                "apoio neste no, simplesmente nao crie um Support para ele."
            )

    @property
    def restrained_flags(self) -> tuple[bool, bool, bool, bool, bool, bool]:
        """As 6 flags de restricao, na ordem canonica de ``NODE_DOF_ORDER``."""
        return (self.ux, self.uy, self.uz, self.rx, self.ry, self.rz)

    def is_restrained(self, dof: DOF) -> bool:
        """``True`` se o DOF informado esta restringido por este apoio."""
        return self.restrained_flags[NODE_DOF_ORDER.index(dof)]

    def restrained_dofs(self) -> tuple[DOF, ...]:
        """Os DOFs restringidos por este apoio.

        Cada DOF restringido aqui e sempre um deslocamento prescrito
        IGUAL A ZERO — apoio com recalque (prescrito != 0) exigiria
        armazenar o valor prescrito e ainda nao existe nesta fase; a
        assinatura desta classe (flags booleanas) foi escolhida para
        deixar essa extensao natural (trocar ``bool`` por
        ``float | None`` por DOF) sem quebrar a API publica atual.
        """
        pairs = zip(NODE_DOF_ORDER, self.restrained_flags, strict=True)
        return tuple(dof for dof, restrained in pairs if restrained)

    @classmethod
    def fixed(cls, node_id: int) -> Support:
        """Engaste perfeito: todos os 6 DOFs restringidos."""
        return cls(node_id, ux=True, uy=True, uz=True, rx=True, ry=True, rz=True)

    @classmethod
    def pinned(cls, node_id: int) -> Support:
        """Apoio de 3ª ordem / rotula esferica: translacoes restringidas, rotacoes livres."""
        return cls(node_id, ux=True, uy=True, uz=True, rx=False, ry=False, rz=False)
