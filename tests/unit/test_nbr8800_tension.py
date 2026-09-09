"""Testes unitarios de openstruct.normative.nbr8800.tension.

Ver docs/normative/NBR8800-RULES.md, RULE-IDs NBR8800-TRAC-001/002/003.
"""

from __future__ import annotations

import math

import pytest

from openstruct.normative.nbr8800.resistance_factors import (
    LoadCombinationClass,
    SteelResistanceFactors,
    steel_resistance_factors,
)
from openstruct.normative.nbr8800.tension import (
    TensionCheckResult,
    check_tension_member,
    net_area_without_holes,
)

NORMAL_FACTORS = steel_resistance_factors(LoadCombinationClass.NORMAL)


# -- net_area_without_holes --------------------------------------------------


def test_net_area_without_holes_returns_gross_area() -> None:
    assert net_area_without_holes(2000.0) == 2000.0


@pytest.mark.parametrize("gross_area", [0.0, -100.0, math.nan, math.inf])
def test_net_area_without_holes_rejects_invalid_area(gross_area: float) -> None:
    with pytest.raises(ValueError):
        net_area_without_holes(gross_area)


# -- check_tension_member: caso governado por escoamento ---------------------


def test_check_tension_member_yield_governs() -> None:
    # Ag=2000mm^2, fy=250MPa, gamma_a1=1.10 -> Nt_rd_yield = 454545.4545...N
    # Ae=1600mm^2, fu=400MPa, gamma_a2=1.35 -> Nt_rd_rupture = 474074.074...N
    # yield < rupture -> escoamento governa.
    result = check_tension_member(
        nt_sd=400_000.0,
        gross_area=2000.0,
        effective_net_area=1600.0,
        fy=250.0,
        fu=400.0,
        resistance_factors=NORMAL_FACTORS,
    )
    assert isinstance(result, TensionCheckResult)
    assert result.nt_rd_yield == pytest.approx(2000.0 * 250.0 / 1.10)
    assert result.nt_rd_rupture == pytest.approx(1600.0 * 400.0 / 1.35)
    assert result.governing == "escoamento_secao_bruta"
    assert result.nt_rd == pytest.approx(result.nt_rd_yield)
    assert result.utilization == pytest.approx(400_000.0 / result.nt_rd_yield)
    assert result.is_ok is True


# -- check_tension_member: caso governado por ruptura -------------------------


def test_check_tension_member_rupture_governs() -> None:
    # Area liquida efetiva bem menor -> ruptura passa a governar.
    result = check_tension_member(
        nt_sd=200_000.0,
        gross_area=2000.0,
        effective_net_area=500.0,
        fy=250.0,
        fu=400.0,
        resistance_factors=NORMAL_FACTORS,
    )
    assert result.nt_rd_rupture == pytest.approx(500.0 * 400.0 / 1.35)
    assert result.governing == "ruptura_secao_liquida"
    assert result.nt_rd == pytest.approx(result.nt_rd_rupture)


def test_check_tension_member_is_ok_false_when_overloaded() -> None:
    result = check_tension_member(
        nt_sd=1_000_000.0,
        gross_area=2000.0,
        effective_net_area=1600.0,
        fy=250.0,
        fu=400.0,
        resistance_factors=NORMAL_FACTORS,
    )
    assert result.is_ok is False
    assert result.utilization > 1.0


def test_check_tension_member_is_ok_true_at_exact_boundary() -> None:
    # Nt,Sd == Nt,Rd exatamente -> condicao 5.2.1.2 (<=) ainda satisfeita.
    factors = SteelResistanceFactors(gamma_a1=1.0, gamma_a2=1.0)
    nt_rd = 1000.0 * 250.0 / 1.0
    result = check_tension_member(
        nt_sd=nt_rd,
        gross_area=1000.0,
        effective_net_area=1000.0,
        fy=250.0,
        fu=250.0,
        resistance_factors=factors,
    )
    assert result.is_ok is True
    assert result.utilization == pytest.approx(1.0)


# -- validacao de entradas ----------------------------------------------------


def test_check_tension_member_rejects_non_finite_nt_sd() -> None:
    with pytest.raises(ValueError):
        check_tension_member(
            nt_sd=math.nan,
            gross_area=2000.0,
            effective_net_area=2000.0,
            fy=250.0,
            fu=400.0,
            resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("gross_area", [0.0, -1.0, math.nan, math.inf])
def test_check_tension_member_rejects_invalid_gross_area(gross_area: float) -> None:
    with pytest.raises(ValueError):
        check_tension_member(
            nt_sd=1000.0,
            gross_area=gross_area,
            effective_net_area=100.0,
            fy=250.0,
            fu=400.0,
            resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("effective_net_area", [0.0, -1.0, math.nan, math.inf])
def test_check_tension_member_rejects_invalid_effective_net_area(
    effective_net_area: float,
) -> None:
    with pytest.raises(ValueError):
        check_tension_member(
            nt_sd=1000.0,
            gross_area=2000.0,
            effective_net_area=effective_net_area,
            fy=250.0,
            fu=400.0,
            resistance_factors=NORMAL_FACTORS,
        )


def test_check_tension_member_rejects_net_area_larger_than_gross_area() -> None:
    # Ae = Ct*An e An <= Ag sempre (5.2.4.2); Ae > Ag e sempre um erro
    # de modelagem, nunca um caso normativo valido.
    with pytest.raises(ValueError):
        check_tension_member(
            nt_sd=1000.0,
            gross_area=1000.0,
            effective_net_area=1000.1,
            fy=250.0,
            fu=400.0,
            resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("fy", [0.0, -250.0, math.nan, math.inf])
def test_check_tension_member_rejects_invalid_fy(fy: float) -> None:
    with pytest.raises(ValueError):
        check_tension_member(
            nt_sd=1000.0,
            gross_area=2000.0,
            effective_net_area=2000.0,
            fy=fy,
            fu=400.0,
            resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("fu", [0.0, -400.0, math.nan, math.inf])
def test_check_tension_member_rejects_invalid_fu(fu: float) -> None:
    with pytest.raises(ValueError):
        check_tension_member(
            nt_sd=1000.0,
            gross_area=2000.0,
            effective_net_area=2000.0,
            fy=250.0,
            fu=fu,
            resistance_factors=NORMAL_FACTORS,
        )


# -- TensionCheckResult: validacao direta e imutabilidade --------------------


def test_tension_check_result_rejects_non_finite_fields() -> None:
    with pytest.raises(ValueError):
        TensionCheckResult(nt_sd=math.nan, nt_rd_yield=1000.0, nt_rd_rupture=1000.0)


@pytest.mark.parametrize("nt_rd_yield", [0.0, -1.0])
def test_tension_check_result_rejects_non_positive_nt_rd_yield(nt_rd_yield: float) -> None:
    with pytest.raises(ValueError):
        TensionCheckResult(nt_sd=100.0, nt_rd_yield=nt_rd_yield, nt_rd_rupture=1000.0)


@pytest.mark.parametrize("nt_rd_rupture", [0.0, -1.0])
def test_tension_check_result_rejects_non_positive_nt_rd_rupture(nt_rd_rupture: float) -> None:
    with pytest.raises(ValueError):
        TensionCheckResult(nt_sd=100.0, nt_rd_yield=1000.0, nt_rd_rupture=nt_rd_rupture)


def test_tension_check_result_is_frozen() -> None:
    result = TensionCheckResult(nt_sd=100.0, nt_rd_yield=1000.0, nt_rd_rupture=2000.0)
    with pytest.raises(AttributeError):
        result.nt_sd = 200.0  # type: ignore[misc]


def test_tension_check_result_governing_tie_prefers_yield() -> None:
    # Empate exato -> a implementacao usa "<=" para nt_rd_yield, entao
    # o empate resolve para escoamento (escolha arbitraria mas
    # deterministica, documentada no docstring de `governing`).
    result = TensionCheckResult(nt_sd=100.0, nt_rd_yield=1000.0, nt_rd_rupture=1000.0)
    assert result.governing == "escoamento_secao_bruta"
    assert result.nt_rd == 1000.0
