"""VAL-0010 — Validacao normativa de check_shear_major_axis
(NBR 8800:2024, 5.4.1.3/5.4.3.1).

Fonte normativa: ABNT NBR 8800:2024, 5.4.3.1.1 "Em secoes I, H e U
fletidas em relacao ao eixo central de inercia perpendicular a alma
[...], a forca cortante resistente de calculo, VRd, e calculada
conforme a seguir" (pagina 57) e 5.4.3.1.2 "A forca cortante
correspondente a plastificacao da alma por cisalhamento e calculada
conforme a seguinte equacao: Vpl = 0,60 Aw fy [...] Aw = d.tw" (paginas
57-58) — ver docs/normative/NBR8800-RULES.md para a rastreabilidade
completa (RULE-IDs NBR8800-SHEAR-001 a 004).

Metodo: calculo manual independente (mesma tecnica de VAL-0006 a
VAL-0009), calculando os 3 ramos da curva de Vrd (plastico, inelastico,
elastico) a partir das formulas lidas diretamente do PDF.

Nota sobre a geometria usada: ao contrario de Ag/Iy/Iz/J (valores de
catalogo reais do perfil W310x21 usados em VAL-0001 a VAL-0009), as
dimensoes de alma (d, h, tw) usadas abaixo sao HIPOTETICAS -- nao sao
valores catalograficos certificados para nenhum perfil especifico
(mesma disciplina de VAL-0008 com Cw). O objetivo e confirmar que a
formula esta implementada corretamente, nao fornecer um valor de
projeto real para um perfil especifico.
"""

from __future__ import annotations

import math

from validation_record import ValidationRecord

from openstruct.normative.nbr8800.shear import (
    check_shear_major_axis,
    effective_shear_area_major_axis,
    plastic_shear_force,
    shear_buckling_coefficient,
    shear_resistance,
)

FY = 345.0
E = 200_000.0
GAMMA_A1 = 1.10
TOTAL_DEPTH = 400.0
WEB_CLEAR_HEIGHT = 350.0


def _manual_vrd(web_thickness: float, stiffener_spacing: float | None) -> tuple[float, str]:
    """Calculo manual independente de Vrd, retornando tambem o ramo esperado."""
    aw = TOTAL_DEPTH * web_thickness
    vpl = 0.60 * aw * FY
    if stiffener_spacing is None:
        kv = 5.34
    else:
        ratio = stiffener_spacing / WEB_CLEAR_HEIGHT
        kv = 5.34 if ratio > 3 else 5.0 + 5.0 / ratio**2
    lam = WEB_CLEAR_HEIGHT / web_thickness
    lam_p = 1.10 * math.sqrt(kv * E / FY)
    lam_r = 1.37 * math.sqrt(kv * E / FY)
    if lam <= lam_p:
        return vpl / GAMMA_A1, "plastico"
    if lam <= lam_r:
        return (lam_p / lam) * vpl / GAMMA_A1, "inelastico"
    return 1.24 * (lam_p / lam) ** 2 * vpl / GAMMA_A1, "elastico"


# ---------------------------------------------------------------------------
# Caso 1: alma espessa -> ramo plastico (escoamento por cisalhamento)
# ---------------------------------------------------------------------------


def test_val0010_thick_web_plastic_branch_matches_manual_calculation() -> None:
    web_thickness = 8.0
    vrd_ref, branch = _manual_vrd(web_thickness, stiffener_spacing=None)
    assert branch == "plastico"

    result = check_shear_major_axis(
        vsd=100_000.0,
        total_depth=TOTAL_DEPTH,
        web_clear_height=WEB_CLEAR_HEIGHT,
        web_thickness=web_thickness,
        fy=FY,
        elastic_modulus=E,
        stiffener_spacing=None,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Vrd, alma espessa (tw=8mm, sem enrijecedores) -- ramo plastico",
        referencia=vrd_ref,
        resultado=result.vrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 2: alma intermediaria -> ramo de flambagem inelastica
# ---------------------------------------------------------------------------


def test_val0010_intermediate_web_inelastic_branch_matches_manual_calculation() -> None:
    web_thickness = 5.0
    vrd_ref, branch = _manual_vrd(web_thickness, stiffener_spacing=None)
    assert branch == "inelastico"

    result = check_shear_major_axis(
        vsd=1.0,
        total_depth=TOTAL_DEPTH,
        web_clear_height=WEB_CLEAR_HEIGHT,
        web_thickness=web_thickness,
        fy=FY,
        elastic_modulus=E,
        stiffener_spacing=None,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Vrd, alma intermediaria (tw=5mm, sem enrijecedores) -- ramo inelastico",
        referencia=vrd_ref,
        resultado=result.vrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 3: alma fina -> ramo de flambagem elastica por cisalhamento
# ---------------------------------------------------------------------------


def test_val0010_thin_web_elastic_branch_matches_manual_calculation() -> None:
    web_thickness = 2.5
    vrd_ref, branch = _manual_vrd(web_thickness, stiffener_spacing=None)
    assert branch == "elastico"

    result = check_shear_major_axis(
        vsd=1.0,
        total_depth=TOTAL_DEPTH,
        web_clear_height=WEB_CLEAR_HEIGHT,
        web_thickness=web_thickness,
        fy=FY,
        elastic_modulus=E,
        stiffener_spacing=None,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    record = ValidationRecord(
        problema="Vrd, alma fina (tw=2,5mm, sem enrijecedores) -- ramo elastico",
        referencia=vrd_ref,
        resultado=result.vrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 4: efeito dos enrijecedores transversais (a/h pequeno -> kv maior)
# ---------------------------------------------------------------------------


def test_val0010_transverse_stiffeners_increase_vrd_matches_manual_calculation() -> None:
    """Com alma fina (tw=5mm, ramo inelastico sem enrijecedores),
    adicionar enrijecedores transversais proximos (a/h=1) aumenta kv de
    5,34 para 10,0, deslocando lambda_p/lambda_r para cima e elevando
    Vrd -- confirma numericamente que a implementacao de kv reflete o
    beneficio esperado dos enrijecedores."""
    web_thickness = 5.0
    stiffener_spacing = WEB_CLEAR_HEIGHT * 1.0  # a/h = 1

    vrd_ref, branch = _manual_vrd(web_thickness, stiffener_spacing=stiffener_spacing)
    vrd_no_stiffeners_ref, _ = _manual_vrd(web_thickness, stiffener_spacing=None)
    assert vrd_ref > vrd_no_stiffeners_ref  # confirma o efeito esperado no calculo de referencia

    result = check_shear_major_axis(
        vsd=1.0,
        total_depth=TOTAL_DEPTH,
        web_clear_height=WEB_CLEAR_HEIGHT,
        web_thickness=web_thickness,
        fy=FY,
        elastic_modulus=E,
        stiffener_spacing=stiffener_spacing,
        resistance_factors_gamma_a1=GAMMA_A1,
    )

    kv_ref = 5.0 + 5.0 / (stiffener_spacing / WEB_CLEAR_HEIGHT) ** 2
    record_kv = ValidationRecord(
        problema="kv com enrijecedores (a/h=1)", referencia=10.0, resultado=kv_ref
    )
    assert record_kv.status == "APROVADO", record_kv

    record = ValidationRecord(
        problema=f"Vrd com enrijecedores transversais (a/h=1, ramo {branch})",
        referencia=vrd_ref,
        resultado=result.vrd,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 5: componentes intermediarios (Aw, Vpl, kv) batem isoladamente
# ---------------------------------------------------------------------------


def test_val0010_intermediate_quantities_match_manual_calculation() -> None:
    web_thickness = 8.0
    aw = effective_shear_area_major_axis(TOTAL_DEPTH, web_thickness)
    vpl = plastic_shear_force(aw, FY)
    kv = shear_buckling_coefficient(WEB_CLEAR_HEIGHT, stiffener_spacing=None)

    records = [
        ValidationRecord(
            problema="Aw = d*tw", referencia=TOTAL_DEPTH * web_thickness, resultado=aw
        ),
        ValidationRecord(
            problema="Vpl = 0,60*Aw*fy", referencia=0.60 * aw * FY, resultado=vpl
        ),
        ValidationRecord(problema="kv (sem enrijecedores)", referencia=5.34, resultado=kv),
    ]
    for record in records:
        assert record.status == "APROVADO", record

    lam_p = 1.10 * math.sqrt(kv * E / FY)
    lam_r = 1.37 * math.sqrt(kv * E / FY)
    lam = WEB_CLEAR_HEIGHT / web_thickness
    vrd = shear_resistance(vpl, lam, lam_p, lam_r, GAMMA_A1)
    record_vrd = ValidationRecord(
        problema="Vrd via shear_resistance (chamada direta)",
        referencia=vpl / GAMMA_A1,  # este caso cai no ramo plastico
        resultado=vrd,
    )
    assert record_vrd.status == "APROVADO", record_vrd
