"""VAL-0011 — Validacao normativa de check_lateral_torsional_buckling
(NBR 8800:2024, 5.4.1.3/5.4.2/Anexo D, D.2.8-a).

Fonte normativa: ABNT NBR 8800:2024, Anexo D, Tabela D.1 (primeira
linha, coluna FLT: secoes I, H com dois eixos de simetria e secoes U
nao sujeitas a momento de torcao, fletidas em relacao ao eixo de maior
momento de inercia) e D.2.8-a (formulas de `Mcr`/`lambda_r`), paginas
144-146 — ver docs/normative/NBR8800-RULES.md para a rastreabilidade
completa (RULE-IDs NBR8800-FLEX-001 a 004).

Metodo: calculo manual independente (mesma tecnica de VAL-0006 a
VAL-0010), calculando os 3 ramos da curva de Mrd (plastico,
inelastico, elastico) a partir das formulas lidas diretamente do PDF.

Nota sobre a geometria usada: ao contrario de Ag/Iy/Iz/J (valores de
catalogo reais do perfil W310x21 usados em VAL-0001 a VAL-0009), as
propriedades de secao (Iy, J, Cw, W, Z, ry) usadas abaixo sao
HIPOTETICAS -- nao sao valores catalograficos certificados para
nenhum perfil especifico (mesma disciplina de VAL-0008 com Cw e
VAL-0010 com as dimensoes de alma). O objetivo e confirmar que a
formula esta implementada corretamente, nao fornecer um valor de
projeto real para um perfil especifico.
"""

from __future__ import annotations

import math

from validation_record import ValidationRecord

from openstruct.normative.nbr8800.flexure import (
    check_lateral_torsional_buckling,
    lateral_torsional_buckling_moment,
    lateral_torsional_buckling_slenderness_limit,
    moment_gradient_factor_doubly_symmetric,
    warping_constant_i_section,
)

FY = 345.0
E = 200_000.0
GAMMA_A1 = 1.10
IY = 20.0e6
J = 500.0e3
TOTAL_DEPTH = 400.0
FLANGE_THICKNESS = 16.0
CW = IY * (TOTAL_DEPTH - FLANGE_THICKNESS) ** 2 / 4.0
ELASTIC_SECTION_MODULUS = 900.0e3
PLASTIC_SECTION_MODULUS = 1_000.0e3
RY = 60.0
CB = 1.0


def _manual_mrd(unbraced_length: float) -> tuple[float, str]:
    """Calculo manual independente de Mrd, retornando tambem o ramo esperado."""
    mr = 0.70 * FY * ELASTIC_SECTION_MODULUS
    mpl = FY * PLASTIC_SECTION_MODULUS
    beta1 = mr / (E * J)
    lam_p = 1.76 * math.sqrt(E / FY)
    lam_r = (1.38 * CB * math.sqrt(IY * J) / (RY * J * beta1)) * math.sqrt(
        1.0 + math.sqrt(1.0 + 27.0 * CW * beta1**2 / (CB**2 * IY))
    )
    lam = unbraced_length / RY
    if lam <= lam_p:
        return mpl / GAMMA_A1, "plastico"
    mcr = (CB * math.pi**2 * E * IY / unbraced_length**2) * math.sqrt(
        (CW / IY) * (1.0 + 0.039 * J * unbraced_length**2 / CW)
    )
    if lam <= lam_r:
        ratio = (lam - lam_p) / (lam_r - lam_p)
        return (mpl - (mpl - mr) * ratio) / GAMMA_A1, "inelastico"
    return mcr / GAMMA_A1, "elastico"


# ---------------------------------------------------------------------------
# Caso 1: comprimento destravado curto -> ramo plastico
# ---------------------------------------------------------------------------


def test_val0011_short_unbraced_length_plastic_branch_matches_manual_calculation() -> None:
    lb = 1500.0
    mrd_ref, branch = _manual_mrd(lb)
    assert branch == "plastico"

    result = check_lateral_torsional_buckling(
        msd=1.0e6,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=lb,
        cb=CB,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd, Lb=1500mm (curto) -- ramo plastico",
        referencia=mrd_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 2: comprimento destravado intermediario -> ramo inelastico
# ---------------------------------------------------------------------------


def test_val0011_intermediate_unbraced_length_inelastic_branch_matches_manual_calculation() -> None:
    lb = 4000.0
    mrd_ref, branch = _manual_mrd(lb)
    assert branch == "inelastico"

    result = check_lateral_torsional_buckling(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=lb,
        cb=CB,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd, Lb=4000mm (intermediario) -- ramo inelastico",
        referencia=mrd_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 3: comprimento destravado longo -> ramo elastico (flambagem)
# ---------------------------------------------------------------------------


def test_val0011_long_unbraced_length_elastic_branch_matches_manual_calculation() -> None:
    lb = 12_000.0
    mrd_ref, branch = _manual_mrd(lb)
    assert branch == "elastico"

    result = check_lateral_torsional_buckling(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=lb,
        cb=CB,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd, Lb=12000mm (longo) -- ramo elastico",
        referencia=mrd_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 4: efeito do fator Cb (momento nao uniforme aumenta Mrd no trecho elastico)
# ---------------------------------------------------------------------------


def test_val0011_higher_cb_increases_mrd_matches_manual_calculation() -> None:
    """Com Lb=12000mm (ramo elastico, onde Mcr depende diretamente de
    Cb), um diagrama de momento nao uniforme (Cb=1,75, tipico de uma
    barra em balanco com carga na ponta) deve aumentar Mrd em relacao
    ao caso de momento uniforme (Cb=1,0) -- confirma numericamente que
    a implementacao de Cb reflete o beneficio esperado."""
    lb = 12_000.0
    cb_high = 1.75

    def _manual_mrd_with_cb(cb: float) -> float:
        mr = 0.70 * FY * ELASTIC_SECTION_MODULUS
        mpl = FY * PLASTIC_SECTION_MODULUS
        beta1 = mr / (E * J)
        lam_p = 1.76 * math.sqrt(E / FY)
        lam_r = (1.38 * cb * math.sqrt(IY * J) / (RY * J * beta1)) * math.sqrt(
            1.0 + math.sqrt(1.0 + 27.0 * CW * beta1**2 / (cb**2 * IY))
        )
        lam = lb / RY
        mcr = (cb * math.pi**2 * E * IY / lb**2) * math.sqrt(
            (CW / IY) * (1.0 + 0.039 * J * lb**2 / CW)
        )
        if lam <= lam_p:
            return mpl / GAMMA_A1
        if lam <= lam_r:
            ratio = (lam - lam_p) / (lam_r - lam_p)
            return (mpl - (mpl - mr) * ratio) / GAMMA_A1
        return mcr / GAMMA_A1

    mrd_low_ref = _manual_mrd_with_cb(CB)
    mrd_high_ref = _manual_mrd_with_cb(cb_high)
    assert mrd_high_ref > mrd_low_ref  # confirma o efeito esperado no calculo de referencia

    low = check_lateral_torsional_buckling(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=lb,
        cb=CB,
        resistance_factors_gamma_a1=GAMMA_A1,
    )
    high = check_lateral_torsional_buckling(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=lb,
        cb=cb_high,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record_low = ValidationRecord(
        problema="Mrd com Cb=1,0 (momento uniforme, ramo elastico)",
        referencia=mrd_low_ref,
        resultado=low.mrd,
    )
    record_high = ValidationRecord(
        problema="Mrd com Cb=1,75 (momento nao uniforme, ramo elastico)",
        referencia=mrd_high_ref,
        resultado=high.mrd,
    )
    assert record_low.status == "APROVADO", record_low
    assert record_high.status == "APROVADO", record_high


# ---------------------------------------------------------------------------
# Caso 5: componentes intermediarios (Cw, Cb geral, Mcr, lambda_r) batem isoladamente
# ---------------------------------------------------------------------------


def test_val0011_intermediate_quantities_match_manual_calculation() -> None:
    cw = warping_constant_i_section(IY, TOTAL_DEPTH, FLANGE_THICKNESS)
    cb = moment_gradient_factor_doubly_symmetric(100.0, 50.0, 75.0, 90.0)
    mr = 0.70 * FY * ELASTIC_SECTION_MODULUS
    lb = 4000.0
    mcr = lateral_torsional_buckling_moment(CB, E, IY, J, CW, lb)
    lam_r = lateral_torsional_buckling_slenderness_limit(CB, E, IY, J, CW, RY, mr)

    records = [
        ValidationRecord(
            problema="Cw = Iy*(d-tf)^2/4",
            referencia=IY * (TOTAL_DEPTH - FLANGE_THICKNESS) ** 2 / 4.0,
            resultado=cw,
        ),
        ValidationRecord(
            problema="Cb (formula geral, 5.4.2.3-a)",
            referencia=12.5 * 100.0 / (2.5 * 100.0 + 3 * 50.0 + 4 * 75.0 + 3 * 90.0),
            resultado=cb,
        ),
        ValidationRecord(
            problema="Mcr (D.2.8-a, Lb=4000mm)",
            referencia=(CB * math.pi**2 * E * IY / lb**2)
            * math.sqrt((CW / IY) * (1.0 + 0.039 * J * lb**2 / CW)),
            resultado=mcr,
        ),
        ValidationRecord(
            problema="lambda_r (D.2.8-a)",
            referencia=(1.38 * CB * math.sqrt(IY * J) / (RY * J * (mr / (E * J))))
            * math.sqrt(1.0 + math.sqrt(1.0 + 27.0 * CW * (mr / (E * J)) ** 2 / (CB**2 * IY))),
            resultado=lam_r,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record
