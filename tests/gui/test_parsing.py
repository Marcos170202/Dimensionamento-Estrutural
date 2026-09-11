"""Testes de ``openstruct.gui._parsing``."""

from __future__ import annotations

import pytest

from openstruct.gui._parsing import parse_decimal


def test_parse_decimal_accepts_dot() -> None:
    assert parse_decimal("1.5") == 1.5


def test_parse_decimal_accepts_comma() -> None:
    assert parse_decimal("1,5") == 1.5


def test_parse_decimal_accepts_scientific_notation() -> None:
    assert parse_decimal("7.85e-9") == 7.85e-9


def test_parse_decimal_invalid_raises_value_error() -> None:
    with pytest.raises(ValueError, match="could not convert"):
        parse_decimal("abc")
