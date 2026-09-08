"""Testes unitarios de openstruct.results.analysis_result.

Cobre a orquestracao (``run_analysis``) e a estrutura de
``AnalysisResult``. A CORRECAO numerica do resultado (comparacao
contra formulas fechadas) esta em
``tests/validation/test_solver_v1_benchmark.py`` (VAL-0002) — aqui o
foco e o comportamento da API: quais nos aparecem em cada dicionario,
propagacao de erros, etc.
"""

from __future__ import annotations

import numpy as np
import pytest

from openstruct.analysis.boundary_conditions import ModelInstabilityError
from openstruct.domain.elements.frame3d import Element3D
from openstruct.domain.loads import LoadCase, NodalLoad
from openstruct.domain.material import Material
from openstruct.domain.model import AnalysisModel
from openstruct.domain.node import Node
from openstruct.domain.section import Section
from openstruct.domain.support import Support
from openstruct.results.analysis_result import (
    AnalysisResult,
    EquilibriumResidualError,
    run_analysis,
)

STEEL = Material(
    name="Steel", E=200000.0, G=77000.0, density=7.85e-6, fy=345.0, fu=450.0, poisson=0.3
)
SECTION = Section(
    name="Sec1", A=2680.0, Iy=3.79e6, Iz=37.0e6, J=52.8e3,
    Wply=306e3, Wplz=254e3, Wely=272e3, Welz=239e3,
)


def _cantilever() -> AnalysisModel:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    model.add_support(Support.fixed(1))
    return model


def test_run_analysis_returns_analysis_result() -> None:
    model = _cantilever()
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    result = run_analysis(model, load)
    assert isinstance(result, AnalysisResult)


def test_displacements_present_for_every_node() -> None:
    model = _cantilever()
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    result = run_analysis(model, load)
    assert set(result.displacements) == {1, 2}
    assert result.displacements[1].shape == (6,)
    assert result.displacements[2].shape == (6,)


def test_fixed_node_has_zero_displacement() -> None:
    model = _cantilever()
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    result = run_analysis(model, load)
    assert np.allclose(result.displacements[1], np.zeros(6))


def test_reactions_present_only_for_supported_nodes() -> None:
    model = _cantilever()
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    result = run_analysis(model, load)
    assert set(result.reactions) == {1}  # so o no 1 tem Support
    assert result.reactions[1].shape == (6,)


def test_element_forces_present_for_every_element() -> None:
    model = _cantilever()
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    result = run_analysis(model, load)
    assert set(result.element_forces) == {1}
    assert result.element_forces[1].shape == (12,)


def test_global_equilibrium_reaction_balances_applied_load() -> None:
    model = _cantilever()
    applied_fy = -10000.0
    load = LoadCase("P", (NodalLoad(2, fy=applied_fy),))
    result = run_analysis(model, load)
    # Equilibrio global: soma das reacoes + soma das cargas aplicadas = 0.
    assert result.reactions[1][1] == pytest.approx(-applied_fy, rel=1e-8)


def test_free_dof_equilibrium_residual_is_numerically_zero() -> None:
    model = _cantilever()
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0, fz=3000.0, mx=2.0e5),))
    result = run_analysis(model, load)
    assert result.free_dof_equilibrium_residual < 1e-6


def test_run_analysis_propagates_model_instability_error() -> None:
    model = AnalysisModel()
    n1 = Node(1, 0.0, 0.0, 0.0)
    n2 = Node(2, 4000.0, 0.0, 0.0)
    model.add_node(n1)
    model.add_node(n2)
    model.add_element(Element3D(1, (n1, n2), STEEL, SECTION))
    # sem nenhum Support -> mecanismo
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    with pytest.raises(ModelInstabilityError):
        run_analysis(model, load)


def test_run_analysis_raises_equilibrium_residual_error_on_broken_solve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simula um solver "quebrado" (devolve um vetor incorreto) via monkeypatch.

    ``Element3D`` sempre produz matriz simetrica (VAL-0001), entao
    esse caminho nao deveria disparar em uso normal — este teste
    exercita a rede de seguranca diretamente, sem depender de
    encontrar um elemento real com matriz assimetrica.
    """
    import openstruct.results.analysis_result as analysis_result_module

    def _broken_solve(k_ff: np.ndarray, f_f: np.ndarray, method: str = "auto") -> np.ndarray:
        return np.full_like(f_f, fill_value=1.0e9)  # deliberadamente errado

    monkeypatch.setattr(analysis_result_module, "solve_linear_system", _broken_solve)

    model = _cantilever()
    load = LoadCase("P", (NodalLoad(2, fy=-10000.0),))
    with pytest.raises(EquilibriumResidualError):
        run_analysis(model, load)


def test_run_analysis_with_empty_load_case_gives_zero_displacement() -> None:
    model = _cantilever()
    result = run_analysis(model, LoadCase("Vazio"))
    for vector in result.displacements.values():
        assert np.allclose(vector, np.zeros(6))
    assert np.allclose(result.reactions[1], np.zeros(6))
