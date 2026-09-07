"""No estrutural.

Fonte: PROGRAM_MASTER.md secao 4 ("NO"): ``id, x, y, z`` e os 6 DOFs
(UX, UY, UZ, RX, RY, RZ).

Convencao de unidades: coordenadas em mm (ver nota em ``material.py``).

Identidade do no
-----------------
``Node`` compara e faz hash apenas pelo campo ``id`` — igual a como
qualquer software de analise matricial trata nos: o ``id`` e a chave
de identidade do modelo (usada depois para montar a matriz global e
para conectividade de elementos); duas instancias com o mesmo ``id``
representam o mesmo no ainda que, por erro, tragam coordenadas
diferentes, e a construcao de um `Element` deteta esse tipo de
inconsistencia (ver ``elements/base.py``). Coordenadas continuam
mutaveis (``x``, ``y``, ``z``) para suportar a futura operacao
"move node" do MODELING AGENT (PROGRAM_MASTER secao 17) — essa
operacao nao e implementada nesta fase.
"""

from __future__ import annotations

import math

from .dof import DOF, NODE_DOF_ORDER


class Node:
    """Um no do modelo estrutural, com 6 graus de liberdade (3D).

    Parametros
    ----------
    id:
        Identificador inteiro nao-negativo, unico dentro do modelo
        (a unicidade nao e verificada por ``Node`` isoladamente —
        sera responsabilidade do futuro ``AnalysisModel``).
    x, y, z:
        Coordenadas globais do no (mm).
    """

    __slots__ = ("_id", "_x", "_y", "_z")

    def __init__(self, id: int, x: float, y: float, z: float) -> None:
        if not isinstance(id, int) or isinstance(id, bool):
            raise TypeError(f"Node.id deve ser int, recebido {type(id).__name__}.")
        if id < 0:
            raise ValueError(f"Node.id deve ser nao-negativo, recebido {id!r}.")
        for axis_name, value in (("x", x), ("y", y), ("z", z)):
            if not math.isfinite(value):
                raise ValueError(
                    f"Node.{axis_name} deve ser um numero finito, recebido {value!r}."
                )

        self._id = id
        self._x = float(x)
        self._y = float(y)
        self._z = float(z)

    @property
    def id(self) -> int:
        return self._id

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def z(self) -> float:
        return self._z

    @property
    def coordinates(self) -> tuple[float, float, float]:
        """Coordenadas globais como tupla ``(x, y, z)``."""
        return (self._x, self._y, self._z)

    @property
    def dofs(self) -> tuple[DOF, ...]:
        """Os 6 graus de liberdade disponiveis neste no, em ordem canonica.

        A numeracao global de equacoes (offset deste no dentro do
        vetor global de deslocamentos) e responsabilidade da futura
        montagem (``Assembly`` / ``AnalysisModel``), fora do escopo
        desta fase.
        """
        return NODE_DOF_ORDER

    def distance_to(self, other: Node) -> float:
        """Distancia euclidiana ate outro no (mm)."""
        return math.sqrt(
            (self._x - other._x) ** 2
            + (self._y - other._y) ** 2
            + (self._z - other._z) ** 2
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"Node(id={self._id!r}, x={self._x!r}, y={self._y!r}, z={self._z!r})"
