"""Testes unitarios de openstruct.domain.material."""

import dataclasses
import math

import pytest

from openstruct.domain.material import Material

STEEL_A572_GR50 = dict(
    name="ASTM A572 Gr. 50",
    E=200000.0,
    G=77000.0,
    density=7.85e-6,
    fy=345.0,
    fu=450.0,
    poisson=0.3,
)


def test_material_valid_construction_stores_fields() -> None:
    mat = Material(**STEEL_A572_GR50)
    assert mat.name == "ASTM A572 Gr. 50"
    assert mat.E == 200000.0
    assert mat.fy == 345.0


def test_material_is_frozen() -> None:
    mat = Material(**STEEL_A572_GR50)
    with pytest.raises(dataclasses.FrozenInstanceError):
        mat.E = 210000.0  # type: ignore[misc]


def test_material_rejects_blank_name() -> None:
    data = dict(STEEL_A572_GR50)
    data["name"] = "   "
    with pytest.raises(ValueError):
        Material(**data)


@pytest.mark.parametrize("field", ["E", "G", "density", "fy", "fu"])
def test_material_rejects_non_positive_values(field: str) -> None:
    data = dict(STEEL_A572_GR50)
    data[field] = 0.0
    with pytest.raises(ValueError):
        Material(**data)

    data[field] = -1.0
    with pytest.raises(ValueError):
        Material(**data)


@pytest.mark.parametrize("field", ["E", "G", "density", "fy", "fu"])
def test_material_rejects_nan_values(field: str) -> None:
    # regressao: "valor <= 0" nao rejeita NaN (nan<=0 e False), entao a
    # validacao precisa usar "not (valor > 0)" — ver CODE REVIEW AGENT.
    data = dict(STEEL_A572_GR50)
    data[field] = math.nan
    with pytest.raises(ValueError):
        Material(**data)


def test_material_rejects_fu_less_than_fy() -> None:
    data = dict(STEEL_A572_GR50)
    data["fy"] = 500.0
    data["fu"] = 400.0
    with pytest.raises(ValueError):
        Material(**data)


def test_material_accepts_fu_equal_to_fy() -> None:
    data = dict(STEEL_A572_GR50)
    data["fy"] = 400.0
    data["fu"] = 400.0
    mat = Material(**data)  # nao deve levantar
    assert mat.fu == mat.fy


@pytest.mark.parametrize("bad_poisson", [-0.1, 0.5, 0.6])
def test_material_rejects_poisson_out_of_range(bad_poisson: float) -> None:
    data = dict(STEEL_A572_GR50)
    data["poisson"] = bad_poisson
    with pytest.raises(ValueError):
        Material(**data)


def test_material_accepts_poisson_zero() -> None:
    data = dict(STEEL_A572_GR50)
    data["poisson"] = 0.0
    mat = Material(**data)
    assert mat.poisson == 0.0


def test_material_isotropic_shear_modulus_formula() -> None:
    mat = Material(**STEEL_A572_GR50)
    expected = mat.E / (2.0 * (1.0 + mat.poisson))
    assert mat.isotropic_shear_modulus == pytest.approx(expected)


def test_material_is_isotropic_consistent_for_typical_steel() -> None:
    # E=200000, G=77000, nu=0.3 -> G_teorico = 200000/2.6 ~= 76923.
    # Erro relativo ~0.1%, bem dentro da tolerancia padrao (3%).
    mat = Material(**STEEL_A572_GR50)
    assert mat.is_isotropic_consistent()


def test_material_is_isotropic_consistent_flags_bad_data() -> None:
    data = dict(STEEL_A572_GR50)
    data["G"] = 200000.0  # G igual a E: fisicamente absurdo para um solido isotropico
    mat = Material(**data)
    assert not mat.is_isotropic_consistent()


def test_material_equality_by_value() -> None:
    a = Material(**STEEL_A572_GR50)
    b = Material(**STEEL_A572_GR50)
    assert a == b
    assert hash(a) == hash(b)
