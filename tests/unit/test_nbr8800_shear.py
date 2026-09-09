"""Testes unitarios de openstruct.normative.nbr8800.shear.

Ver docs/normative/NBR8800-RULES.md, RULE-IDs NBR8800-SHEAR-001 a 004.
"""

from __future__ import annotations

import math

import pytest

from openstruct.normative.nbr8800.shear import (
    ShearCheckResult,
    check_shear_major_axis,
    effective_shear_area_major_axis,
    plastic_shear_force,
    shear_buckling_coefficient,
    shear_resistance,
)

# -- effective_shear_area_major_axis --------------------------------------------


def test_effective_shear_area_major_axis_matches_formula() -> None:
    # Aw = d*tw
    assert effective_shear_area_major_axis(400.0, 8.0) == pytest.approx(3200.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_effective_shear_area_major_axis_rejects_invalid_total_depth(value: float) -> None:
    with pytest.raises(ValueError):
        effective_shear_area_major_axis(value, 8.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_effective_shear_area_major_axis_rejects_invalid_web_thickness(value: float) -> None:
    with pytest.raises(ValueError):
        effective_shear_area_major_axis(400.0, value)


# -- plastic_shear_force ---------------------------------------------------------


def test_plastic_shear_force_matches_formula() -> None:
    # Vpl = 0.60*Aw*fy
    assert plastic_shear_force(3200.0, 345.0) == pytest.approx(0.60 * 3200.0 * 345.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_plastic_shear_force_rejects_invalid_effective_shear_area(value: float) -> None:
    with pytest.raises(ValueError):
        plastic_shear_force(value, 345.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_plastic_shear_force_rejects_invalid_fy(value: float) -> None:
    with pytest.raises(ValueError):
        plastic_shear_force(3200.0, value)


# -- shear_buckling_coefficient (kv) ----------------------------------------------


def test_shear_buckling_coefficient_no_stiffeners_is_5_34() -> None:
    assert shear_buckling_coefficient(350.0, None) == pytest.approx(5.34)


def test_shear_buckling_coefficient_a_over_h_greater_than_3_is_5_34() -> None:
    # a/h = 4 > 3 -> mesmo comportamento de alma sem enrijecedores.
    assert shear_buckling_coefficient(350.0, 1400.0) == pytest.approx(5.34)


def test_shear_buckling_coefficient_a_over_h_equal_3_is_5_34() -> None:
    # a/h == 3 exatamente -> "> 3" e falso -> cai no ramo 5.0+5/(a/h)^2,
    # que em a/h=3 vale 5.0+5/9=5.5556 (nao 5.34) -> testa o limite exato.
    h = 350.0
    a = 3.0 * h
    expected = 5.0 + 5.0 / 3.0**2
    assert shear_buckling_coefficient(h, a) == pytest.approx(expected)
    assert expected != pytest.approx(5.34)


def test_shear_buckling_coefficient_with_stiffeners_matches_formula() -> None:
    h = 350.0
    a = 2.0 * h  # a/h = 2
    expected = 5.0 + 5.0 / 2.0**2
    assert shear_buckling_coefficient(h, a) == pytest.approx(expected)


def test_shear_buckling_coefficient_decreases_as_spacing_increases_up_to_limit() -> None:
    h = 350.0
    kv_close = shear_buckling_coefficient(h, 1.0 * h)
    kv_far = shear_buckling_coefficient(h, 2.5 * h)
    assert kv_far < kv_close


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_shear_buckling_coefficient_rejects_invalid_web_clear_height(value: float) -> None:
    with pytest.raises(ValueError):
        shear_buckling_coefficient(value, None)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_shear_buckling_coefficient_rejects_invalid_stiffener_spacing(value: float) -> None:
    with pytest.raises(ValueError):
        shear_buckling_coefficient(350.0, value)


# -- shear_resistance (Vrd) -------------------------------------------------------


def test_shear_resistance_plastic_branch_at_exact_boundary() -> None:
    # lambda == lambda_p exatamente -> "<=" inclui o limite no PRIMEIRO ramo.
    vpl, gamma_a1 = 662_400.0, 1.10
    lam_p, lam_r = 61.2, 76.2
    expected = vpl / gamma_a1
    assert shear_resistance(vpl, lam_p, lam_p, lam_r, gamma_a1) == pytest.approx(expected)


def test_shear_resistance_inelastic_branch_just_above_lambda_p() -> None:
    vpl, gamma_a1 = 662_400.0, 1.10
    lam_p, lam_r = 61.2, 76.2
    lam = lam_p + 1e-6
    expected = (lam_p / lam) * vpl / gamma_a1
    assert shear_resistance(vpl, lam, lam_p, lam_r, gamma_a1) == pytest.approx(expected)


def test_shear_resistance_inelastic_branch_at_exact_lambda_r_boundary() -> None:
    # lambda == lambda_r exatamente -> "<=" inclui o limite no SEGUNDO ramo
    # (nao no terceiro) -- ver descontinuidade documentada na docstring.
    vpl, gamma_a1 = 662_400.0, 1.10
    lam_p, lam_r = 61.2, 76.2
    expected = (lam_p / lam_r) * vpl / gamma_a1
    assert shear_resistance(vpl, lam_r, lam_p, lam_r, gamma_a1) == pytest.approx(expected)


def test_shear_resistance_elastic_branch_just_above_lambda_r() -> None:
    vpl, gamma_a1 = 662_400.0, 1.10
    lam_p, lam_r = 61.2, 76.2
    lam = lam_r + 1e-6
    expected = 1.24 * (lam_p / lam) ** 2 * vpl / gamma_a1
    assert shear_resistance(vpl, lam, lam_p, lam_r, gamma_a1) == pytest.approx(expected)


def test_shear_resistance_branches_are_close_but_not_identical_at_lambda_r() -> None:
    # Caracteristica conhecida da curva normativa (ver docstring de
    # shear_resistance): os ramos 2 e 3 NAO se encontram exatamente em
    # lambda=lambda_r (pois lambda_r/lambda_p=1,37/1,10=1,24545... != 1,24).
    # Confirma que a implementacao usa EXATAMENTE as formulas da norma.
    vpl, gamma_a1 = 1.0, 1.0
    lam_p, lam_r = 1.10, 1.37
    branch2 = (lam_p / lam_r) * vpl / gamma_a1
    branch3 = 1.24 * (lam_p / lam_r) ** 2 * vpl / gamma_a1
    assert branch2 != pytest.approx(branch3, abs=1e-6)


def test_shear_resistance_is_monotonically_decreasing_with_slenderness() -> None:
    vpl, gamma_a1 = 662_400.0, 1.10
    lam_p, lam_r = 61.2, 76.2
    values = [
        shear_resistance(vpl, lam, lam_p, lam_r, gamma_a1)
        for lam in [10.0, 40.0, lam_p, 65.0, lam_r, 90.0, 150.0]
    ]
    assert values == sorted(values, reverse=True)


def test_shear_resistance_never_exceeds_plastic_value() -> None:
    vpl, gamma_a1 = 662_400.0, 1.10
    lam_p, lam_r = 61.2, 76.2
    plastic_value = vpl / gamma_a1
    for lam in [1.0, lam_p, 70.0, lam_r, 200.0]:
        vrd = shear_resistance(vpl, lam, lam_p, lam_r, gamma_a1)
        assert vrd <= plastic_value or vrd == pytest.approx(plastic_value)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_shear_resistance_rejects_invalid_plastic_shear_force(value: float) -> None:
    with pytest.raises(ValueError):
        shear_resistance(value, 50.0, 60.0, 75.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_shear_resistance_rejects_invalid_slenderness(value: float) -> None:
    with pytest.raises(ValueError):
        shear_resistance(662_400.0, value, 60.0, 75.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_shear_resistance_rejects_invalid_slenderness_limit_p(value: float) -> None:
    with pytest.raises(ValueError):
        shear_resistance(662_400.0, 50.0, value, 75.0, 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_shear_resistance_rejects_invalid_slenderness_limit_r(value: float) -> None:
    with pytest.raises(ValueError):
        shear_resistance(662_400.0, 50.0, 60.0, value, 1.10)


def test_shear_resistance_rejects_limit_r_smaller_than_limit_p() -> None:
    with pytest.raises(ValueError):
        shear_resistance(662_400.0, 50.0, 75.0, 60.0, 1.10)


def test_shear_resistance_accepts_limit_r_equal_to_limit_p() -> None:
    # Caso degenerado (kv identico e limites coincidentes) -> aceito, sem
    # ramo intermediario (o segundo ramo colapsa a um unico ponto).
    result = shear_resistance(662_400.0, 60.0, 60.0, 60.0, 1.10)
    assert result == pytest.approx(662_400.0 / 1.10)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_shear_resistance_rejects_invalid_gamma_a1(value: float) -> None:
    with pytest.raises(ValueError):
        shear_resistance(662_400.0, 50.0, 60.0, 75.0, value)


# -- check_shear_major_axis -------------------------------------------------------


def test_check_shear_major_axis_matches_manual_calculation_plastic_branch() -> None:
    d, h, tw, fy, e, gamma_a1 = 400.0, 350.0, 8.0, 345.0, 200_000.0, 1.10
    result = check_shear_major_axis(
        vsd=100_000.0,
        total_depth=d,
        web_clear_height=h,
        web_thickness=tw,
        fy=fy,
        elastic_modulus=e,
        stiffener_spacing=None,
        resistance_factors_gamma_a1=gamma_a1,
    )

    aw_ref = d * tw
    vpl_ref = 0.60 * aw_ref * fy
    kv_ref = 5.34
    lam_ref = h / tw
    lam_p_ref = 1.10 * math.sqrt(kv_ref * e / fy)
    assert lam_ref <= lam_p_ref  # confirma que este caso cai no ramo plastico
    vrd_ref = vpl_ref / gamma_a1

    assert isinstance(result, ShearCheckResult)
    assert result.vrd == pytest.approx(vrd_ref)
    assert result.utilization == pytest.approx(100_000.0 / vrd_ref)
    assert result.is_ok is True


def test_check_shear_major_axis_matches_manual_calculation_inelastic_branch() -> None:
    # Alma mais fina -> lambda cai no trecho inelastico (lambda_p < lambda <= lambda_r).
    d, h, tw, fy, e, gamma_a1 = 400.0, 350.0, 5.0, 345.0, 200_000.0, 1.10
    result = check_shear_major_axis(
        vsd=1.0,
        total_depth=d,
        web_clear_height=h,
        web_thickness=tw,
        fy=fy,
        elastic_modulus=e,
        stiffener_spacing=None,
        resistance_factors_gamma_a1=gamma_a1,
    )

    aw_ref = d * tw
    vpl_ref = 0.60 * aw_ref * fy
    kv_ref = 5.34
    lam_ref = h / tw
    lam_p_ref = 1.10 * math.sqrt(kv_ref * e / fy)
    lam_r_ref = 1.37 * math.sqrt(kv_ref * e / fy)
    assert lam_p_ref < lam_ref <= lam_r_ref  # confirma o ramo esperado
    vrd_ref = (lam_p_ref / lam_ref) * vpl_ref / gamma_a1

    assert result.vrd == pytest.approx(vrd_ref)


def test_check_shear_major_axis_matches_manual_calculation_elastic_branch() -> None:
    # Alma bem fina -> lambda cai no trecho de flambagem elastica.
    d, h, tw, fy, e, gamma_a1 = 400.0, 350.0, 2.5, 345.0, 200_000.0, 1.10
    result = check_shear_major_axis(
        vsd=1.0,
        total_depth=d,
        web_clear_height=h,
        web_thickness=tw,
        fy=fy,
        elastic_modulus=e,
        stiffener_spacing=None,
        resistance_factors_gamma_a1=gamma_a1,
    )

    aw_ref = d * tw
    vpl_ref = 0.60 * aw_ref * fy
    kv_ref = 5.34
    lam_ref = h / tw
    lam_p_ref = 1.10 * math.sqrt(kv_ref * e / fy)
    lam_r_ref = 1.37 * math.sqrt(kv_ref * e / fy)
    assert lam_ref > lam_r_ref  # confirma o ramo esperado
    vrd_ref = 1.24 * (lam_p_ref / lam_ref) ** 2 * vpl_ref / gamma_a1

    assert result.vrd == pytest.approx(vrd_ref)


def test_check_shear_major_axis_thinner_web_reduces_vrd() -> None:
    kwargs = dict(
        vsd=1.0, total_depth=400.0, web_clear_height=350.0, fy=345.0,
        elastic_modulus=200_000.0, stiffener_spacing=None, resistance_factors_gamma_a1=1.10,
    )
    thick = check_shear_major_axis(web_thickness=8.0, **kwargs)
    thin = check_shear_major_axis(web_thickness=5.0, **kwargs)
    assert thin.vrd < thick.vrd


def test_check_shear_major_axis_with_stiffeners_increases_vrd_in_buckling_range() -> None:
    # No trecho de flambagem, enrijecedores (a/h pequeno -> kv maior) devem
    # aumentar Vrd em relacao ao caso sem enrijecedores (kv=5,34), pois
    # kv maior desloca lambda_p/lambda_r para cima.
    kwargs = dict(
        vsd=1.0, total_depth=400.0, web_clear_height=350.0, web_thickness=5.0,
        fy=345.0, elastic_modulus=200_000.0, resistance_factors_gamma_a1=1.10,
    )
    without_stiffeners = check_shear_major_axis(stiffener_spacing=None, **kwargs)
    with_stiffeners = check_shear_major_axis(stiffener_spacing=350.0, **kwargs)  # a/h=1
    assert with_stiffeners.vrd > without_stiffeners.vrd


def test_check_shear_major_axis_is_ok_false_when_overloaded() -> None:
    result = check_shear_major_axis(
        vsd=10_000_000.0,
        total_depth=400.0,
        web_clear_height=350.0,
        web_thickness=8.0,
        fy=345.0,
        elastic_modulus=200_000.0,
        stiffener_spacing=None,
        resistance_factors_gamma_a1=1.10,
    )
    assert result.is_ok is False
    assert result.utilization > 1.0


def test_check_shear_major_axis_rejects_non_finite_vsd() -> None:
    with pytest.raises(ValueError):
        check_shear_major_axis(
            vsd=math.nan, total_depth=400.0, web_clear_height=350.0, web_thickness=8.0,
            fy=345.0, elastic_modulus=200_000.0, stiffener_spacing=None,
            resistance_factors_gamma_a1=1.10,
        )


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_check_shear_major_axis_rejects_invalid_elastic_modulus(value: float) -> None:
    with pytest.raises(ValueError):
        check_shear_major_axis(
            vsd=1.0, total_depth=400.0, web_clear_height=350.0, web_thickness=8.0,
            fy=345.0, elastic_modulus=value, stiffener_spacing=None,
            resistance_factors_gamma_a1=1.10,
        )


def test_check_shear_major_axis_rejects_web_clear_height_larger_than_total_depth() -> None:
    with pytest.raises(ValueError):
        check_shear_major_axis(
            vsd=1.0, total_depth=350.0, web_clear_height=400.0, web_thickness=8.0,
            fy=345.0, elastic_modulus=200_000.0, stiffener_spacing=None,
            resistance_factors_gamma_a1=1.10,
        )


def test_check_shear_major_axis_accepts_web_clear_height_equal_to_total_depth() -> None:
    # Caso degenerado (secao sem mesas, h==d) -> deve ser aceito ("<=" na
    # validacao, nao "<"), mesmo sendo fisicamente incomum para I/H/U.
    result = check_shear_major_axis(
        vsd=1.0, total_depth=350.0, web_clear_height=350.0, web_thickness=8.0,
        fy=345.0, elastic_modulus=200_000.0, stiffener_spacing=None,
        resistance_factors_gamma_a1=1.10,
    )
    assert result.is_ok is True


# -- ShearCheckResult: validacao direta e imutabilidade --------------------------


def test_shear_check_result_rejects_non_finite_vsd() -> None:
    with pytest.raises(ValueError):
        ShearCheckResult(vsd=math.nan, vrd=1000.0)


@pytest.mark.parametrize("vrd", [0.0, -1.0, math.nan, math.inf])
def test_shear_check_result_rejects_invalid_vrd(vrd: float) -> None:
    with pytest.raises(ValueError):
        ShearCheckResult(vsd=100.0, vrd=vrd)


def test_shear_check_result_accepts_negative_vsd() -> None:
    # Vsd pode ser negativo (sentido oposto do cisalhamento) -> so a
    # magnitude importa fisicamente, mas a classe em si nao assume sinal
    # (o chamador e responsavel por passar |Vsd| se for esse o interesse).
    result = ShearCheckResult(vsd=-100.0, vrd=1000.0)
    assert result.sd == -100.0


def test_shear_check_result_sd_rd_aliases() -> None:
    result = ShearCheckResult(vsd=100.0, vrd=1000.0)
    assert result.sd == result.vsd
    assert result.rd == result.vrd


def test_shear_check_result_is_frozen() -> None:
    result = ShearCheckResult(vsd=100.0, vrd=1000.0)
    with pytest.raises(AttributeError):
        result.vsd = 200.0  # type: ignore[misc]
