"""Testes unitarios de openstruct.normative.nbr8800.compression.

Ver docs/normative/NBR8800-RULES.md, RULE-IDs NBR8800-COMP-001 a 005.
"""

from __future__ import annotations

import math

import pytest

from openstruct.normative.nbr8800.compression import (
    CompressionCheckResult,
    check_compression_member,
    effective_area_without_local_buckling,
    flexural_buckling_force,
    reduction_factor,
    slenderness_parameter,
)
from openstruct.normative.nbr8800.resistance_factors import (
    LoadCombinationClass,
    steel_resistance_factors,
)

NORMAL_FACTORS = steel_resistance_factors(LoadCombinationClass.NORMAL)


# -- flexural_buckling_force ---------------------------------------------------


def test_flexural_buckling_force_matches_euler_formula() -> None:
    # Ne = pi^2*E*I/L^2
    e, i, length = 200_000.0, 3.79e6, 4000.0
    expected = math.pi**2 * e * i / length**2
    assert flexural_buckling_force(e, i, length) == pytest.approx(expected)


def test_flexural_buckling_force_halves_when_length_doubles_squared() -> None:
    # Ne ~ 1/L^2 -> dobrar L reduz Ne para 1/4.
    e, i = 200_000.0, 3.79e6
    ne_short = flexural_buckling_force(e, i, 2000.0)
    ne_long = flexural_buckling_force(e, i, 4000.0)
    assert ne_short / ne_long == pytest.approx(4.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_buckling_force_rejects_invalid_elastic_modulus(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_buckling_force(value, 1000.0, 1000.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_buckling_force_rejects_invalid_moment_of_inertia(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_buckling_force(200_000.0, value, 1000.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_buckling_force_rejects_invalid_length(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_buckling_force(200_000.0, 1000.0, value)


# -- effective_area_without_local_buckling -------------------------------------


def test_effective_area_without_local_buckling_returns_gross_area() -> None:
    assert effective_area_without_local_buckling(2680.0) == 2680.0


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_effective_area_without_local_buckling_rejects_invalid_area(value: float) -> None:
    with pytest.raises(ValueError):
        effective_area_without_local_buckling(value)


# -- slenderness_parameter ------------------------------------------------------


def test_slenderness_parameter_matches_formula() -> None:
    ag, fy, ne = 2680.0, 345.0, 467572.5
    expected = math.sqrt(ag * fy / ne)
    assert slenderness_parameter(ag, fy, ne) == pytest.approx(expected)


def test_slenderness_parameter_is_zero_when_buckling_force_is_very_large() -> None:
    # Ne -> infinito (coluna "infinitamente robusta" a flambagem) -> lambda_0 -> 0.
    lam0 = slenderness_parameter(1000.0, 250.0, 1e18)
    assert lam0 == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_slenderness_parameter_rejects_invalid_gross_area(value: float) -> None:
    with pytest.raises(ValueError):
        slenderness_parameter(value, 250.0, 1000.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_slenderness_parameter_rejects_invalid_fy(value: float) -> None:
    with pytest.raises(ValueError):
        slenderness_parameter(1000.0, value, 1000.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_slenderness_parameter_rejects_invalid_elastic_buckling_force(value: float) -> None:
    with pytest.raises(ValueError):
        slenderness_parameter(1000.0, 250.0, value)


# -- reduction_factor (chi) ------------------------------------------------------


def test_reduction_factor_at_zero_is_one() -> None:
    # Coluna infinitamente robusta -> chi=1 (resistencia plena de escoamento).
    assert reduction_factor(0.0) == pytest.approx(1.0)


def test_reduction_factor_uses_first_branch_at_1_5_exactly() -> None:
    # lambda_0 == 1.5 -> "<=" inclui o limite no PRIMEIRO ramo (0,658^lambda_0^2).
    expected = 0.658 ** (1.5**2)
    assert reduction_factor(1.5) == pytest.approx(expected)


def test_reduction_factor_second_branch_just_above_1_5() -> None:
    lam0 = 1.5 + 1e-9
    expected = 0.877 / lam0**2
    assert reduction_factor(lam0) == pytest.approx(expected)


def test_reduction_factor_branches_are_close_but_not_identical_at_1_5() -> None:
    # Caracteristica conhecida da curva normativa (ver docstring de
    # reduction_factor): os dois ramos NAO se encontram exatamente em
    # lambda_0=1.5 (~1.7e-4 de diferenca). Confirma que a implementacao
    # usa EXATAMENTE as formulas da norma, sem "consertar" a
    # descontinuidade artificialmente.
    branch1 = 0.658 ** (1.5**2)
    branch2 = 0.877 / 1.5**2
    assert branch1 != pytest.approx(branch2, abs=1e-6)
    assert abs(branch1 - branch2) == pytest.approx(1.7166e-4, abs=1e-6)


def test_reduction_factor_is_monotonically_decreasing() -> None:
    values = [reduction_factor(lam) for lam in [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]]
    assert values == sorted(values, reverse=True)


def test_reduction_factor_stays_within_zero_one_for_reasonable_range() -> None:
    for lam0 in [0.0, 0.3, 0.8, 1.2, 1.5, 1.8, 2.5, 4.0, 10.0]:
        chi = reduction_factor(lam0)
        assert 0.0 < chi <= 1.0


@pytest.mark.parametrize("lambda_0", [-1.0, -0.001, math.nan])
def test_reduction_factor_rejects_invalid_lambda_0(lambda_0: float) -> None:
    with pytest.raises(ValueError):
        reduction_factor(lambda_0)


def test_reduction_factor_rejects_infinite_lambda_0() -> None:
    with pytest.raises(ValueError):
        reduction_factor(math.inf)


# -- check_compression_member ----------------------------------------------------


def test_check_compression_member_matches_manual_calculation() -> None:
    ag = 2680.0
    fy = 345.0
    ne = 467572.5
    aef = effective_area_without_local_buckling(ag)

    result = check_compression_member(
        nc_sd=100_000.0,
        gross_area=ag,
        effective_area=aef,
        fy=fy,
        elastic_buckling_force=ne,
        resistance_factors=NORMAL_FACTORS,
    )

    lambda_0_ref = math.sqrt(ag * fy / ne)
    chi_ref = 0.658 ** (lambda_0_ref**2) if lambda_0_ref <= 1.5 else 0.877 / lambda_0_ref**2
    nc_rd_ref = chi_ref * aef * fy / 1.10

    assert isinstance(result, CompressionCheckResult)
    assert result.lambda_0 == pytest.approx(lambda_0_ref)
    assert result.chi == pytest.approx(chi_ref)
    assert result.nc_rd == pytest.approx(nc_rd_ref)
    assert result.utilization == pytest.approx(100_000.0 / nc_rd_ref)
    assert result.is_ok is True


def test_check_compression_member_is_ok_false_when_overloaded() -> None:
    result = check_compression_member(
        nc_sd=1_000_000.0,
        gross_area=2680.0,
        effective_area=2680.0,
        fy=345.0,
        elastic_buckling_force=467572.5,
        resistance_factors=NORMAL_FACTORS,
    )
    assert result.is_ok is False
    assert result.utilization > 1.0


def test_check_compression_member_is_ok_true_at_exact_boundary() -> None:
    ag = 1000.0
    fy = 250.0
    ne = 1e9  # Ne muito grande -> lambda_0 ~ 0 -> chi ~ 1 -> Nc_rd ~ Ag*fy/gamma_a1
    aef = ag
    result_probe = check_compression_member(
        nc_sd=0.0, gross_area=ag, effective_area=aef, fy=fy,
        elastic_buckling_force=ne, resistance_factors=NORMAL_FACTORS,
    )
    result = check_compression_member(
        nc_sd=result_probe.nc_rd, gross_area=ag, effective_area=aef, fy=fy,
        elastic_buckling_force=ne, resistance_factors=NORMAL_FACTORS,
    )
    assert result.is_ok is True
    assert result.utilization == pytest.approx(1.0)


def test_check_compression_member_smaller_effective_area_reduces_nc_rd() -> None:
    ag = 2680.0
    fy = 345.0
    ne = 467572.5
    full = check_compression_member(
        nc_sd=1.0, gross_area=ag, effective_area=ag, fy=fy,
        elastic_buckling_force=ne, resistance_factors=NORMAL_FACTORS,
    )
    reduced = check_compression_member(
        nc_sd=1.0, gross_area=ag, effective_area=ag * 0.7, fy=fy,
        elastic_buckling_force=ne, resistance_factors=NORMAL_FACTORS,
    )
    assert reduced.nc_rd < full.nc_rd
    assert reduced.nc_rd == pytest.approx(full.nc_rd * 0.7)


def test_check_compression_member_shorter_length_increases_nc_rd() -> None:
    # Coluna mais curta -> Ne maior -> lambda_0 menor -> chi maior -> Nc_rd maior.
    ag, fy = 2680.0, 345.0
    e, iz = 200_000.0, 37.0e6
    ne_short = flexural_buckling_force(e, iz, 2000.0)
    ne_long = flexural_buckling_force(e, iz, 8000.0)
    result_short = check_compression_member(
        nc_sd=1.0, gross_area=ag, effective_area=ag, fy=fy,
        elastic_buckling_force=ne_short, resistance_factors=NORMAL_FACTORS,
    )
    result_long = check_compression_member(
        nc_sd=1.0, gross_area=ag, effective_area=ag, fy=fy,
        elastic_buckling_force=ne_long, resistance_factors=NORMAL_FACTORS,
    )
    assert result_short.nc_rd > result_long.nc_rd


def test_check_compression_member_rejects_non_finite_nc_sd() -> None:
    with pytest.raises(ValueError):
        check_compression_member(
            nc_sd=math.nan, gross_area=1000.0, effective_area=1000.0, fy=250.0,
            elastic_buckling_force=1000.0, resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_compression_member_rejects_invalid_gross_area(value: float) -> None:
    with pytest.raises(ValueError):
        check_compression_member(
            nc_sd=1.0, gross_area=value, effective_area=100.0, fy=250.0,
            elastic_buckling_force=1000.0, resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_compression_member_rejects_invalid_effective_area(value: float) -> None:
    with pytest.raises(ValueError):
        check_compression_member(
            nc_sd=1.0, gross_area=1000.0, effective_area=value, fy=250.0,
            elastic_buckling_force=1000.0, resistance_factors=NORMAL_FACTORS,
        )


def test_check_compression_member_rejects_effective_area_larger_than_gross_area() -> None:
    with pytest.raises(ValueError):
        check_compression_member(
            nc_sd=1.0, gross_area=1000.0, effective_area=1000.1, fy=250.0,
            elastic_buckling_force=1000.0, resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_compression_member_rejects_invalid_fy(value: float) -> None:
    with pytest.raises(ValueError):
        check_compression_member(
            nc_sd=1.0, gross_area=1000.0, effective_area=1000.0, fy=value,
            elastic_buckling_force=1000.0, resistance_factors=NORMAL_FACTORS,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_compression_member_rejects_invalid_elastic_buckling_force(value: float) -> None:
    with pytest.raises(ValueError):
        check_compression_member(
            nc_sd=1.0, gross_area=1000.0, effective_area=1000.0, fy=250.0,
            elastic_buckling_force=value, resistance_factors=NORMAL_FACTORS,
        )


# -- CompressionCheckResult: validacao direta e imutabilidade -------------------


def test_compression_check_result_rejects_non_finite_nc_sd() -> None:
    with pytest.raises(ValueError):
        CompressionCheckResult(nc_sd=math.nan, lambda_0=1.0, chi=0.5, nc_rd=1000.0)


@pytest.mark.parametrize("lambda_0", [-1.0, math.nan, math.inf])
def test_compression_check_result_rejects_invalid_lambda_0(lambda_0: float) -> None:
    with pytest.raises(ValueError):
        CompressionCheckResult(nc_sd=100.0, lambda_0=lambda_0, chi=0.5, nc_rd=1000.0)


@pytest.mark.parametrize("chi", [0.0, -0.1, 1.0001, math.nan])
def test_compression_check_result_rejects_invalid_chi(chi: float) -> None:
    with pytest.raises(ValueError):
        CompressionCheckResult(nc_sd=100.0, lambda_0=1.0, chi=chi, nc_rd=1000.0)


def test_compression_check_result_accepts_chi_equal_to_one() -> None:
    result = CompressionCheckResult(nc_sd=100.0, lambda_0=0.0, chi=1.0, nc_rd=1000.0)
    assert result.chi == 1.0


@pytest.mark.parametrize("nc_rd", [0.0, -1.0, math.nan, math.inf])
def test_compression_check_result_rejects_invalid_nc_rd(nc_rd: float) -> None:
    with pytest.raises(ValueError):
        CompressionCheckResult(nc_sd=100.0, lambda_0=1.0, chi=0.5, nc_rd=nc_rd)


def test_compression_check_result_is_frozen() -> None:
    result = CompressionCheckResult(nc_sd=100.0, lambda_0=1.0, chi=0.5, nc_rd=1000.0)
    with pytest.raises(AttributeError):
        result.nc_sd = 200.0  # type: ignore[misc]
