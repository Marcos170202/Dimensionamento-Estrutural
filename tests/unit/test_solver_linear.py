"""Testes unitarios de openstruct.solver.linear.solve_linear_system."""

from __future__ import annotations

import numpy as np
import pytest

from openstruct.solver.linear import solve_linear_system


def test_solve_simple_symmetric_system() -> None:
    k = np.array([[4.0, 1.0], [1.0, 3.0]])
    u_expected = np.array([1.0, 2.0])
    f = k @ u_expected
    u = solve_linear_system(k, f)
    assert np.allclose(u, u_expected)


@pytest.mark.parametrize("method", ["auto", "lu", "cholesky", "ldlt"])
def test_solve_agrees_across_methods_for_spd_system(method: str) -> None:
    k = np.array([[4.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]])
    u_expected = np.array([1.0, -2.0, 3.0])
    f = k @ u_expected
    u = solve_linear_system(k, f, method=method)  # type: ignore[arg-type]
    assert np.allclose(u, u_expected)


def test_solve_rejects_non_square_k() -> None:
    k = np.zeros((2, 3))
    f = np.zeros(2)
    with pytest.raises(ValueError):
        solve_linear_system(k, f)


def test_solve_rejects_incompatible_shapes() -> None:
    k = np.eye(3)
    f = np.zeros(2)
    with pytest.raises(ValueError):
        solve_linear_system(k, f)


def test_solve_rejects_unknown_method() -> None:
    k = np.eye(2)
    f = np.zeros(2)
    with pytest.raises(ValueError):
        solve_linear_system(k, f, method="bogus")  # type: ignore[arg-type]


def test_solve_larger_random_spd_system() -> None:
    rng = np.random.default_rng(seed=7)
    a = rng.uniform(-1, 1, size=(10, 10))
    k = a @ a.T + 10 * np.eye(10)  # garante SPD
    u_expected = rng.uniform(-5, 5, size=10)
    f = k @ u_expected
    u = solve_linear_system(k, f)
    assert np.allclose(u, u_expected, rtol=1e-8)
