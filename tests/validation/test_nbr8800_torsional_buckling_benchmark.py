"""VAL-0008 — Validacao normativa de torsional_buckling_force (NBR 8800:2024, 5.3.5.1-c).

Fonte normativa: ABNT NBR 8800:2024, 5.3.5.1, caso c) "para flambagem
por torcao em relacao ao eixo longitudinal z": ``Nez = (1/r0^2)*
[pi^2*E*Cw/Lz^2 + G*J]``, com ``r0 = sqrt(rx^2+ry^2+x0^2+y0^2)``
(``x0=y0=0`` para secoes com dupla simetria ou simetricas em relacao a
um ponto) — ver docs/normative/NBR8800-RULES.md para a rastreabilidade
completa (RULE-IDs NBR8800-COMP-005/006/007).

Metodo: mesma tecnica de VAL-0006/VAL-0007 — calculo manual
independente de cada termo da formula lida diretamente do PDF
fornecido pelo usuario.

**Nota sobre os valores de Cw usados abaixo**: ao contrario de Ag/Iy/
Iz/J (valores de catalogo reais do perfil W310x21, ja usados em
VAL-0001 a VAL-0007), a constante de empenamento Cw usada aqui e
HIPOTETICA — nao e um valor catalografico certificado deste projeto
para o W310x21 (evitar citar um valor de memoria sem fonte, mesma
disciplina de docs/normative/NBR8800-RULES.md). O objetivo desta
validacao e confirmar que a formula de Nez esta implementada
CORRETAMENTE, nao fornecer um valor de projeto real para este perfil
especifico.
"""

from __future__ import annotations

import math

from validation_record import ValidationRecord

from openstruct.domain.material import Material
from openstruct.domain.section import Section
from openstruct.normative.nbr8800.compression import (
    check_compression_member,
    flexural_buckling_force,
    polar_radius_of_gyration,
    torsional_buckling_force,
)
from openstruct.normative.nbr8800.resistance_factors import (
    LoadCombinationClass,
    steel_resistance_factors,
)

STEEL = Material(
    name="ASTM A572 Gr. 50", E=200_000.0, G=77_000.0, density=7.85e-6,
    fy=345.0, fu=450.0, poisson=0.3,
)
# Mesma geometria de VAL-0001 a VAL-0007 (W310x21), com Cw HIPOTETICO
# (ver nota do modulo) so para exercitar a formula de Nez.
SECTION = Section(
    name="W310x21 (Cw hipotetico)", A=2680.0, Iy=3.79e6, Iz=37.0e6, J=52.8e3,
    Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3, Cw=1.2e9,
)
LENGTH = 4000.0


# ---------------------------------------------------------------------------
# Caso 1: r0 e Nez batem com o calculo manual
# ---------------------------------------------------------------------------


def test_val0008_r0_and_nez_match_manual_calculation() -> None:
    r0 = polar_radius_of_gyration(SECTION.radius_of_gyration_y, SECTION.radius_of_gyration_z)
    nez = torsional_buckling_force(
        STEEL.E, STEEL.G, SECTION.Cw, SECTION.J, r0, LENGTH
    )

    r0_ref = math.sqrt(SECTION.radius_of_gyration_y**2 + SECTION.radius_of_gyration_z**2)
    nez_ref = (1.0 / r0_ref**2) * (
        math.pi**2 * STEEL.E * SECTION.Cw / LENGTH**2 + STEEL.G * SECTION.J
    )

    records = [
        ValidationRecord(
            problema="r0 = sqrt(ry^2+rz^2) (dupla simetria, x0=y0=0)",
            referencia=r0_ref,
            resultado=r0,
        ),
        ValidationRecord(
            problema="Nez = (1/r0^2)*(pi^2*E*Cw/Lz^2 + G*J)",
            referencia=nez_ref,
            resultado=nez,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record


# ---------------------------------------------------------------------------
# Caso 2: cenario em que a torcao GOVERNA — demonstra por que omitir Nez
# seria nao conservador (a limitacao de seguranca que este incremento fecha)
# ---------------------------------------------------------------------------


def test_val0008_torsion_governs_and_changes_nc_rd_materially() -> None:
    """Com o Cw hipotetico usado aqui, Nez < Nex e Nez < Ney — a
    torcao governa a flambagem, e Nc,Rd calculado incluindo Nez e
    MENOR (mais conservador/correto) que o calculado so com flexao."""
    factors = steel_resistance_factors(LoadCombinationClass.NORMAL)

    nex = flexural_buckling_force(STEEL.E, SECTION.Iz, LENGTH)
    ney = flexural_buckling_force(STEEL.E, SECTION.Iy, LENGTH)
    r0 = polar_radius_of_gyration(SECTION.radius_of_gyration_y, SECTION.radius_of_gyration_z)
    nez = torsional_buckling_force(STEEL.E, STEEL.G, SECTION.Cw, SECTION.J, r0, LENGTH)

    assert nez < ney < nex  # torcao e o modo mais critico neste caso

    ne_completo = min(nex, ney, nez)
    ne_so_flexao = min(nex, ney)

    result_completo = check_compression_member(
        nc_sd=100_000.0, gross_area=SECTION.A, effective_area=SECTION.A, fy=STEEL.fy,
        elastic_buckling_force=ne_completo, resistance_factors=factors,
    )
    result_so_flexao = check_compression_member(
        nc_sd=100_000.0, gross_area=SECTION.A, effective_area=SECTION.A, fy=STEEL.fy,
        elastic_buckling_force=ne_so_flexao, resistance_factors=factors,
    )

    chi_completo_ref = 0.658 ** (
        math.sqrt(SECTION.A * STEEL.fy / ne_completo) ** 2
    ) if math.sqrt(SECTION.A * STEEL.fy / ne_completo) <= 1.5 else 0.877 / (
        math.sqrt(SECTION.A * STEEL.fy / ne_completo) ** 2
    )
    nc_rd_completo_ref = chi_completo_ref * SECTION.A * STEEL.fy / factors.gamma_a1
    record = ValidationRecord(
        problema="Nc,Rd incluindo Nez (torcao governando)",
        referencia=nc_rd_completo_ref,
        resultado=result_completo.nc_rd,
    )
    assert record.status == "APROVADO", record

    # A demonstracao de seguranca: ignorar Nez (usar so flexao) superestima
    # Nc,Rd de forma NAO CONSERVADORA para esta secao/comprimento.
    assert result_completo.nc_rd < result_so_flexao.nc_rd
    reducao_percentual = 100 * (1 - result_completo.nc_rd / result_so_flexao.nc_rd)
    assert reducao_percentual > 30.0  # reducao substancial, nao um efeito marginal


# ---------------------------------------------------------------------------
# Caso 3: Cw=0 (secao fechada/tubular) reduz Nez ao termo de Saint-Venant puro
# ---------------------------------------------------------------------------


def test_val0008_zero_warping_constant_reduces_to_saint_venant_term() -> None:
    r0 = polar_radius_of_gyration(SECTION.radius_of_gyration_y, SECTION.radius_of_gyration_z)
    nez_sem_empenamento = torsional_buckling_force(STEEL.E, STEEL.G, 0.0, SECTION.J, r0, LENGTH)

    nez_ref = STEEL.G * SECTION.J / r0**2
    record = ValidationRecord(
        problema="Nez com Cw=0 (secao fechada) = G*J/r0^2 (termo de Saint-Venant puro)",
        referencia=nez_ref,
        resultado=nez_sem_empenamento,
    )
    assert record.status == "APROVADO", record
