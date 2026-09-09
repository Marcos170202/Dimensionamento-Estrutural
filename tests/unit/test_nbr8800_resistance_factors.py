"""Testes unitarios de openstruct.normative.nbr8800.resistance_factors.

Ver docs/normative/NBR8800-RULES.md, RULE-ID NBR8800-RES-001.
"""

from __future__ import annotations

import math

import pytest

from openstruct.normative.nbr8800.resistance_factors import (
    LoadCombinationClass,
    SteelResistanceFactors,
    steel_resistance_factors,
)


def test_steel_resistance_factors_normal() -> None:
    factors = steel_resistance_factors(LoadCombinationClass.NORMAL)
    assert factors.gamma_a1 == 1.10
    assert factors.gamma_a2 == 1.35


def test_steel_resistance_factors_especial_ou_construcao() -> None:
    factors = steel_resistance_factors(LoadCombinationClass.ESPECIAL_OU_CONSTRUCAO)
    assert factors.gamma_a1 == 1.10
    assert factors.gamma_a2 == 1.35


def test_steel_resistance_factors_excepcional() -> None:
    factors = steel_resistance_factors(LoadCombinationClass.EXCEPCIONAL)
    assert factors.gamma_a1 == 1.00
    assert factors.gamma_a2 == 1.15


def test_steel_resistance_factors_covers_all_combination_classes() -> None:
    # Garante que nenhuma classe do enum fica sem entrada na Tabela 3
    # (regressao: adicionar uma classe nova sem atualizar a tabela
    # levantaria KeyError aqui, nao silenciosamente em producao).
    for combination_class in LoadCombinationClass:
        factors = steel_resistance_factors(combination_class)
        assert isinstance(factors, SteelResistanceFactors)


def test_normal_and_especial_have_the_same_factors() -> None:
    # NBR 8800:2024, Tabela 3: as linhas "Normais" e "Especiais ou de
    # construcao" tem os mesmos valores de gamma_a1/gamma_a2.
    assert steel_resistance_factors(LoadCombinationClass.NORMAL) == steel_resistance_factors(
        LoadCombinationClass.ESPECIAL_OU_CONSTRUCAO
    )


def test_excepcional_factors_are_smaller_than_normal() -> None:
    normal = steel_resistance_factors(LoadCombinationClass.NORMAL)
    excepcional = steel_resistance_factors(LoadCombinationClass.EXCEPCIONAL)
    assert excepcional.gamma_a1 < normal.gamma_a1
    assert excepcional.gamma_a2 < normal.gamma_a2


def test_steel_resistance_factors_is_frozen_and_hashable() -> None:
    factors = SteelResistanceFactors(gamma_a1=1.10, gamma_a2=1.35)
    with pytest.raises(AttributeError):
        factors.gamma_a1 = 2.0  # type: ignore[misc]
    hash(factors)  # nao deve levantar


@pytest.mark.parametrize("gamma_a1", [0.0, -1.10, math.nan, math.inf])
def test_steel_resistance_factors_rejects_invalid_gamma_a1(gamma_a1: float) -> None:
    with pytest.raises(ValueError):
        SteelResistanceFactors(gamma_a1=gamma_a1, gamma_a2=1.35)


@pytest.mark.parametrize("gamma_a2", [0.0, -1.35, math.nan, math.inf])
def test_steel_resistance_factors_rejects_invalid_gamma_a2(gamma_a2: float) -> None:
    with pytest.raises(ValueError):
        SteelResistanceFactors(gamma_a1=1.10, gamma_a2=gamma_a2)
