"""Phragmen bos_version edge cases: zero utilities, unaffordable candidates."""

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable, lpSum

from muoblpsolvers import PhragmenSolver


def solve(
    costs: dict[str, int],
    ballots: dict[str, dict[str, int]],
    budget: int,
    bos_version: bool,
) -> list[str]:
    variables = {c: LpVariable(c, cat="Binary") for c in costs}
    objectives = [
        LpAffineExpression(
            {variables[c]: u for c, u in utilities.items()}, name=voter
        )
        for voter, utilities in ballots.items()
    ]
    problem = MultiObjectiveLpProblem("bos", objectives=objectives)
    problem += (
        lpSum(cost * variables[c] for c, cost in costs.items()) <= budget,
        "pb",
    )
    problem.solve(PhragmenSolver(msg=False, bos_version=bos_version))
    return sorted(v.name for v in problem.variables() if v.value() == 1)


@pytest.mark.parametrize("bos_version", [False, True])
def test_zero_utility_equals_omitted(bos_version):
    """Explicit 0 coef (in-memory only; LP files drop it) == no coef."""
    costs = {"a": 10, "b": 10, "c": 15}
    budget = 25
    with_zero = {"v1": {"a": 1, "b": 0}, "v2": {"a": 1, "b": 1, "c": 1}}
    without = {"v1": {"a": 1}, "v2": {"a": 1, "b": 1, "c": 1}}
    assert solve(costs, with_zero, budget, bos_version) == solve(
        costs, without, budget, bos_version
    )


@pytest.mark.parametrize("bos_version", [False, True])
def test_unaffordable_candidates_skipped(bos_version):
    """Candidates with no finite rho at current T (alpha rounds to 0) must
    not be considered. Many such candidates -> one is iterated first."""
    costs = {f"e{i}": 10**8 for i in range(20)} | {"c": 1}
    ballots = {v: {c: 1 for c in costs} for v in ("v1", "v2")}
    selected = solve(costs, ballots, 10**8 + 1, bos_version)
    assert "c" in selected
    assert len(selected) == 2
