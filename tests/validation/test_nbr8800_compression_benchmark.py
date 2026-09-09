"""VAL-0007 — Validacao normativa de check_compression_member (NBR 8800:2024, 5.3).

Fonte normativa: ABNT NBR 8800:2024, 5.3.1/5.3.2 (forca axial de
compressao resistente de calculo), 5.3.3 (fator de reducao chi),
5.3.4.1 (area efetiva sem flambagem local) e 5.3.5.1-a)/b) (forca
axial de flambagem por flexao) — ver docs/normative/NBR8800-RULES.md
para a rastreabilidade completa (RULE-IDs NBR8800-COMP-001 a 005).

Metodo: mesma tecnica de VAL-0006 — calculo manual independente de
cada termo das formulas lidas diretamente do PDF fornecido pelo
usuario (nao um "exemplo de livro-texto" da norma).

**Lembrete de escopo** (ver ATENCAO em compression.py): os valores de
``Ne`` usados abaixo consideram apenas flambagem por flexao (Nex/Ney)
— nao ha flambagem por torcao/flexo-torcao nesta fase. Isso e
adequado para os perfis de mesa larga (I/H com dupla simetria) usados
nestes casos, e nao deve ser generalizado para secoes abertas de
parede fina sem essa verificacao adicional.
"""

from __future__ import annotations

import math

from validation_record import ValidationRecord

from openstruct.normative.nbr8800.compression import (
    check_compression_member,
    effective_area_without_local_buckling,
    flexural_buckling_force,
    reduction_factor,
)
from openstruct.normative.nbr8800.resistance_factors import (
    LoadCombinationClass,
    steel_resistance_factors,
)

# Mesmo perfil/material de VAL-0001 a VAL-0006.
AG = 2680.0
IY = 3.79e6
IZ = 37.0e6
FY = 345.0
E = 200_000.0


def _nc_rd_reference(ag: float, aef: float, fy: float, ne: float, gamma_a1: float) -> float:
    """Referencia calculada a mao, independente do codigo em teste."""
    lambda_0 = math.sqrt(ag * fy / ne)
    chi = 0.658 ** (lambda_0**2) if lambda_0 <= 1.5 else 0.877 / lambda_0**2
    return chi * aef * fy / gamma_a1


# ---------------------------------------------------------------------------
# Caso 1: coluna "curta" (esbeltez pequena, ramo lambda_0<=1.5, chi proximo de 1)
# ---------------------------------------------------------------------------


def test_val0007_short_column_matches_manual_calculation() -> None:
    length = 1500.0  # curta -> Ne grande -> lambda_0 pequeno
    factors = steel_resistance_factors(LoadCombinationClass.NORMAL)
    aef = effective_area_without_local_buckling(AG)

    nex = flexural_buckling_force(E, IZ, length)
    ney = flexural_buckling_force(E, IY, length)
    ne = min(nex, ney)

    result = check_compression_member(
        nc_sd=200_000.0, gross_area=AG, effective_area=aef, fy=FY,
        elastic_buckling_force=ne, resistance_factors=factors,
    )

    lambda_0_ref = math.sqrt(AG * FY / ne)
    nc_rd_ref = _nc_rd_reference(AG, aef, FY, ne, 1.10)

    records = [
        ValidationRecord(
            problema="Coluna curta — lambda_0 = sqrt(Ag*fy/Ne)",
            referencia=lambda_0_ref,
            resultado=result.lambda_0,
        ),
        ValidationRecord(
            problema="Coluna curta — Nc,Rd = chi*Aef*fy/gamma_a1",
            referencia=nc_rd_ref,
            resultado=result.nc_rd,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record

    assert result.lambda_0 <= 1.5  # confirma que o ramo <=1.5 e o exercitado
    assert result.chi > 0.85  # coluna curta -> a maior parte da resistencia de escoamento
    assert result.is_ok is True


# ---------------------------------------------------------------------------
# Caso 2: coluna "esbelta" (ramo lambda_0>1.5, chi pequeno)
# ---------------------------------------------------------------------------


def test_val0007_slender_column_matches_manual_calculation() -> None:
    length = 8000.0  # longa -> Ne pequeno -> lambda_0 grande
    factors = steel_resistance_factors(LoadCombinationClass.NORMAL)
    aef = effective_area_without_local_buckling(AG)

    ne = min(flexural_buckling_force(E, IZ, length), flexural_buckling_force(E, IY, length))

    result = check_compression_member(
        nc_sd=50_000.0, gross_area=AG, effective_area=aef, fy=FY,
        elastic_buckling_force=ne, resistance_factors=factors,
    )

    lambda_0_ref = math.sqrt(AG * FY / ne)
    nc_rd_ref = _nc_rd_reference(AG, aef, FY, ne, 1.10)

    records = [
        ValidationRecord(
            problema="Coluna esbelta — lambda_0 = sqrt(Ag*fy/Ne)",
            referencia=lambda_0_ref,
            resultado=result.lambda_0,
        ),
        ValidationRecord(
            problema="Coluna esbelta — Nc,Rd = chi*Aef*fy/gamma_a1 (ramo lambda_0>1,5)",
            referencia=nc_rd_ref,
            resultado=result.nc_rd,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record

    assert result.lambda_0 > 1.5  # confirma que o ramo >1.5 e o exercitado
    assert result.chi < 0.5  # coluna esbelta -> flambagem domina, resistencia reduzida


# ---------------------------------------------------------------------------
# Caso 3: chi no limite exato lambda_0=1,5 — confirma a descontinuidade conhecida
# ---------------------------------------------------------------------------


def test_val0007_chi_at_lambda_0_equals_1_5_matches_first_branch_exactly() -> None:
    chi = reduction_factor(1.5)
    chi_branch1_ref = 0.658 ** (1.5**2)
    chi_branch2_ref = 0.877 / 1.5**2

    record = ValidationRecord(
        problema=(
            "chi(lambda_0=1,5) usa o PRIMEIRO ramo (0,658^lambda_0^2), "
            'por definicao normativa ("<=")'
        ),
        referencia=chi_branch1_ref,
        resultado=chi,
    )
    assert record.status == "APROVADO", record

    # A norma define os dois ramos com formulas empiricas independentes
    # que NAO coincidem exatamente em lambda_0=1,5 — documentado tambem
    # no docstring de reduction_factor. Confirma que a diferenca e
    # pequena (~1,7e-4) mas real, nao um erro de arredondamento maior.
    diff = abs(chi_branch1_ref - chi_branch2_ref)
    assert 1e-5 < diff < 1e-3


# ---------------------------------------------------------------------------
# Caso 4: invariante fundamental — Nc,Rd nunca excede a capacidade de
# escoamento puro (Ag*fy/gamma_a1), qualquer que seja a esbeltez
# ---------------------------------------------------------------------------


def test_val0007_nc_rd_never_exceeds_pure_yield_capacity() -> None:
    """chi <= 1 sempre (5.3.3.1) e Aef <= Ag sempre (5.3.4) -> Nc,Rd =
    chi*Aef*fy/gamma_a1 <= Ag*fy/gamma_a1 para qualquer combinacao de
    comprimento/secao. Esta e a mesma logica fisica que torna a
    compressao sempre mais (ou igualmente) restritiva que o escoamento
    puro por tracao da mesma secao — verificado para varios
    comprimentos, do muito curto ao muito longo."""
    factors = steel_resistance_factors(LoadCombinationClass.NORMAL)
    aef = effective_area_without_local_buckling(AG)
    yield_capacity_ref = AG * FY / factors.gamma_a1

    for length in [500.0, 1500.0, 4000.0, 8000.0, 20000.0]:
        ne = min(flexural_buckling_force(E, IZ, length), flexural_buckling_force(E, IY, length))
        result = check_compression_member(
            nc_sd=1.0, gross_area=AG, effective_area=aef, fy=FY,
            elastic_buckling_force=ne, resistance_factors=factors,
        )
        assert result.nc_rd <= yield_capacity_ref + 1e-6, (length, result.nc_rd)

    record = ValidationRecord(
        problema="Capacidade de escoamento puro (Ag*fy/gamma_a1), usada como teto",
        referencia=AG * FY / 1.10,
        resultado=yield_capacity_ref,
    )
    assert record.status == "APROVADO", record
