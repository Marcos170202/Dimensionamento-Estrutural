"""VAL-0006 — Validacao normativa de check_tension_member (NBR 8800:2024, 5.2).

Fonte normativa: ABNT NBR 8800:2024, 5.2.1.2/5.2.2 (forca axial
resistente de calculo de barras tracionadas) e 4.9.2, Tabela 3
(coeficientes de ponderacao da resistencia do aco estrutural) — ver
docs/normative/NBR8800-RULES.md para a rastreabilidade completa
(RULE-IDs NBR8800-RES-001, NBR8800-TRAC-001/002/003).

Metodo: como as formulas de 5.2.2 sao aritmetica direta (nao ha
integracao/iteracao como nos casos de FEM), a validacao aqui e por
CALCULO MANUAL INDEPENDENTE de cada termo (mesma tecnica de
"referencia calculada a mao" usada em VAL-0001 a VAL-0005) — nao um
"exemplo de livro-texto" da NBR especificamente, para nao arriscar
citar um valor de memoria. O que se valida e que o codigo reproduz
EXATAMENTE a aritmetica da formula lida diretamente do PDF fornecido
pelo usuario.
"""

from __future__ import annotations

from validation_record import ValidationRecord

from openstruct.normative.nbr8800.resistance_factors import (
    LoadCombinationClass,
    steel_resistance_factors,
)
from openstruct.normative.nbr8800.tension import (
    check_tension_member,
    net_area_without_holes,
)

# ---------------------------------------------------------------------------
# Caso 1: barra sem furos, escoamento governa (combinacao normal)
# ---------------------------------------------------------------------------


def test_val0006_no_holes_yield_governs_matches_manual_calculation() -> None:
    """Perfil W310x21 (Ag=2680mm^2, ASTM A572 Gr.50: fy=345MPa,
    fu=450MPa), sem furos (An=Ag, 5.2.4.2) e ligacao direta
    (hipoteticamente Ct=1 — nao implementado nesta fase, usado aqui so
    para fechar o numero de Ae; ver docs/normative/NBR8800-RULES.md
    para o porque de Ct nao estar implementado ainda)."""
    ag = 2680.0
    fy = 345.0
    fu = 450.0
    factors = steel_resistance_factors(LoadCombinationClass.NORMAL)
    an = net_area_without_holes(ag)
    ae = an  # Ct=1 (ligacao direta hipotetica, ver docstring acima)

    result = check_tension_member(
        nt_sd=500_000.0,
        gross_area=ag,
        effective_net_area=ae,
        fy=fy,
        fu=fu,
        resistance_factors=factors,
    )

    nt_rd_yield_ref = ag * fy / 1.10
    nt_rd_rupture_ref = ae * fu / 1.35
    nt_rd_ref = min(nt_rd_yield_ref, nt_rd_rupture_ref)

    records = [
        ValidationRecord(
            problema="Nt,Rd escoamento da secao bruta (Ag*fy/gamma_a1)",
            referencia=nt_rd_yield_ref,
            resultado=result.nt_rd_yield,
        ),
        ValidationRecord(
            problema="Nt,Rd ruptura da secao liquida (Ae*fu/gamma_a2)",
            referencia=nt_rd_rupture_ref,
            resultado=result.nt_rd_rupture,
        ),
        ValidationRecord(
            problema="Nt,Rd governante (o menor dos dois)",
            referencia=nt_rd_ref,
            resultado=result.nt_rd,
        ),
        ValidationRecord(
            problema="Taxa de utilizacao (Nt,Sd/Nt,Rd)",
            referencia=500_000.0 / nt_rd_ref,
            resultado=result.utilization,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record

    # Para este perfil/material, o escoamento da secao bruta governa
    # (Ag*fy/1.10 = 840545.45 N < Ae*fu/1.35 = 893333.3 N).
    assert result.governing == "escoamento_secao_bruta"
    assert result.is_ok is True


# ---------------------------------------------------------------------------
# Caso 2: area liquida efetiva reduzida o suficiente para a ruptura governar
# ---------------------------------------------------------------------------


def test_val0006_reduced_net_area_rupture_governs_matches_manual_calculation() -> None:
    """Mesmo perfil/material do Caso 1, mas com Ae bem menor que Ag
    (simulando perda de secao por ligacao) — a ruptura da secao
    liquida passa a governar."""
    ag = 2680.0
    ae = 900.0  # bem menor que Ag, forcando a ruptura a governar
    fy = 345.0
    fu = 450.0
    factors = steel_resistance_factors(LoadCombinationClass.NORMAL)

    result = check_tension_member(
        nt_sd=250_000.0,
        gross_area=ag,
        effective_net_area=ae,
        fy=fy,
        fu=fu,
        resistance_factors=factors,
    )

    nt_rd_yield_ref = ag * fy / 1.10
    nt_rd_rupture_ref = ae * fu / 1.35

    records = [
        ValidationRecord(
            problema="Nt,Rd ruptura da secao liquida (Ae*fu/gamma_a2), Ae reduzida",
            referencia=nt_rd_rupture_ref,
            resultado=result.nt_rd_rupture,
        ),
        ValidationRecord(
            problema="Nt,Rd governante (ruptura, pois Ae e pequena)",
            referencia=min(nt_rd_yield_ref, nt_rd_rupture_ref),
            resultado=result.nt_rd,
        ),
    ]
    for record in records:
        assert record.status == "APROVADO", record

    assert result.governing == "ruptura_secao_liquida"
    assert result.nt_rd_rupture < result.nt_rd_yield


# ---------------------------------------------------------------------------
# Caso 3: combinacao excepcional usa os coeficientes reduzidos da Tabela 3
# ---------------------------------------------------------------------------


def test_val0006_excepcional_combination_uses_reduced_factors() -> None:
    """Mesma barra do Caso 1, mas classificada como combinacao
    excepcional (gamma_a1=1.00, gamma_a2=1.15 em vez de 1.10/1.35) —
    confirma que a Tabela 3 e consultada corretamente por classe de
    combinacao, nao um valor fixo."""
    ag = 2680.0
    ae = ag
    fy = 345.0
    fu = 450.0
    factors_normal = steel_resistance_factors(LoadCombinationClass.NORMAL)
    factors_excepcional = steel_resistance_factors(LoadCombinationClass.EXCEPCIONAL)

    result_normal = check_tension_member(
        nt_sd=500_000.0, gross_area=ag, effective_net_area=ae, fy=fy, fu=fu,
        resistance_factors=factors_normal,
    )
    result_excepcional = check_tension_member(
        nt_sd=500_000.0, gross_area=ag, effective_net_area=ae, fy=fy, fu=fu,
        resistance_factors=factors_excepcional,
    )

    record = ValidationRecord(
        problema="Nt,Rd (escoamento) combinacao excepcional (Ag*fy/1.00)",
        referencia=ag * fy / 1.00,
        resultado=result_excepcional.nt_rd_yield,
    )
    assert record.status == "APROVADO", record

    # Coeficientes menores (combinacao excepcional) -> resistencia de
    # calculo MAIOR para o mesmo material/secao (menos conservador,
    # coerente com a menor probabilidade de ocorrencia simultanea).
    assert result_excepcional.nt_rd > result_normal.nt_rd
