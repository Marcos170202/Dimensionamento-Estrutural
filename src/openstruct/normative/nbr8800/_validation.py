"""Validacao numerica compartilhada entre os submodulos de ``nbr8800``.

Fatorado para nao duplicar a mesma checagem (finito e estritamente
positivo) em cada campo de cada dataclass/funcao deste pacote — achado
do CODE REVIEW AGENT na fase de barras tracionadas (a mesma checagem
apareceria repetida em ``resistance_factors.py`` e ``tension.py``).

Modulo privado (prefixo ``_``): nao faz parte da API publica de
``openstruct.normative.nbr8800``.
"""

from __future__ import annotations

import math


def is_positive_finite(value: float) -> bool:
    """``True`` se ``value`` for finito (nao NaN, nao +/-inf) e > 0.

    Nota: mais estrito que o padrao usado em ``domain/material.py`` e
    ``domain/section.py`` (``not (valor > 0)``), que rejeita NaN mas
    NAO rejeita infinito (``math.inf > 0`` e ``True``). Aqui, como as
    grandezas normativas (tensoes, areas, coeficientes) nunca sao
    fisicamente infinitas, a checagem extra de ``math.isfinite`` e
    deliberada e mais rigorosa — nao e o "mesmo padrao" do dominio,
    e sim uma extensao dele.
    """
    return math.isfinite(value) and value > 0
