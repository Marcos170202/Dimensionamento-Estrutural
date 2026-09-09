"""VAL-0009 — Validacao normativa de check_tension_slenderness/check_compression_slenderness
(NBR 8800:2024, 5.2.8.1/5.3.7.1).

Fonte normativa: ABNT NBR 8800:2024, 5.2.8.1 "Recomenda-se que o
indice de esbeltez das barras tracionadas [...] nao supere 300" e
5.3.7.1 "Recomenda-se que o indice de esbeltez das barras comprimidas
[...] nao supere 200" — ver docs/normative/NBR8800-RULES.md para a
rastreabilidade completa (RULE-IDs NBR8800-TRAC-004, NBR8800-COMP-008).

Metodo: calculo manual independente (mesma tecnica de VAL-0006 a
VAL-0008), usando a geometria real (nao hipotetica) do perfil W310x21
ja usado em VAL-0001 a VAL-0008 — ao contrario de VAL-0008 (que usou
um Cw hipotetico), aqui Iy/Iz/A sao os mesmos valores catalograficos
reais, e o raio de giracao e uma propriedade DERIVADA deles
(``sqrt(I/A)``), entao nenhum dado adicional precisa ser hipotetico.
"""

from __future__ import annotations

import math

from validation_record import ValidationRecord

from openstruct.domain.section import Section
from openstruct.normative.nbr8800.slenderness import (
    COMPRESSION_SLENDERNESS_LIMIT,
    TENSION_SLENDERNESS_LIMIT,
    check_compression_slenderness,
    check_tension_slenderness,
    slenderness_ratio,
)

SECTION = Section(
    name="W310x21", A=2680.0, Iy=3.79e6, Iz=37.0e6, J=52.8e3,
    Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3,
)


# ---------------------------------------------------------------------------
# Caso 1: indice de esbeltez bate com o calculo manual (raio de giracao real)
# ---------------------------------------------------------------------------


def test_val0009_slenderness_ratio_matches_manual_calculation() -> None:
    length = 4000.0
    ratio_y = slenderness_ratio(length, SECTION.radius_of_gyration_y)
    ratio_z = slenderness_ratio(length, SECTION.radius_of_gyration_z)

    ratio_y_ref = length / math.sqrt(SECTION.Iy / SECTION.A)
    ratio_z_ref = length / math.sqrt(SECTION.Iz / SECTION.A)

    records = [
        ValidationRecord(
            problema="Indice de esbeltez L/ry (eixo fraco)",
            referencia=ratio_y_ref,
            resultado=ratio_y,
        ),
        ValidationRecord(
            problema="Indice de esbeltez L/rz (eixo forte)",
            referencia=ratio_z_ref,
            resultado=ratio_z,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record

    # Confirma que o eixo fraco (menor r) governa (maior L/r).
    assert ratio_y > ratio_z


# ---------------------------------------------------------------------------
# Caso 2: coluna de 4m (esbeltez usual) fica dentro de AMBOS os limites
# ---------------------------------------------------------------------------


def test_val0009_typical_column_length_within_both_limits() -> None:
    length = 4000.0
    tension = check_tension_slenderness(
        length, SECTION.radius_of_gyration_y, length, SECTION.radius_of_gyration_z
    )
    compression = check_compression_slenderness(
        length, SECTION.radius_of_gyration_y, length, SECTION.radius_of_gyration_z
    )

    ratio_ref = length / math.sqrt(SECTION.Iy / SECTION.A)  # eixo fraco governa
    records = [
        ValidationRecord(
            problema="Indice de esbeltez governante (L=4000mm, eixo fraco)",
            referencia=ratio_ref,
            resultado=tension.ratio,
        ),
        ValidationRecord(
            problema="Indice de esbeltez governante (compressao, mesmo valor)",
            referencia=ratio_ref,
            resultado=compression.ratio,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record

    assert tension.is_within_recommended_limit is True
    assert compression.is_within_recommended_limit is True


# ---------------------------------------------------------------------------
# Caso 3: comprimento intermediario (9m) discrimina os dois limites diferentes
# ---------------------------------------------------------------------------


def test_val0009_intermediate_length_discriminates_the_two_limits() -> None:
    """Com L=9000mm, L/ry ~= 239 — entre 200 (limite de compressao) e
    300 (limite de tracao). A mesma barra fisica passaria na
    recomendacao de tracao mas nao na de compressao, demonstrando que
    os dois limites sao aplicados corretamente e de forma
    independente."""
    length = 9000.0
    tension = check_tension_slenderness(
        length, SECTION.radius_of_gyration_y, length, SECTION.radius_of_gyration_z
    )
    compression = check_compression_slenderness(
        length, SECTION.radius_of_gyration_y, length, SECTION.radius_of_gyration_z
    )

    ratio_ref = length / math.sqrt(SECTION.Iy / SECTION.A)
    record = ValidationRecord(
        problema="Indice de esbeltez (L=9000mm, eixo fraco)",
        referencia=ratio_ref,
        resultado=tension.ratio,
    )
    assert record.status == "APROVADO", record

    assert COMPRESSION_SLENDERNESS_LIMIT < tension.ratio < TENSION_SLENDERNESS_LIMIT
    assert tension.is_within_recommended_limit is True
    assert compression.is_within_recommended_limit is False
