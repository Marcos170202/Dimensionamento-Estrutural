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


# -- Cw (constante de empenamento) -------------------------------------------


def test_section_cw_defaults_to_none() -> None:
    sec = Section(**W310X21)
    assert sec.Cw is None


def test_section_accepts_explicit_cw_value() -> None:
    data = dict(W310X21)
    data["Cw"] = 1.2e9
    sec = Section(**data)
    assert sec.Cw == 1.2e9


def test_section_accepts_cw_equal_to_zero() -> None:
    # Cw=0 e fisicamente valido (secoes fechadas/tubulares, sem
    # empenamento) — nao deve ser confundido com "nao informado" (None).
    data = dict(W310X21)
    data["Cw"] = 0.0
    sec = Section(**data)
    assert sec.Cw == 0.0


@pytest.mark.parametrize("cw", [-1.0, -0.0001])
def test_section_rejects_negative_cw(cw: float) -> None:
    data = dict(W310X21)
    data["Cw"] = cw
    with pytest.raises(ValueError):
        Section(**data)


def test_section_rejects_nan_cw() -> None:
    data = dict(W310X21)
    data["Cw"] = math.nan
    with pytest.raises(ValueError):
        Section(**data)


# -- raio de giracao -----------------------------------------------------------


def test_section_radius_of_gyration_matches_formula() -> None:
    sec = Section(**W310X21)
    assert sec.radius_of_gyration_y == pytest.approx(math.sqrt(sec.Iy / sec.A))
    assert sec.radius_of_gyration_z == pytest.approx(math.sqrt(sec.Iz / sec.A))


def test_section_radius_of_gyration_z_larger_than_y_for_w_shape() -> None:
    # Perfil W (I/H): Iz (eixo forte) > Iy (eixo fraco) -> rz > ry.
    sec = Section(**W310X21)
    assert sec.radius_of_gyration_z > sec.radius_of_gyration_y


def test_section_radius_of_gyration_doubling_area_at_fixed_inertia_halves_it_squared() -> None:
    # r = sqrt(I/A) -> dobrar A (a I fixo) divide r^2 por 2.
    data = dict(W310X21)
    sec1 = Section(**data)
    data2 = dict(W310X21)
    data2["A"] = data["A"] * 2
    data2["name"] = "W310x21-2xA"
    sec2 = Section(**data2)
    assert sec2.radius_of_gyration_y**2 == pytest.approx(sec1.radius_of_gyration_y**2 / 2)


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
