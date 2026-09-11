"""VAL-0012 — Validacao normativa de check_flexural_resistance_major_axis
(NBR 8800:2024, 5.4.1.3/5.4.2/Anexo D, D.2.8-e/f/h e Tabela D.1).

Fonte normativa: ABNT NBR 8800:2024, Anexo D, Tabela D.1 (primeira
linha, colunas FLM e FLA) e D.2.8-e/f/h, paginas 143-146 — ver
docs/normative/NBR8800-RULES.md para a rastreabilidade completa
(RULE-IDs NBR8800-FLEX-005 a 008).

Metodo: calculo manual independente (mesma tecnica de VAL-0006 a
VAL-0011), calculando os 3 ramos das curvas de Mrd para FLM (perfis
laminados e soldados) e FLA, e confirmando que
check_flexural_resistance_major_axis retorna o MENOR entre
FLT/FLM/FLA (e o limite de 5.4.2.2), fechando a limitacao de
seguranca registrada em NBR8800-FLEX-004 para este tipo de secao/eixo.

Nota sobre a geometria usada: mesma secao hipotetica de VAL-0011
(Iy=20e6mm^4, J=500e3mm^4, d=400mm, tf=16mm, W=900e3mm^3, Z=1000e3mm^3,
ry=60mm), com dimensoes de mesa/alma adicionais tambem hipoteticas
(mesma disciplina de VAL-0008/VAL-0010/VAL-0011) — o objetivo e
confirmar as formulas, nao fornecer um valor de projeto real.
"""

from __future__ import annotations

import math

from validation_record import ValidationRecord

from openstruct.normative.nbr8800.flexure import (
    check_flexural_resistance_major_axis,
    flange_local_buckling_coefficient_welded,
    flange_local_buckling_moment_rolled,
    flange_local_buckling_moment_welded,
    lateral_torsional_buckling_moment,
    lateral_torsional_buckling_slenderness_limit,
)

FY = 345.0
E = 200_000.0
GAMMA_A1 = 1.10
IY = 20.0e6
J = 500.0e3
TOTAL_DEPTH = 400.0
FLANGE_THICKNESS_BASE = 16.0
CW = IY * (TOTAL_DEPTH - FLANGE_THICKNESS_BASE) ** 2 / 4.0
ELASTIC_SECTION_MODULUS = 900.0e3
PLASTIC_SECTION_MODULUS = 1_000.0e3
RY = 60.0
CB = 1.0
UNBRACED_LENGTH = 1500.0


def _flt_mrd(unbraced_length: float) -> float:
    mr = 0.70 * FY * ELASTIC_SECTION_MODULUS
    mpl = FY * PLASTIC_SECTION_MODULUS
    lam_p = 1.76 * math.sqrt(E / FY)
    lam_r = lateral_torsional_buckling_slenderness_limit(CB, E, IY, J, CW, RY, mr)
    lam = unbraced_length / RY
    if lam <= lam_p:
        return mpl / GAMMA_A1
    mcr = lateral_torsional_buckling_moment(CB, E, IY, J, CW, unbraced_length)
    if lam <= lam_r:
        ratio = (lam - lam_p) / (lam_r - lam_p)
        return (mpl - (mpl - mr) * ratio) / GAMMA_A1
    return mcr / GAMMA_A1


def _flm_mrd_rolled(flange_width: float, flange_thickness: float) -> tuple[float, str]:
    mr = 0.70 * FY * ELASTIC_SECTION_MODULUS
    mpl = FY * PLASTIC_SECTION_MODULUS
    lam = (flange_width / 2.0) / flange_thickness
    lam_p = 0.38 * math.sqrt(E / FY)
    lam_r = 0.83 * math.sqrt(E / (0.70 * FY))
    if lam <= lam_p:
        return mpl / GAMMA_A1, "plastico"
    mcr = flange_local_buckling_moment_rolled(E, ELASTIC_SECTION_MODULUS, lam)
    if lam <= lam_r:
        ratio = (lam - lam_p) / (lam_r - lam_p)
        return (mpl - (mpl - mr) * ratio) / GAMMA_A1, "inelastico"
    return mcr / GAMMA_A1, "elastico"


def _flm_mrd_welded(
    flange_width: float, flange_thickness: float, web_clear_height: float, web_thickness: float
) -> tuple[float, str]:
    mr = 0.70 * FY * ELASTIC_SECTION_MODULUS
    mpl = FY * PLASTIC_SECTION_MODULUS
    lam = (flange_width / 2.0) / flange_thickness
    kc = flange_local_buckling_coefficient_welded(web_clear_height, web_thickness)
    lam_p = 0.38 * math.sqrt(E / FY)
    lam_r = 0.95 * math.sqrt(E * kc / (0.70 * FY))
    if lam <= lam_p:
        return mpl / GAMMA_A1, "plastico"
    mcr = flange_local_buckling_moment_welded(E, kc, ELASTIC_SECTION_MODULUS, lam)
    if lam <= lam_r:
        ratio = (lam - lam_p) / (lam_r - lam_p)
        return (mpl - (mpl - mr) * ratio) / GAMMA_A1, "inelastico"
    return mcr / GAMMA_A1, "elastico"


def _fla_mrd(web_clear_height: float, web_thickness: float) -> tuple[float, str]:
    mr = FY * ELASTIC_SECTION_MODULUS  # Mr=fy*W para FLA (diferente de FLT/FLM)
    mpl = FY * PLASTIC_SECTION_MODULUS
    lam = web_clear_height / web_thickness
    lam_p = 3.76 * math.sqrt(E / FY)
    lam_r = 5.70 * math.sqrt(E / FY)
    if lam <= lam_p:
        return mpl / GAMMA_A1, "plastico"
    if lam <= lam_r:
        ratio = (lam - lam_p) / (lam_r - lam_p)
        return (mpl - (mpl - mr) * ratio) / GAMMA_A1, "inelastico"
    raise AssertionError("cenario de alma esbelta -- fora do escopo do Anexo D (Anexo E)")


# ---------------------------------------------------------------------------
# Caso 1: mesa e alma espessas -> FLT governa (bate com FLT isolado)
# ---------------------------------------------------------------------------


def test_val0012_thick_flange_and_web_flt_governs() -> None:
    flange_width, flange_thickness = 200.0, 16.0
    web_clear_height, web_thickness = 350.0, 8.0

    flt_ref = _flt_mrd(UNBRACED_LENGTH)
    flm_ref, flm_branch = _flm_mrd_rolled(flange_width, flange_thickness)
    fla_ref, fla_branch = _fla_mrd(web_clear_height, web_thickness)
    assert flm_branch == "plastico"
    assert fla_branch == "plastico"
    mrd_ref = min(flt_ref, flm_ref, fla_ref)

    result = check_flexural_resistance_major_axis(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=UNBRACED_LENGTH,
        cb=CB,
        flange_width=flange_width,
        flange_thickness=flange_thickness,
        web_clear_height=web_clear_height,
        web_thickness=web_thickness,
        rolled=True,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd, mesa/alma espessas -- FLT governa (min(FLT,FLM,FLA))",
        referencia=mrd_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 2: mesa fina (laminado) -> FLM governa, ramo elastico
# ---------------------------------------------------------------------------


def test_val0012_thin_flange_rolled_flm_governs_elastic_branch() -> None:
    flange_width, flange_thickness = 300.0, 5.0
    web_clear_height, web_thickness = 350.0, 8.0

    flm_ref, flm_branch = _flm_mrd_rolled(flange_width, flange_thickness)
    assert flm_branch == "elastico"
    flt_ref = _flt_mrd(UNBRACED_LENGTH)
    fla_ref, _ = _fla_mrd(web_clear_height, web_thickness)
    assert flm_ref < flt_ref and flm_ref < fla_ref  # confirma que FLM de fato governa

    result = check_flexural_resistance_major_axis(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=UNBRACED_LENGTH,
        cb=CB,
        flange_width=flange_width,
        flange_thickness=flange_thickness,
        web_clear_height=web_clear_height,
        web_thickness=web_thickness,
        rolled=True,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd, mesa fina laminada (FLM governa, ramo elastico)",
        referencia=flm_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 3: mesa fina (soldado) -> FLM com kc, ramo elastico
# ---------------------------------------------------------------------------


def test_val0012_thin_flange_welded_flm_uses_kc_elastic_branch() -> None:
    flange_width, flange_thickness = 300.0, 5.0
    web_clear_height, web_thickness = 350.0, 8.0

    flm_ref, flm_branch = _flm_mrd_welded(
        flange_width, flange_thickness, web_clear_height, web_thickness
    )
    assert flm_branch == "elastico"
    flm_rolled_ref, _ = _flm_mrd_rolled(flange_width, flange_thickness)
    assert flm_ref < flm_rolled_ref  # soldado (kc<0,767) e mais conservador que laminado

    result = check_flexural_resistance_major_axis(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=UNBRACED_LENGTH,
        cb=CB,
        flange_width=flange_width,
        flange_thickness=flange_thickness,
        web_clear_height=web_clear_height,
        web_thickness=web_thickness,
        rolled=False,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd, mesa fina soldada (FLM com kc, ramo elastico)",
        referencia=flm_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 4: alma fina (mas nao esbelta) -> FLA governa, ramo inelastico
# ---------------------------------------------------------------------------


def test_val0012_thin_web_fla_governs_inelastic_branch() -> None:
    flange_width, flange_thickness = 200.0, 16.0
    web_clear_height, web_thickness = 350.0, 3.0

    fla_ref, fla_branch = _fla_mrd(web_clear_height, web_thickness)
    assert fla_branch == "inelastico"
    flt_ref = _flt_mrd(UNBRACED_LENGTH)
    flm_ref, _ = _flm_mrd_rolled(flange_width, flange_thickness)
    assert fla_ref < flt_ref and fla_ref < flm_ref  # confirma que FLA de fato governa

    result = check_flexural_resistance_major_axis(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=PLASTIC_SECTION_MODULUS,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=UNBRACED_LENGTH,
        cb=CB,
        flange_width=flange_width,
        flange_thickness=flange_thickness,
        web_clear_height=web_clear_height,
        web_thickness=web_thickness,
        rolled=True,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd, alma fina nao esbelta (FLA governa, ramo inelastico)",
        referencia=fla_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 5: limite de 5.4.2.2 (Mrd <= 1,50*W*fy/gamma_a1)
# ---------------------------------------------------------------------------


def test_val0012_5422_cap_matches_manual_calculation() -> None:
    # Modulo plastico artificialmente alto (fator de forma extremo) ->
    # mesmo no ramo plastico de FLT/FLM/FLA, o limite de 5.4.2.2 deve
    # reduzir Mrd para 1,50*W*fy/gamma_a1.
    huge_plastic_modulus = 10_000.0e3
    cap_ref = 1.50 * ELASTIC_SECTION_MODULUS * FY / GAMMA_A1

    result = check_flexural_resistance_major_axis(
        msd=1.0,
        fy=FY,
        elastic_modulus=E,
        elastic_section_modulus=ELASTIC_SECTION_MODULUS,
        plastic_section_modulus=huge_plastic_modulus,
        minor_axis_moment_of_inertia=IY,
        torsion_constant=J,
        warping_constant=CW,
        radius_of_gyration_minor_axis=RY,
        unbraced_length=UNBRACED_LENGTH,
        cb=CB,
        flange_width=200.0,
        flange_thickness=16.0,
        web_clear_height=350.0,
        web_thickness=8.0,
        rolled=True,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Mrd limitado por 5.4.2.2 (1,50*W*fy/gamma_a1)",
        referencia=cap_ref,
        resultado=result.mrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 6: precondicao D.1.2 (viga de alma esbelta -> ValueError, Anexo E)
# ---------------------------------------------------------------------------


def test_val0012_slender_web_precondition_matches_manual_calculation() -> None:
    web_clear_height, web_thickness = 1000.0, 2.0
    lam_fla_ref = web_clear_height / web_thickness
    lam_r_fla_ref = 5.70 * math.sqrt(E / FY)

    record = ValidationRecord(
        problema="lambda_r_FLA = 5,70*sqrt(E/fy) (limite de aplicabilidade do Anexo D, D.1.2)",
        referencia=5.70 * math.sqrt(E / FY),
        resultado=lam_r_fla_ref,
    )
    assert record.status == "APROVADO", record
    assert lam_fla_ref > lam_r_fla_ref  # confirma que este cenario e de fato alma esbelta

    raised = False
    try:
        check_flexural_resistance_major_axis(
            msd=1.0,
            fy=FY,
            elastic_modulus=E,
            elastic_section_modulus=ELASTIC_SECTION_MODULUS,
            plastic_section_modulus=PLASTIC_SECTION_MODULUS,
            minor_axis_moment_of_inertia=IY,
            torsion_constant=J,
            warping_constant=CW,
            radius_of_gyration_minor_axis=RY,
            unbraced_length=UNBRACED_LENGTH,
            cb=CB,
            flange_width=200.0,
            flange_thickness=16.0,
            web_clear_height=web_clear_height,
            web_thickness=web_thickness,
            rolled=True,
            resistance_factors_gamma_a1=GAMMA_A1,
        )
    except ValueError:
        raised = True
    assert raised, "esperava ValueError para viga de alma esbelta (fora do escopo do Anexo D)"
