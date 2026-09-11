"""Testes unitarios de openstruct.normative.nbr8800.combined_forces.

Ver docs/normative/NBR8800-RULES.md, RULE-IDs NBR8800-COMB-001 e 002.
"""

from __future__ import annotations

import math

import pytest

from openstruct.normative.nbr8800.combined_forces import (
    CombinedForcesCheckResult,
    axial_bending_interaction_ratio,
    check_axial_and_bending_interaction,
)

# -- axial_bending_interaction_ratio ----------------------------------------------


def test_axial_bending_interaction_ratio_uses_equation_a_when_ratio_at_or_above_0_2() -> None:
    # Nsd/Nrd = 0,625 >= 0,2 -> equacao a).
    n_sd, n_rd = 500_000.0, 800_000.0
    mx_sd, mx_rd = 100e6, 300e6
    my_sd, my_rd = 20e6, 80e6
    expected = n_sd / n_rd + (8.0 / 9.0) * (mx_sd / mx_rd + my_sd / my_rd)
    assert axial_bending_interaction_ratio(
        n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd
    ) == pytest.approx(expected)


def test_axial_bending_interaction_ratio_uses_equation_b_when_ratio_below_0_2() -> None:
    # Nsd/Nrd = 0,125 < 0,2 -> equacao b).
    n_sd, n_rd = 100_000.0, 800_000.0
    mx_sd, mx_rd = 100e6, 300e6
    my_sd, my_rd = 20e6, 80e6
    expected = n_sd / (2.0 * n_rd) + (mx_sd / mx_rd + my_sd / my_rd)
    assert axial_bending_interaction_ratio(
        n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd
    ) == pytest.approx(expected)


def test_axial_bending_interaction_ratio_uses_equation_a_at_exact_boundary() -> None:
    # Nsd/Nrd == 0,2 exatamente -> ">=" inclui o limite na equacao a).
    n_rd = 800_000.0
    n_sd = 0.2 * n_rd
    mx_sd, mx_rd = 100e6, 300e6
    my_sd, my_rd = 20e6, 80e6
    expected_a = n_sd / n_rd + (8.0 / 9.0) * (mx_sd / mx_rd + my_sd / my_rd)
    expected_b = n_sd / (2.0 * n_rd) + (mx_sd / mx_rd + my_sd / my_rd)
    result = axial_bending_interaction_ratio(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)
    assert result == pytest.approx(expected_a)
    assert result != pytest.approx(expected_b)


def test_axial_bending_interaction_ratio_accepts_zero_moments() -> None:
    # Barra sem momento em nenhum dos eixos (esforco axial puro) ->
    # o termo de flexao some, sobra so a parcela axial.
    n_sd, n_rd = 500_000.0, 800_000.0
    result = axial_bending_interaction_ratio(n_sd, n_rd, 0.0, 300e6, 0.0, 80e6)
    assert result == pytest.approx(n_sd / n_rd)


def test_axial_bending_interaction_ratio_accepts_zero_axial_force() -> None:
    # Barra sem forca axial (flexao pura) -> Nsd/Nrd=0 < 0,2 -> equacao b).
    mx_sd, mx_rd = 100e6, 300e6
    my_sd, my_rd = 20e6, 80e6
    result = axial_bending_interaction_ratio(0.0, 800_000.0, mx_sd, mx_rd, my_sd, my_rd)
    expected = mx_sd / mx_rd + my_sd / my_rd
    assert result == pytest.approx(expected)


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_axial_bending_interaction_ratio_rejects_invalid_n_sd(value: float) -> None:
    with pytest.raises(ValueError):
        axial_bending_interaction_ratio(value, 800_000.0, 100e6, 300e6, 20e6, 80e6)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_axial_bending_interaction_ratio_rejects_invalid_n_rd(value: float) -> None:
    with pytest.raises(ValueError):
        axial_bending_interaction_ratio(500_000.0, value, 100e6, 300e6, 20e6, 80e6)


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_axial_bending_interaction_ratio_rejects_invalid_mx_sd(value: float) -> None:
    with pytest.raises(ValueError):
        axial_bending_interaction_ratio(500_000.0, 800_000.0, value, 300e6, 20e6, 80e6)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_axial_bending_interaction_ratio_rejects_invalid_mx_rd(value: float) -> None:
    with pytest.raises(ValueError):
        axial_bending_interaction_ratio(500_000.0, 800_000.0, 100e6, value, 20e6, 80e6)


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_axial_bending_interaction_ratio_rejects_invalid_my_sd(value: float) -> None:
    with pytest.raises(ValueError):
        axial_bending_interaction_ratio(500_000.0, 800_000.0, 100e6, 300e6, value, 80e6)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_axial_bending_interaction_ratio_rejects_invalid_my_rd(value: float) -> None:
    with pytest.raises(ValueError):
        axial_bending_interaction_ratio(500_000.0, 800_000.0, 100e6, 300e6, 20e6, value)


# -- check_axial_and_bending_interaction ------------------------------------------


def test_check_axial_and_bending_interaction_matches_manual_calculation() -> None:
    n_sd, n_rd = 500_000.0, 800_000.0
    mx_sd, mx_rd = 100e6, 300e6
    my_sd, my_rd = 20e6, 80e6

    result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)
    ratio_ref = n_sd / n_rd + (8.0 / 9.0) * (mx_sd / mx_rd + my_sd / my_rd)

    assert isinstance(result, CombinedForcesCheckResult)
    assert result.interaction_ratio == pytest.approx(ratio_ref)
    assert result.utilization == pytest.approx(ratio_ref)
    assert result.rd == 1.0
    assert result.sd == result.interaction_ratio


def test_check_axial_and_bending_interaction_is_ok_true_when_within_limit() -> None:
    result = check_axial_and_bending_interaction(100_000.0, 800_000.0, 10e6, 300e6, 5e6, 80e6)
    assert result.is_ok is True
    assert result.interaction_ratio < 1.0


def test_check_axial_and_bending_interaction_is_ok_false_when_overloaded() -> None:
    result = check_axial_and_bending_interaction(700_000.0, 800_000.0, 250e6, 300e6, 60e6, 80e6)
    assert result.is_ok is False
    assert result.interaction_ratio > 1.0


def test_check_axial_and_bending_interaction_is_ok_true_at_exact_boundary() -> None:
    # Escolhido para dar interaction_ratio == 1,0 exatamente (equacao b,
    # Nsd/Nrd=0,1<0,2): 0,1/2 + Mx_sd/Mx_rd = 1,0 -> Mx_sd/Mx_rd=0,95.
    n_rd = 800_000.0
    n_sd = 0.1 * n_rd
    mx_rd = 300e6
    mx_sd = 0.95 * mx_rd
    result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, 0.0, 80e6)
    assert result.interaction_ratio == pytest.approx(1.0)
    assert result.is_ok is True


# -- CombinedForcesCheckResult: validacao direta e imutabilidade -----------------


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_combined_forces_check_result_rejects_invalid_n_sd(value: float) -> None:
    with pytest.raises(ValueError):
        CombinedForcesCheckResult(
            n_sd=value, n_rd=800_000.0, mx_sd=10e6, mx_rd=300e6, my_sd=5e6, my_rd=80e6,
            interaction_ratio=0.5,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_combined_forces_check_result_rejects_invalid_n_rd(value: float) -> None:
    with pytest.raises(ValueError):
        CombinedForcesCheckResult(
            n_sd=100_000.0, n_rd=value, mx_sd=10e6, mx_rd=300e6, my_sd=5e6, my_rd=80e6,
            interaction_ratio=0.5,
        )


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_combined_forces_check_result_rejects_invalid_mx_sd(value: float) -> None:
    with pytest.raises(ValueError):
        CombinedForcesCheckResult(
            n_sd=100_000.0, n_rd=800_000.0, mx_sd=value, mx_rd=300e6, my_sd=5e6, my_rd=80e6,
            interaction_ratio=0.5,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_combined_forces_check_result_rejects_invalid_mx_rd(value: float) -> None:
    with pytest.raises(ValueError):
        CombinedForcesCheckResult(
            n_sd=100_000.0, n_rd=800_000.0, mx_sd=10e6, mx_rd=value, my_sd=5e6, my_rd=80e6,
            interaction_ratio=0.5,
        )


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_combined_forces_check_result_rejects_invalid_my_sd(value: float) -> None:
    with pytest.raises(ValueError):
        CombinedForcesCheckResult(
            n_sd=100_000.0, n_rd=800_000.0, mx_sd=10e6, mx_rd=300e6, my_sd=value, my_rd=80e6,
            interaction_ratio=0.5,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_combined_forces_check_result_rejects_invalid_my_rd(value: float) -> None:
    with pytest.raises(ValueError):
        CombinedForcesCheckResult(
            n_sd=100_000.0, n_rd=800_000.0, mx_sd=10e6, mx_rd=300e6, my_sd=5e6, my_rd=value,
            interaction_ratio=0.5,
        )


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_combined_forces_check_result_rejects_invalid_interaction_ratio(value: float) -> None:
    with pytest.raises(ValueError):
        CombinedForcesCheckResult(
            n_sd=100_000.0, n_rd=800_000.0, mx_sd=10e6, mx_rd=300e6, my_sd=5e6, my_rd=80e6,
            interaction_ratio=value,
        )


def test_combined_forces_check_result_accepts_zero_interaction_ratio() -> None:
    result = CombinedForcesCheckResult(
        n_sd=0.0, n_rd=800_000.0, mx_sd=0.0, mx_rd=300e6, my_sd=0.0, my_rd=80e6,
        interaction_ratio=0.0,
    )
    assert result.interaction_ratio == 0.0
    assert result.is_ok is True


def test_combined_forces_check_result_is_frozen() -> None:
    result = CombinedForcesCheckResult(
        n_sd=100_000.0, n_rd=800_000.0, mx_sd=10e6, mx_rd=300e6, my_sd=5e6, my_rd=80e6,
        interaction_ratio=0.5,
    )
    with pytest.raises(AttributeError):
        result.interaction_ratio = 0.9  # type: ignore[misc]
