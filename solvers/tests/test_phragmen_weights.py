"""Weighted Phragmen: a weight-w voter must behave as w identical voters,
regardless of voter order.
"""

import itertools
import random

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable, lpSum

from muoblpsolvers import PhragmenSolver
from muoblpsolvers.phragmen import update_local_scalings

# voter -> (weight, {candidate: utility}), costs, budget
Spec = tuple[dict[str, tuple[int, dict[str, int]]], dict[str, int], int]


def scalings(order, weights, spent, timestamp=2.0):
    """Local scalings for one candidate (cost 10), all utilities 1."""
    local = {v: 0.0 for v in weights}
    update_local_scalings(
        local,
        remaining={"c"},
        timestamp=timestamp,
        m_spent=spent,
        sorted_utils={"c": [(v, 1.0) for v in order]},
        candidates={"c": 10.0},
        weights=weights,
    )
    return local


def test_scalings_ignore_overspent_voters_order():
    """Voters with m_spent > timestamp must not make scalings order-dependent."""
    weights = {"a1": 1.0, "a2": 1.0, "b": 1.0}
    spent = {"a1": 5.0, "a2": 5.0, "b": 0.0}
    results = [
        scalings(order, weights, spent)
        for order in itertools.permutations(weights)
    ]
    for result in results:
        assert result == pytest.approx({"a1": 0.2, "a2": 0.2, "b": 0.2})


def test_scalings_weighted_equals_expanded():
    expanded = scalings(
        ["a1", "b", "a2"],
        {"a1": 1.0, "a2": 1.0, "b": 1.0},
        {"a1": 5.0, "a2": 5.0, "b": 0.0},
    )
    for order in (["a", "b"], ["b", "a"]):
        weighted = scalings(order, {"a": 2.0, "b": 1.0}, {"a": 5.0, "b": 0.0})
        assert weighted["a"] == pytest.approx(expanded["a1"])
        assert weighted["b"] == pytest.approx(expanded["b"])


def build(spec: Spec, expand: bool, seed: int) -> MultiObjectiveLpProblem:
    """Weighted problem, or w copies per voter in shuffled order."""
    ballots, costs, budget = spec
    variables = {c: LpVariable(c, cat="Binary") for c in costs}
    entries = [
        (name, utilities)
        for voter, (weight, utilities) in ballots.items()
        for name in (
            [f"{voter}_{k}" for k in range(weight)] if expand else [voter]
        )
    ]
    random.Random(seed).shuffle(entries)
    objectives = [
        LpAffineExpression(
            {variables[c]: u for c, u in utilities.items()}, name=name
        )
        for name, utilities in entries
    ]
    weights = {} if expand else {v: float(w) for v, (w, _) in ballots.items()}
    problem = MultiObjectiveLpProblem(
        "weighted", objectives=objectives, objectives_weights=weights
    )
    problem += (
        lpSum(cost * variables[c] for c, cost in costs.items()) <= budget,
        "pb",
    )
    return problem


def solve(problem: MultiObjectiveLpProblem, bos_version: bool) -> list[str]:
    problem.solve(PhragmenSolver(msg=False, bos_version=bos_version))
    return sorted(v.name for v in problem.variables() if v.value() == 1)


def random_spec(seed: int, cost_utility: bool) -> Spec:
    rng = random.Random(seed)
    candidates = [f"p{j}" for j in range(rng.randint(2, 10))]
    costs = {c: rng.randint(1, 400) for c in candidates}
    ballots: dict[str, tuple[int, dict[str, int]]] = {}
    for i in range(rng.randint(2, 15)):
        approved = rng.sample(candidates, rng.randint(1, len(candidates)))
        ballots[f"v{i}"] = (
            rng.randint(1, 5),
            {c: costs[c] if cost_utility else 1 for c in approved},
        )
    budget = rng.randint(max(costs.values()), sum(costs.values()))
    return ballots, costs, budget


@pytest.mark.parametrize("bos_version", [False, True])
@pytest.mark.parametrize("cost_utility", [True, False], ids=["COST", "APPR"])
@pytest.mark.parametrize("seed", range(40))
def test_weighted_equals_shuffled_expansion(seed, cost_utility, bos_version):
    spec = random_spec(seed, cost_utility)
    weighted = solve(build(spec, expand=False, seed=seed), bos_version)
    expanded = solve(build(spec, expand=True, seed=seed), bos_version)
    assert weighted == expanded
