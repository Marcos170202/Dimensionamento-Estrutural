"""Material estrutural.

Fonte: PROGRAM_MASTER.md secao 5 ("MATERIAL").

Convencao de unidades adotada neste projeto (a ser formalizada
futuramente pelo UNITS & DATA AGENT / AGENTS_MASTER.md secao 12):
sistema consistente **N, mm, MPa**, onde MPa = N/mm^2. Assim:

- ``E``, ``G``, ``fy``, ``fu`` : MPa (N/mm^2)
- ``density``                 : kg/mm^3 (ver nota abaixo)
- ``poisson``                 : adimensional

A densidade em kg/mm^3 e um valor muito pequeno para acos comuns
(~7.85e-6 kg/mm^3); ela e mantida nessa unidade apenas para ficar
consistente com N/mm/MPa quando peso proprio for introduzido em fase
futura (Load / self weight, PROGRAM_MASTER secao 10). Nenhuma
conversao automatica de unidades e feita aqui — grandeza fora dessa
convencao produz resultado fisicamente incoerente sem erro explicito.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """Material estrutural elastico-linear (fase atual: metalico).

    Preparado para (fases futuras, NAO implementadas aqui):
    comportamento plastico e dependencia de temperatura — ver
    PROGRAM_MASTER.md secao 5, "Preparar para: elastic / plastic /
    temperature-dependent". Este objeto e imutavel (``frozen``) porque
    representa uma propriedade de catalogo, nao um estado de analise.

    Atributos
    ---------
    name:
        Identificacao do material (ex.: ``"ASTM A572 Gr. 50"``).
    E:
        Modulo de elasticidade longitudinal (MPa).
    G:
        Modulo de elasticidade transversal / cisalhamento (MPa).
    density:
        Massa especifica (kg/mm^3, ver nota de modulo).
    fy:
        Tensao de escoamento (MPa).
    fu:
        Tensao de ruptura (MPa).
    poisson:
        Coeficiente de Poisson (adimensional, 0 <= poisson < 0.5).
    """

    name: str
    E: float
    G: float
    density: float
    fy: float
    fu: float
    poisson: float

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Material.name nao pode ser vazio.")
        # As comparacoes abaixo usam "not (valor > 0)" em vez de
        # "valor <= 0": para NaN ambas as comparacoes (`> 0` e `<= 0`)
        # resultam em False, entao "valor <= 0" deixaria um NaN passar
        # silenciosamente pela validacao. "not (valor > 0)" rejeita NaN
        # corretamente (CODE REVIEW AGENT, achado confirmado).
        if not (self.E > 0):
            raise ValueError(f"Material.E deve ser positivo, recebido {self.E!r}.")
        if not (self.G > 0):
            raise ValueError(f"Material.G deve ser positivo, recebido {self.G!r}.")
        if not (self.density > 0):
            raise ValueError(
                f"Material.density deve ser positiva, recebido {self.density!r}."
            )
        if not (self.fy > 0):
            raise ValueError(f"Material.fy deve ser positivo, recebido {self.fy!r}.")
        if not (self.fu > 0):
            raise ValueError(f"Material.fu deve ser positivo, recebido {self.fu!r}.")
        if not (self.fu >= self.fy):
            raise ValueError(
                f"Material.fu ({self.fu!r}) nao pode ser menor que Material.fy "
                f"({self.fy!r})."
            )
        if not (0.0 <= self.poisson < 0.5):
            raise ValueError(
                f"Material.poisson deve satisfazer 0 <= poisson < 0.5, "
                f"recebido {self.poisson!r}."
            )

    @property
    def isotropic_shear_modulus(self) -> float:
        """``G`` teorico para um material isotropico: ``E / (2 * (1 + nu))``.

        Usado apenas como referencia de coerencia fisica (ver
        :meth:`is_isotropic_consistent`) — o ``G`` efetivamente usado
        nos calculos e sempre o valor informado em :attr:`G`.
        """
        return self.E / (2.0 * (1.0 + self.poisson))

    def is_isotropic_consistent(self, rel_tol: float = 0.03) -> bool:
        """Verifica se ``G`` informado e compativel com material isotropico.

        Compara :attr:`G` com :attr:`isotropic_shear_modulus` dentro de
        uma tolerancia relativa (padrao 3%, suficiente para absorver
        arredondamento de catalogo sem mascarar dados inconsistentes).
        Verificacao de coerencia (ENGINEERING QA AGENT), nao impede a
        construcao do objeto.
        """
        reference = self.isotropic_shear_modulus
        return abs(self.G - reference) <= rel_tol * reference
