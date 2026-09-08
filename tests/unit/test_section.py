"""Testes unitarios de openstruct.domain.section."""

import dataclasses
import math

import pytest

from openstruct.domain.section import Section

# Perfil W310x21 (valores tipicos de tabela, mm/mm2/mm3/mm4).
W310X21 = dict(
    name="W310x21",
    A=2680.0,
    Iy=3.79e6,
    Iz=37.0e6,
    J=52.8e3,
    Wply=306e3,
    Wplz=254e3,
    Wely=272e3,
    Welz=239e3,
)


def test_section_valid_construction_stores_fields() -> None:
    sec = Section(**W310X21)
    assert sec.name == "W310x21"
    assert sec.A == 2680.0


def test_section_is_frozen() -> None:
    sec = Section(**W310X21)
    with pytest.raises(dataclasses.FrozenInstanceError):
        sec.A = 1.0  # type: ignore[misc]


def test_section_rejects_blank_name() -> None:
    data = dict(W310X21)
    data["name"] = ""
    with pytest.raises(ValueError):
        Section(**data)


@pytest.mark.parametrize(
    "field", ["A", "Iy", "Iz", "J", "Wply", "Wplz", "Wely", "Welz"]
)
def test_section_rejects_non_positive_geometric_properties(field: str) -> None:
    data = dict(W310X21)
    data[field] = 0.0
    with pytest.raises(ValueError):
        Section(**data)

    data[field] = -1.0
    with pytest.raises(ValueError):
        Section(**data)


@pytest.mark.parametrize(
    "field", ["A", "Iy", "Iz", "J", "Wply", "Wplz", "Wely", "Welz"]
)
def test_section_rejects_nan_geometric_properties(field: str) -> None:
    # regressao: "valor <= 0" nao rejeita NaN (nan<=0 e False), entao a
    # validacao precisa usar "not (valor > 0)" — ver CODE REVIEW AGENT.
    data = dict(W310X21)
    data[field] = math.nan
    with pytest.raises(ValueError):
        Section(**data)


def test_section_rejects_plastic_modulus_smaller_than_elastic_y() -> None:
    data = dict(W310X21)
    data["Wply"] = 100e3
    data["Wely"] = 200e3
    with pytest.raises(ValueError):
        Section(**data)


def test_section_rejects_plastic_modulus_smaller_than_elastic_z() -> None:
    data = dict(W310X21)
    data["Wplz"] = 100e3
    data["Welz"] = 200e3
    with pytest.raises(ValueError):
        Section(**data)


def test_section_accepts_plastic_equal_elastic_modulus() -> None:
    data = dict(W310X21)
    data["Wply"] = data["Wely"]
    data["Wplz"] = data["Welz"]
    sec = Section(**data)  # nao deve levantar
    assert sec.shape_factor_y == pytest.approx(1.0)


def test_section_shape_factors() -> None:
    sec = Section(**W310X21)
    assert sec.shape_factor_y == pytest.approx(sec.Wply / sec.Wely)
    assert sec.shape_factor_z == pytest.approx(sec.Wplz / sec.Welz)
    assert sec.shape_factor_y > 1.0
    assert sec.shape_factor_z > 1.0


def test_section_dimensions_default_is_empty_and_immutable() -> None:
    sec = Section(**W310X21)
    assert dict(sec.dimensions) == {}
    with pytest.raises(TypeError):
        sec.dimensions["h"] = 310.0  # type: ignore[index]


def test_section_dimensions_are_stored_and_immutable() -> None:
    data = dict(W310X21)
    data["dimensions"] = {"h": 303.0, "bf": 101.0, "tw": 5.0, "tf": 5.7}
    sec = Section(**data)
    assert sec.dimensions["h"] == 303.0
    with pytest.raises(TypeError):
        sec.dimensions["h"] = 999.0  # type: ignore[index]


def test_section_equality_ignores_nothing_but_hash_ignores_dimensions() -> None:
    data_a = dict(W310X21)
    data_a["dimensions"] = {"h": 303.0}
    data_b = dict(W310X21)
    data_b["dimensions"] = {"h": 999.0}  # dimensions diferentes
    a = Section(**data_a)
    b = Section(**data_b)
    assert a != b  # __eq__ ainda compara dimensions
    # dimensions e excluida do hash (MappingProxyType nao e hasheavel);
    # o hash deve ser calculavel sem lancar excecao.
    assert isinstance(hash(a), int)
    assert isinstance(hash(b), int)
