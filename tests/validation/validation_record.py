"""Registro PROBLEMA/REFERENCIA/RESULTADO exigido por AGENTS_MASTER.md secao 7.

Compartilhado por todos os testes de ``tests/validation/`` — nao e um
modulo ``test_*`` (nao e coletado pelo pytest como suite de testes).
"""

from __future__ import annotations

from dataclasses import dataclass

#: Tolerancia relativa padrao. Comparacoes contra solucao FECHADA (nao
#: discretizada) devem usar algo desta ordem — so ha erro de
#: arredondamento de ponto flutuante a absorver, nao erro de metodo.
DEFAULT_RELATIVE_TOLERANCE = 1.0e-8


@dataclass(frozen=True)
class ValidationRecord:
    """Um caso de validacao: PROBLEMA / REFERENCIA / RESULTADO / ERRO / STATUS."""

    problema: str
    referencia: float
    resultado: float
    tolerancia: float = DEFAULT_RELATIVE_TOLERANCE

    @property
    def erro_relativo(self) -> float:
        if self.referencia == 0.0:
            return abs(self.resultado)
        return abs(self.resultado - self.referencia) / abs(self.referencia)

    @property
    def status(self) -> str:
        return "APROVADO" if self.erro_relativo <= self.tolerancia else "REPROVADO"
