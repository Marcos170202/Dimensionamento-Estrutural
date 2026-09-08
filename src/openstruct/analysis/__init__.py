"""Camada ANALYSIS (PROGRAM_MASTER.md secao 2): montagem e condicoes de contorno.

Ver ADR-002 para o mapeamento das camadas do PROGRAM_MASTER para os
pacotes deste repositorio.
"""

from .assembly import Assembly
from .boundary_conditions import BoundaryConditions, ModelInstabilityError

__all__ = ["Assembly", "BoundaryConditions", "ModelInstabilityError"]
