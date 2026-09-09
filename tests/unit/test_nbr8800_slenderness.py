"""Testes unitarios de openstruct.normative.nbr8800.slenderness.

Ver docs/normative/NBR8800-RULES.md, RULE-IDs NBR8800-TRAC-004 e
NBR8800-COMP-008.
"""

from __future__ import annotations

import math

import pytest

from openstruct.normative.nbr8800.slenderness import (
    COMPRESSION_SLENDERNESS_LIMIT,
    TENSION_SLENDERNESS_LIMIT,
    SlendernessCheckResult,
    check_compression_slenderness,
    check_tension_slenderness,
    slenderness_ratio,
)

# -- slenderness_ratio ---------------------------------------------------------


def test_slenderness_ratio_matches_formula() -> None:
    assert slenderness_ratio(4000.0, 40.0) == pytest.approx(100.0)


def test_slenderness_ratio_doubles_when_length_doubles() -> None:
    assert slenderness_ratio(8000.0, 40.0) == pytest.approx(2 * slenderness_ratio(4000.0, 40.0))


def test_slenderness_ratio_halves_when_radius_doubles() -> None:
    assert slenderness_ratio(4000.0, 80.0) == pytest.approx(slenderness_ratio(4000.0, 40.0) / 2)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_slenderness_ratio_rejects_invalid_length(value: float) -> None:
    with pytest.raises(ValueError):
        slenderness_ratio(value, 40.0)


@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_slenderness_ratio_rejects_invalid_radius_of_gyration(value: float) -> None:
    with pytest.raises(ValueError):
        slenderness_ratio(4000.0, value)


# -- limites (constantes) -------------------------------------------------------


def test_tension_slenderness_limit_is_300() -> None:
    assert TENSION_SLENDERNESS_LIMIT == 300.0


def test_compression_slenderness_limit_is_200() -> None:
    assert COMPRESSION_SLENDERNESS_LIMIT == 200.0


def test_tension_limit_is_larger_than_compression_limit() -> None:
    # NBR 8800:2024 permite barras tracionadas mais esbeltas que
    # comprimidas (a esbeltez em compressao afeta diretamente a
    # capacidade resistente via flambagem; em tracao, e so uma
    # recomendacao de comportamento em servico).
    assert TENSION_SLENDERNESS_LIMIT > COMPRESSION_SLENDERNESS_LIMIT


# -- check_tension_slenderness --------------------------------------------------


def test_check_tension_slenderness_uses_the_larger_ratio() -> None:
    # ry menor -> L/ry maior -> deve ser o valor usado (eixo mais esbelto governa).
    result = check_tension_slenderness(
        length_y=4000.0, radius_of_gyration_y=40.0, length_z=4000.0, radius_of_gyration_z=120.0
    )
    assert result.ratio == pytest.approx(100.0)  # 4000/40, nao 4000/120
    assert result.limit == TENSION_SLENDERNESS_LIMIT


def test_check_tension_slenderness_within_limit() -> None:
    result = check_tension_slenderness(4000.0, 40.0, 4000.0, 120.0)
    assert result.is_within_recommended_limit is True


def test_check_tension_slenderness_exceeds_limit() -> None:
    result = check_tension_slenderness(20000.0, 40.0, 20000.0, 120.0)
    assert result.ratio == pytest.approx(500.0)
    assert result.is_within_recommended_limit is False


def test_check_tension_slenderness_at_exact_limit_via_public_function() -> None:
    # length/radius_of_gyration escolhidos para dar ratio=300 exatamente
    # (12000/40), passando pelo caminho real de calculo (nao construindo
    # SlendernessCheckResult diretamente) — achado do CODE REVIEW AGENT.
    result = check_tension_slenderness(12000.0, 40.0, 1000.0, 120.0)
    assert result.ratio == pytest.approx(TENSION_SLENDERNESS_LIMIT)
    assert result.is_within_recommended_limit is True


# -- check_compression_slenderness -----------------------------------------------


def test_check_compression_slenderness_uses_the_larger_ratio() -> None:
    result = check_compression_slenderness(
        length_y=4000.0, radius_of_gyration_y=40.0, length_z=4000.0, radius_of_gyration_z=120.0
    )
    assert result.ratio == pytest.approx(100.0)
    assert result.limit == COMPRESSION_SLENDERNESS_LIMIT


def test_check_compression_slenderness_within_limit() -> None:
    result = check_compression_slenderness(4000.0, 40.0, 4000.0, 120.0)
    assert result.is_within_recommended_limit is True


def test_check_compression_slenderness_exceeds_limit() -> None:
    result = check_compression_slenderness(9000.0, 37.6, 9000.0, 117.5)
    assert result.is_within_recommended_limit is False


def test_check_compression_slenderness_at_exact_limit_via_public_function() -> None:
    # length/radius_of_gyration escolhidos para dar ratio=200 exatamente
    # (8000/40), passando pelo caminho real de calculo — mesmo raciocinio
    # do teste equivalente de tracao.
    result = check_compression_slenderness(8000.0, 40.0, 1000.0, 120.0)
    assert result.ratio == pytest.approx(COMPRESSION_SLENDERNESS_LIMIT)
    assert result.is_within_recommended_limit is True


def test_same_geometry_can_pass_tension_but_fail_compression() -> None:
    # ratio=239.3 esta entre os dois limites (200 < 239.3 < 300) ->
    # discrimina corretamente os dois limites diferentes da mesma barra.
    length, ry, rz = 9000.0, 37.60557278486277, 117.49880913972589
    tension = check_tension_slenderness(length, ry, length, rz)
    compression = check_compression_slenderness(length, ry, length, rz)
    assert tension.ratio == compression.ratio  # mesma geometria -> mesmo indice
    assert tension.is_within_recommended_limit is True
    assert compression.is_within_recommended_limit is False


# -- SlendernessCheckResult: validacao direta e imutabilidade -------------------


@pytest.mark.parametrize("ratio", [0.0, -1.0, math.nan, math.inf])
def test_slenderness_check_result_rejects_invalid_ratio(ratio: float) -> None:
    with pytest.raises(ValueError):
        SlendernessCheckResult(ratio=ratio, limit=300.0)


@pytest.mark.parametrize("limit", [0.0, -1.0, math.nan, math.inf])
def test_slenderness_check_result_rejects_invalid_limit(limit: float) -> None:
    with pytest.raises(ValueError):
        SlendernessCheckResult(ratio=100.0, limit=limit)


def test_slenderness_check_result_boundary_is_within_limit() -> None:
    # ratio == limit exatamente -> "<=" ainda dentro da recomendacao.
    result = SlendernessCheckResult(ratio=300.0, limit=300.0)
    assert result.is_within_recommended_limit is True


def test_slenderness_check_result_is_frozen() -> None:
    result = SlendernessCheckResult(ratio=100.0, limit=300.0)
    with pytest.raises(AttributeError):
        result.ratio = 200.0  # type: ignore[misc]
