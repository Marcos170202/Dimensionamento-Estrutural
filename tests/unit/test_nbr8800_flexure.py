"""Testes unitarios de openstruct.normative.nbr8800.flexure.

Ver docs/normative/NBR8800-RULES.md, RULE-IDs NBR8800-FLEX-001 a 004.
"""

from __future__ import annotations

import math

import pytest

from openstruct.normative.nbr8800.flexure import (
    FlexureCheckResult,
    check_lateral_torsional_buckling,
    flexural_resistance,
    lateral_torsional_buckling_moment,
    lateral_torsional_buckling_slenderness_limit,
    moment_gradient_factor_doubly_symmetric,
    warping_constant_i_section,
)

# -- moment_gradient_factor_doubly_symmetric (Cb) --------------------------------


def test_moment_gradient_factor_matches_formula() -> None:
    m_max, m_a, m_b, m_c = 100.0, 50.0, 75.0, 90.0
    expected = 12.5 * m_max / (2.5 * m_max + 3 * m_a + 4 * m_b + 3 * m_c)
    assert moment_gradient_factor_doubly_symmetric(m_max, m_a, m_b, m_c) == pytest.approx(
        expected
    )


def test_moment_gradient_factor_is_one_for_uniform_moment() -> None:
    # Momento constante ao longo do vao (Mmax=MA=MB=MC) -> Cb=1,0,
    # caso classico de referencia (sem gradiente de momento).
    assert moment_gradient_factor_doubly_symmetric(100.0, 100.0, 100.0, 100.0) == pytest.approx(
        1.0
    )


def test_moment_gradient_factor_accepts_zero_intermediate_moments() -> None:
    # MA/MB/MC podem ser zero (ex.: proximo a um apoio simples).
    result = moment_gradient_factor_doubly_symmetric(100.0, 0.0, 0.0, 0.0)
    assert result == pytest.approx(12.5 * 100.0 / (2.5 * 100.0))


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_moment_gradient_factor_rejects_invalid_m_max(value: float) -> None:
    with pytest.raises(ValueError):
        moment_gradient_factor_doubly_symmetric(value, 50.0, 75.0, 90.0)


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_moment_gradient_factor_rejects_invalid_m_a(value: float) -> None:
    with pytest.raises(ValueError):
        moment_gradient_factor_doubly_symmetric(100.0, value, 75.0, 90.0)


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_moment_gradient_factor_rejects_invalid_m_b(value: float) -> None:
    with pytest.raises(ValueError):
        moment_gradient_factor_doubly_symmetric(100.0, 50.0, value, 90.0)


@pytest.mark.parametrize("value", [-1.0, math.nan, math.inf])
def test_moment_gradient_factor_rejects_invalid_m_c(value: float) -> None:
    with pytest.raises(ValueError):
        moment_gradient_factor_doubly_symmetric(100.0, 50.0, 75.0, value)


# -- warping_constant_i_section (Cw) ----------------------------------------------


def test_warping_constant_i_section_matches_formula() -> None:
    iy, d, tf = 20e6, 400.0, 16.0
    expected = iy * (d - tf) ** 2 / 4.0
    assert warping_constant_i_section(iy, d, tf) == pytest.approx(expected)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_warping_constant_i_section_rejects_invalid_iy(value: float) -> None:
    with pytest.raises(ValueError):
        warping_constant_i_section(value, 400.0, 16.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_warping_constant_i_section_rejects_invalid_total_depth(value: float) -> None:
    with pytest.raises(ValueError):
        warping_constant_i_section(20e6, value, 16.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_warping_constant_i_section_rejects_invalid_flange_thickness(value: float) -> None:
    with pytest.raises(ValueError):
        warping_constant_i_section(20e6, 400.0, value)


def test_warping_constant_i_section_rejects_flange_thickness_larger_than_depth() -> None:
    with pytest.raises(ValueError):
        warping_constant_i_section(20e6, 16.0, 400.0)


def test_warping_constant_i_section_rejects_flange_thickness_equal_to_depth() -> None:
    with pytest.raises(ValueError):
        warping_constant_i_section(20e6, 400.0, 400.0)


# -- lateral_torsional_buckling_moment (Mcr) --------------------------------------


def test_lateral_torsional_buckling_moment_matches_formula() -> None:
    cb, e, iy, j, cw, lb = 1.0, 200_000.0, 20e6, 500e3, 737.28e9, 1500.0
    expected = (cb * math.pi**2 * e * iy / lb**2) * math.sqrt(
        (cw / iy) * (1.0 + 0.039 * j * lb**2 / cw)
    )
    assert lateral_torsional_buckling_moment(cb, e, iy, j, cw, lb) == pytest.approx(expected)


def test_lateral_torsional_buckling_moment_scales_linearly_with_cb() -> None:
    e, iy, j, cw, lb = 200_000.0, 20e6, 500e3, 737.28e9, 1500.0
    m1 = lateral_torsional_buckling_moment(1.0, e, iy, j, cw, lb)
    m2 = lateral_torsional_buckling_moment(2.0, e, iy, j, cw, lb)
    assert m2 == pytest.approx(2.0 * m1)


def test_lateral_torsional_buckling_moment_decreases_with_longer_unbraced_length() -> None:
    cb, e, iy, j, cw = 1.0, 200_000.0, 20e6, 500e3, 737.28e9
    m_short = lateral_torsional_buckling_moment(cb, e, iy, j, cw, 1500.0)
    m_long = lateral_torsional_buckling_moment(cb, e, iy, j, cw, 6000.0)
    assert m_long < m_short


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_moment_rejects_invalid_cb(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_moment(value, 200_000.0, 20e6, 500e3, 737.28e9, 1500.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_moment_rejects_invalid_elastic_modulus(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_moment(1.0, value, 20e6, 500e3, 737.28e9, 1500.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_moment_rejects_invalid_iy(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_moment(1.0, 200_000.0, value, 500e3, 737.28e9, 1500.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_moment_rejects_invalid_j(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_moment(1.0, 200_000.0, 20e6, value, 737.28e9, 1500.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_moment_rejects_invalid_cw(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_moment(1.0, 200_000.0, 20e6, 500e3, value, 1500.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_moment_rejects_invalid_length(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_moment(1.0, 200_000.0, 20e6, 500e3, 737.28e9, value)


# -- lateral_torsional_buckling_slenderness_limit (lambda_r) ----------------------


def test_lateral_torsional_buckling_slenderness_limit_matches_formula() -> None:
    cb, e, iy, j, cw, ry, mr = 1.0, 200_000.0, 20e6, 500e3, 737.28e9, 60.0, 217_350_000.0
    beta1 = mr / (e * j)
    expected = (1.38 * cb * math.sqrt(iy * j) / (ry * j * beta1)) * math.sqrt(
        1.0 + math.sqrt(1.0 + 27.0 * cw * beta1**2 / (cb**2 * iy))
    )
    assert lateral_torsional_buckling_slenderness_limit(
        cb, e, iy, j, cw, ry, mr
    ) == pytest.approx(expected)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_slenderness_limit_rejects_invalid_cb(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_slenderness_limit(
            value, 200_000.0, 20e6, 500e3, 737.28e9, 60.0, 217_350_000.0
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_slenderness_limit_rejects_invalid_elastic_modulus(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_slenderness_limit(
            1.0, value, 20e6, 500e3, 737.28e9, 60.0, 217_350_000.0
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_slenderness_limit_rejects_invalid_iy(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_slenderness_limit(
            1.0, 200_000.0, value, 500e3, 737.28e9, 60.0, 217_350_000.0
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_slenderness_limit_rejects_invalid_j(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_slenderness_limit(
            1.0, 200_000.0, 20e6, value, 737.28e9, 60.0, 217_350_000.0
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_slenderness_limit_rejects_invalid_cw(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_slenderness_limit(
            1.0, 200_000.0, 20e6, 500e3, value, 60.0, 217_350_000.0
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_slenderness_limit_rejects_invalid_ry(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_slenderness_limit(
            1.0, 200_000.0, 20e6, 500e3, 737.28e9, value, 217_350_000.0
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_lateral_torsional_buckling_slenderness_limit_rejects_invalid_mr(value: float) -> None:
    with pytest.raises(ValueError):
        lateral_torsional_buckling_slenderness_limit(
            1.0, 200_000.0, 20e6, 500e3, 737.28e9, 60.0, value
        )


# -- flexural_resistance (Mrd) -----------------------------------------------------


def test_flexural_resistance_plastic_branch_at_exact_boundary() -> None:
    mpl, mr, mcr, gamma_a1 = 345_000_000.0, 217_350_000.0, 100_000_000.0, 1.10
    lam_p, lam_r = 42.0, 123.0
    expected = mpl / gamma_a1
    assert flexural_resistance(mpl, mr, mcr, lam_p, lam_p, lam_r, gamma_a1) == pytest.approx(
        expected
    )


def test_flexural_resistance_inelastic_branch_just_above_lambda_p() -> None:
    mpl, mr, mcr, gamma_a1 = 345_000_000.0, 217_350_000.0, 100_000_000.0, 1.10
    lam_p, lam_r = 42.0, 123.0
    lam = lam_p + 1e-6
    expected = mpl / gamma_a1  # praticamente no limite -> ratio quase 0
    assert flexural_resistance(mpl, mr, mcr, lam, lam_p, lam_r, gamma_a1) == pytest.approx(
        expected, rel=1e-4
    )


def test_flexural_resistance_inelastic_branch_at_exact_lambda_r_boundary() -> None:
    # lambda == lambda_r exatamente -> "<=" inclui o limite no SEGUNDO
    # ramo (nao no terceiro) -- ver descontinuidade documentada.
    mpl, mr, mcr, gamma_a1 = 345_000_000.0, 217_350_000.0, 100_000_000.0, 1.10
    lam_p, lam_r = 42.0, 123.0
    expected = mr / gamma_a1
    assert flexural_resistance(mpl, mr, mcr, lam_r, lam_p, lam_r, gamma_a1) == pytest.approx(
        expected
    )


def test_flexural_resistance_elastic_branch_just_above_lambda_r() -> None:
    mpl, mr, mcr, gamma_a1 = 345_000_000.0, 217_350_000.0, 100_000_000.0, 1.10
    lam_p, lam_r = 42.0, 123.0
    lam = lam_r + 1e-6
    expected = mcr / gamma_a1
    assert flexural_resistance(mpl, mr, mcr, lam, lam_p, lam_r, gamma_a1) == pytest.approx(
        expected
    )


def test_flexural_resistance_is_monotonically_decreasing_with_slenderness() -> None:
    mpl, mr, mcr, gamma_a1 = 345_000_000.0, 217_350_000.0, 100_000_000.0, 1.10
    lam_p, lam_r = 42.0, 123.0
    values = [
        flexural_resistance(mpl, mr, mcr, lam, lam_p, lam_r, gamma_a1)
        for lam in [10.0, 30.0, lam_p, 80.0, lam_r, 150.0, 300.0]
    ]
    assert values == sorted(values, reverse=True)


def test_flexural_resistance_never_exceeds_plastic_value() -> None:
    mpl, mr, mcr, gamma_a1 = 345_000_000.0, 217_350_000.0, 100_000_000.0, 1.10
    lam_p, lam_r = 42.0, 123.0
    plastic_value = mpl / gamma_a1
    for lam in [1.0, lam_p, 80.0, lam_r, 300.0]:
        mrd = flexural_resistance(mpl, mr, mcr, lam, lam_p, lam_r, gamma_a1)
        assert mrd <= plastic_value or mrd == pytest.approx(plastic_value)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_resistance_rejects_invalid_plastic_moment(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_resistance(value, 217_350_000.0, 100_000_000.0, 60.0, 42.0, 123.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_resistance_rejects_invalid_residual_moment(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_resistance(345_000_000.0, value, 100_000_000.0, 60.0, 42.0, 123.0, 1.10)


def test_flexural_resistance_rejects_residual_moment_larger_than_plastic_moment() -> None:
    with pytest.raises(ValueError):
        flexural_resistance(100.0, 100.1, 50.0, 60.0, 42.0, 123.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_resistance_rejects_invalid_critical_moment(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_resistance(345_000_000.0, 217_350_000.0, value, 60.0, 42.0, 123.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_resistance_rejects_invalid_slenderness(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_resistance(345_000_000.0, 217_350_000.0, 100_000_000.0, value, 42.0, 123.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_resistance_rejects_invalid_slenderness_limit_p(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_resistance(345_000_000.0, 217_350_000.0, 100_000_000.0, 60.0, value, 123.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_resistance_rejects_invalid_slenderness_limit_r(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_resistance(345_000_000.0, 217_350_000.0, 100_000_000.0, 60.0, 42.0, value, 1.10)


def test_flexural_resistance_rejects_limit_r_smaller_than_limit_p() -> None:
    with pytest.raises(ValueError):
        flexural_resistance(345_000_000.0, 217_350_000.0, 100_000_000.0, 60.0, 123.0, 42.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_flexural_resistance_rejects_invalid_gamma_a1(value: float) -> None:
    with pytest.raises(ValueError):
        flexural_resistance(345_000_000.0, 217_350_000.0, 100_000_000.0, 60.0, 42.0, 123.0, value)


# -- check_lateral_torsional_buckling ----------------------------------------------

_E = 200_000.0
_FY = 345.0
_IY = 20e6
_J = 500e3
_D = 400.0
_TF = 16.0
_CW = _IY * (_D - _TF) ** 2 / 4.0
_W = 900e3
_Z = 1_000e3
_RY = 60.0
_GAMMA_A1 = 1.10


def test_check_lateral_torsional_buckling_matches_manual_calculation_plastic_branch() -> None:
    lb = 1500.0
    result = check_lateral_torsional_buckling(
        msd=1.0e6,
        fy=_FY,
        elastic_modulus=_E,
        elastic_section_modulus=_W,
        plastic_section_modulus=_Z,
        minor_axis_moment_of_inertia=_IY,
        torsion_constant=_J,
        warping_constant=_CW,
        radius_of_gyration_minor_axis=_RY,
        unbraced_length=lb,
        cb=1.0,
        resistance_factors_gamma_a1=_GAMMA_A1,
    )

    mr_ref = 0.7 * _FY * _W
    mpl_ref = _FY * _Z
    mcr_ref = lateral_torsional_buckling_moment(1.0, _E, _IY, _J, _CW, lb)
    lam_p_ref = 1.76 * math.sqrt(_E / _FY)
    lam_r_ref = lateral_torsional_buckling_slenderness_limit(1.0, _E, _IY, _J, _CW, _RY, mr_ref)
    lam_ref = lb / _RY
    assert lam_ref <= lam_p_ref  # confirma que este caso cai no ramo plastico
    mrd_ref = mpl_ref / _GAMMA_A1

    assert isinstance(result, FlexureCheckResult)
    assert result.mrd == pytest.approx(mrd_ref)
    assert result.utilization == pytest.approx(1.0e6 / mrd_ref)
    assert result.is_ok is True
    # mcr_ref/lam_r_ref calculados so para reforcar que o cenario e
    # coerente (nao usados diretamente na asserção do ramo plastico).
    assert mcr_ref > 0
    assert lam_r_ref > lam_p_ref


def test_check_lateral_torsional_buckling_matches_manual_calculation_inelastic_branch() -> None:
    lb = 4000.0
    result = check_lateral_torsional_buckling(
        msd=1.0,
        fy=_FY,
        elastic_modulus=_E,
        elastic_section_modulus=_W,
        plastic_section_modulus=_Z,
        minor_axis_moment_of_inertia=_IY,
        torsion_constant=_J,
        warping_constant=_CW,
        radius_of_gyration_minor_axis=_RY,
        unbraced_length=lb,
        cb=1.0,
        resistance_factors_gamma_a1=_GAMMA_A1,
    )

    mr_ref = 0.7 * _FY * _W
    mpl_ref = _FY * _Z
    lam_p_ref = 1.76 * math.sqrt(_E / _FY)
    lam_r_ref = lateral_torsional_buckling_slenderness_limit(1.0, _E, _IY, _J, _CW, _RY, mr_ref)
    lam_ref = lb / _RY
    assert lam_p_ref < lam_ref <= lam_r_ref  # confirma o ramo esperado
    ratio = (lam_ref - lam_p_ref) / (lam_r_ref - lam_p_ref)
    mrd_ref = (mpl_ref - (mpl_ref - mr_ref) * ratio) / _GAMMA_A1

    assert result.mrd == pytest.approx(mrd_ref)


def test_check_lateral_torsional_buckling_matches_manual_calculation_elastic_branch() -> None:
    lb = 12000.0
    result = check_lateral_torsional_buckling(
        msd=1.0,
        fy=_FY,
        elastic_modulus=_E,
        elastic_section_modulus=_W,
        plastic_section_modulus=_Z,
        minor_axis_moment_of_inertia=_IY,
        torsion_constant=_J,
        warping_constant=_CW,
        radius_of_gyration_minor_axis=_RY,
        unbraced_length=lb,
        cb=1.0,
        resistance_factors_gamma_a1=_GAMMA_A1,
    )

    mr_ref = 0.7 * _FY * _W
    mcr_ref = lateral_torsional_buckling_moment(1.0, _E, _IY, _J, _CW, lb)
    lam_r_ref = lateral_torsional_buckling_slenderness_limit(1.0, _E, _IY, _J, _CW, _RY, mr_ref)
    lam_ref = lb / _RY
    assert lam_ref > lam_r_ref  # confirma o ramo esperado
    mrd_ref = mcr_ref / _GAMMA_A1

    assert result.mrd == pytest.approx(mrd_ref)


def test_check_lateral_torsional_buckling_longer_unbraced_length_reduces_mrd() -> None:
    kwargs = dict(
        msd=1.0,
        fy=_FY,
        elastic_modulus=_E,
        elastic_section_modulus=_W,
        plastic_section_modulus=_Z,
        minor_axis_moment_of_inertia=_IY,
        torsion_constant=_J,
        warping_constant=_CW,
        radius_of_gyration_minor_axis=_RY,
        cb=1.0,
        resistance_factors_gamma_a1=_GAMMA_A1,
    )
    short = check_lateral_torsional_buckling(unbraced_length=2000.0, **kwargs)
    long = check_lateral_torsional_buckling(unbraced_length=10000.0, **kwargs)
    assert long.mrd < short.mrd


def test_check_lateral_torsional_buckling_higher_cb_increases_or_maintains_mrd() -> None:
    # Cb maior -> Mcr maior -> Mrd nunca diminui (pode saturar no ramo
    # plastico, que independe de Cb).
    kwargs = dict(
        msd=1.0,
        fy=_FY,
        elastic_modulus=_E,
        elastic_section_modulus=_W,
        plastic_section_modulus=_Z,
        minor_axis_moment_of_inertia=_IY,
        torsion_constant=_J,
        warping_constant=_CW,
        radius_of_gyration_minor_axis=_RY,
        unbraced_length=8000.0,
        resistance_factors_gamma_a1=_GAMMA_A1,
    )
    low_cb = check_lateral_torsional_buckling(cb=1.0, **kwargs)
    high_cb = check_lateral_torsional_buckling(cb=1.75, **kwargs)
    assert high_cb.mrd >= low_cb.mrd


def test_check_lateral_torsional_buckling_is_ok_false_when_overloaded() -> None:
    result = check_lateral_torsional_buckling(
        msd=1.0e12,
        fy=_FY,
        elastic_modulus=_E,
        elastic_section_modulus=_W,
        plastic_section_modulus=_Z,
        minor_axis_moment_of_inertia=_IY,
        torsion_constant=_J,
        warping_constant=_CW,
        radius_of_gyration_minor_axis=_RY,
        unbraced_length=1500.0,
        cb=1.0,
        resistance_factors_gamma_a1=_GAMMA_A1,
    )
    assert result.is_ok is False
    assert result.utilization > 1.0


def test_check_lateral_torsional_buckling_rejects_non_finite_msd() -> None:
    with pytest.raises(ValueError):
        check_lateral_torsional_buckling(
            msd=math.nan,
            fy=_FY,
            elastic_modulus=_E,
            elastic_section_modulus=_W,
            plastic_section_modulus=_Z,
            minor_axis_moment_of_inertia=_IY,
            torsion_constant=_J,
            warping_constant=_CW,
            radius_of_gyration_minor_axis=_RY,
            unbraced_length=1500.0,
            cb=1.0,
            resistance_factors_gamma_a1=_GAMMA_A1,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_lateral_torsional_buckling_rejects_invalid_fy(value: float) -> None:
    with pytest.raises(ValueError):
        check_lateral_torsional_buckling(
            msd=1.0,
            fy=value,
            elastic_modulus=_E,
            elastic_section_modulus=_W,
            plastic_section_modulus=_Z,
            minor_axis_moment_of_inertia=_IY,
            torsion_constant=_J,
            warping_constant=_CW,
            radius_of_gyration_minor_axis=_RY,
            unbraced_length=1500.0,
            cb=1.0,
            resistance_factors_gamma_a1=_GAMMA_A1,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_lateral_torsional_buckling_rejects_invalid_elastic_section_modulus(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        check_lateral_torsional_buckling(
            msd=1.0,
            fy=_FY,
            elastic_modulus=_E,
            elastic_section_modulus=value,
            plastic_section_modulus=_Z,
            minor_axis_moment_of_inertia=_IY,
            torsion_constant=_J,
            warping_constant=_CW,
            radius_of_gyration_minor_axis=_RY,
            unbraced_length=1500.0,
            cb=1.0,
            resistance_factors_gamma_a1=_GAMMA_A1,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_lateral_torsional_buckling_rejects_invalid_plastic_section_modulus(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        check_lateral_torsional_buckling(
            msd=1.0,
            fy=_FY,
            elastic_modulus=_E,
            elastic_section_modulus=_W,
            plastic_section_modulus=value,
            minor_axis_moment_of_inertia=_IY,
            torsion_constant=_J,
            warping_constant=_CW,
            radius_of_gyration_minor_axis=_RY,
            unbraced_length=1500.0,
            cb=1.0,
            resistance_factors_gamma_a1=_GAMMA_A1,
        )


def test_check_lateral_torsional_buckling_rejects_plastic_modulus_smaller_than_elastic() -> None:
    with pytest.raises(ValueError):
        check_lateral_torsional_buckling(
            msd=1.0,
            fy=_FY,
            elastic_modulus=_E,
            elastic_section_modulus=1000e3,
            plastic_section_modulus=900e3,
            minor_axis_moment_of_inertia=_IY,
            torsion_constant=_J,
            warping_constant=_CW,
            radius_of_gyration_minor_axis=_RY,
            unbraced_length=1500.0,
            cb=1.0,
            resistance_factors_gamma_a1=_GAMMA_A1,
        )


def test_check_lateral_torsional_buckling_accepts_plastic_modulus_equal_to_elastic() -> None:
    # Caso degenerado (fator de forma exatamente 1) -> aceito ("<"
    # rejeita, nao "<="), mesmo sendo fisicamente incomum.
    result = check_lateral_torsional_buckling(
        msd=1.0,
        fy=_FY,
        elastic_modulus=_E,
        elastic_section_modulus=_W,
        plastic_section_modulus=_W,
        minor_axis_moment_of_inertia=_IY,
        torsion_constant=_J,
        warping_constant=_CW,
        radius_of_gyration_minor_axis=_RY,
        unbraced_length=1500.0,
        cb=1.0,
        resistance_factors_gamma_a1=_GAMMA_A1,
    )
    assert result.is_ok is True


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_lateral_torsional_buckling_rejects_invalid_radius_of_gyration(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        check_lateral_torsional_buckling(
            msd=1.0,
            fy=_FY,
            elastic_modulus=_E,
            elastic_section_modulus=_W,
            plastic_section_modulus=_Z,
            minor_axis_moment_of_inertia=_IY,
            torsion_constant=_J,
            warping_constant=_CW,
            radius_of_gyration_minor_axis=value,
            unbraced_length=1500.0,
            cb=1.0,
            resistance_factors_gamma_a1=_GAMMA_A1,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_lateral_torsional_buckling_rejects_invalid_unbraced_length(value: float) -> None:
    with pytest.raises(ValueError):
        check_lateral_torsional_buckling(
            msd=1.0,
            fy=_FY,
            elastic_modulus=_E,
            elastic_section_modulus=_W,
            plastic_section_modulus=_Z,
            minor_axis_moment_of_inertia=_IY,
            torsion_constant=_J,
            warping_constant=_CW,
            radius_of_gyration_minor_axis=_RY,
            unbraced_length=value,
            cb=1.0,
            resistance_factors_gamma_a1=_GAMMA_A1,
        )


# -- FlexureCheckResult: validacao direta e imutabilidade -------------------------


def test_flexure_check_result_rejects_non_finite_msd() -> None:
    with pytest.raises(ValueError):
        FlexureCheckResult(msd=math.nan, mrd=1000.0)


@pytest.mark.parametrize("mrd", [0.0, -1.0, math.nan, math.inf])
def test_flexure_check_result_rejects_invalid_mrd(mrd: float) -> None:
    with pytest.raises(ValueError):
        FlexureCheckResult(msd=100.0, mrd=mrd)


def test_flexure_check_result_accepts_negative_msd() -> None:
    # Msd pode ser negativo (sentido oposto do momento) -> so a
    # magnitude importa fisicamente, mesma logica de ShearCheckResult.
    result = FlexureCheckResult(msd=-100.0, mrd=1000.0)
    assert result.sd == -100.0


def test_flexure_check_result_is_ok_ignores_sign_caller_must_pass_magnitude() -> None:
    # ACHADO DO CODE REVIEW AGENT (documentado, nao "corrigido" pela
    # classe): is_ok/utilization (herdados de CheckResult) comparam
    # msd<=mrd diretamente, SEM valor absoluto. Um msd muito negativo
    # (momento no sentido oposto, ex.: regiao de momento negativo de
    # uma viga continua) e sempre "menor" que mrd positivo -> is_ok
    # fica True mesmo com |msd| >> mrd (nao conservador se o chamador
    # nao passar abs(msd)). Ver ATENCAO na docstring de
    # FlexureCheckResult/check_lateral_torsional_buckling.
    result = FlexureCheckResult(msd=-3.0 * 1000.0, mrd=1000.0)
    assert result.is_ok is True
    assert result.utilization < 0


def test_flexure_check_result_sd_rd_aliases() -> None:
    result = FlexureCheckResult(msd=100.0, mrd=1000.0)
    assert result.sd == result.msd
    assert result.rd == result.mrd


def test_flexure_check_result_is_frozen() -> None:
    result = FlexureCheckResult(msd=100.0, mrd=1000.0)
    with pytest.raises(AttributeError):
        result.msd = 200.0  # type: ignore[misc]
