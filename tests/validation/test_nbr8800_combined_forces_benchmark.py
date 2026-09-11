"""VAL-0013 — Validacao normativa de check_axial_and_bending_interaction
(NBR 8800:2024, 5.5.1.2).

Fonte normativa: ABNT NBR 8800:2024, 5.5.1.2, pagina 60: "Para a
atuacao simultanea da forca axial de tracao ou de compressao e de
momentos fletores, deve ser atendida a limitacao fornecida pelas
seguintes equacoes de interacao" (equacoes a e b, conforme Nsd/Nrd
maior/igual ou menor que 0,2) — ver docs/normative/NBR8800-RULES.md
para a rastreabilidade completa (RULE-IDs NBR8800-COMB-001/002).

Metodo: calculo manual independente (mesma tecnica de VAL-0006 a
VAL-0012), calculando as duas equacoes de interacao a partir das
formulas lidas diretamente do PDF.

Nota sobre os valores usados: Nsd/Nrd/Mx,sd/Mx,rd/My,sd/My,rd abaixo
sao HIPOTETICOS -- nao sao valores catalograficos certificados para
nenhum perfil especifico (mesma disciplina de VAL-0008/VAL-0010 a
VAL-0012). O objetivo e confirmar que as duas equacoes de interacao
estao implementadas corretamente, nao fornecer um valor de projeto
real.
"""

from __future__ import annotations

from validation_record import ValidationRecord

from openstruct.normative.nbr8800.combined_forces import check_axial_and_bending_interaction


def _manual_ratio(
    n_sd: float, n_rd: float, mx_sd: float, mx_rd: float, my_sd: float, my_rd: float
) -> tuple[float, str]:
    """Calculo manual independente da razao de interacao, retornando tambem a equacao usada."""
    ratio_n = n_sd / n_rd
    bending_term = mx_sd / mx_rd + my_sd / my_rd
    if ratio_n >= 0.2:
        return ratio_n + (8.0 / 9.0) * bending_term, "a"
    return ratio_n / 2.0 + bending_term, "b"


# ---------------------------------------------------------------------------
# Caso 1: Nsd/Nrd >= 0,2 -> equacao a) -- barra dentro do limite
# ---------------------------------------------------------------------------


def test_val0013_high_axial_ratio_equation_a_within_limit() -> None:
    n_sd, n_rd = 300_000.0, 800_000.0  # ratio = 0,375
    mx_sd, mx_rd = 80.0e6, 300.0e6
    my_sd, my_rd = 15.0e6, 80.0e6

    ratio_ref, equation = _manual_ratio(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)
    assert equation == "a"

    result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)

    record = ValidationRecord(
        problema="Interacao N+M biaxial, Nsd/Nrd=0,375 (>=0,2) -- equacao a)",
        referencia=ratio_ref,
        resultado=result.interaction_ratio,
    )
    assert record.status == "APROVADO", record
    assert result.is_ok is True


# ---------------------------------------------------------------------------
# Caso 2: Nsd/Nrd < 0,2 -> equacao b) -- barra dentro do limite
# ---------------------------------------------------------------------------


def test_val0013_low_axial_ratio_equation_b_within_limit() -> None:
    n_sd, n_rd = 80_000.0, 800_000.0  # ratio = 0,10
    mx_sd, mx_rd = 100.0e6, 300.0e6
    my_sd, my_rd = 20.0e6, 80.0e6

    ratio_ref, equation = _manual_ratio(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)
    assert equation == "b"

    result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)

    record = ValidationRecord(
        problema="Interacao N+M biaxial, Nsd/Nrd=0,10 (<0,2) -- equacao b)",
        referencia=ratio_ref,
        resultado=result.interaction_ratio,
    )
    assert record.status == "APROVADO", record
    assert result.is_ok is True


# ---------------------------------------------------------------------------
# Caso 3: barra sobrecarregada (interaction_ratio > 1,0) -- reprovada
# ---------------------------------------------------------------------------


def test_val0013_overloaded_bar_fails_interaction() -> None:
    n_sd, n_rd = 700_000.0, 800_000.0  # ratio = 0,875 -> equacao a)
    mx_sd, mx_rd = 250.0e6, 300.0e6
    my_sd, my_rd = 60.0e6, 80.0e6

    ratio_ref, equation = _manual_ratio(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)
    assert equation == "a"
    assert ratio_ref > 1.0  # confirma que este cenario de fato reprova

    result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)

    record = ValidationRecord(
        problema="Interacao N+M biaxial, barra sobrecarregada (ratio>1,0)",
        referencia=ratio_ref,
        resultado=result.interaction_ratio,
    )
    assert record.status == "APROVADO", record
    assert result.is_ok is False


# ---------------------------------------------------------------------------
# Caso 4: continuidade exata no limite Nsd/Nrd=0,2 (fronteira das equacoes)
# ---------------------------------------------------------------------------


def test_val0013_exact_boundary_between_equations_matches_equation_a() -> None:
    n_rd = 800_000.0
    n_sd = 0.2 * n_rd  # exatamente no limite -> ">=" usa equacao a)
    mx_sd, mx_rd = 100.0e6, 300.0e6
    my_sd, my_rd = 20.0e6, 80.0e6

    ratio_ref, equation = _manual_ratio(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)
    assert equation == "a"

    result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)

    record = ValidationRecord(
        problema="Interacao N+M biaxial, Nsd/Nrd=0,2 exatamente -- fronteira usa equacao a)",
        referencia=ratio_ref,
        resultado=result.interaction_ratio,
    )
    assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 5: momento uniaxial (My,sd=0) -- confirma que o termo desaparece
# ---------------------------------------------------------------------------


def test_val0013_uniaxial_bending_matches_manual_calculation() -> None:
    n_sd, n_rd = 300_000.0, 800_000.0
    mx_sd, mx_rd = 80.0e6, 300.0e6

    ratio_ref, equation = _manual_ratio(n_sd, n_rd, mx_sd, mx_rd, 0.0, 80.0e6)
    assert equation == "a"

    result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, 0.0, 80.0e6)

    record = ValidationRecord(
        problema="Interacao N+M uniaxial (My,sd=0)",
        referencia=ratio_ref,
        resultado=result.interaction_ratio,
    )
    assert record.status == "APROVADO", record
