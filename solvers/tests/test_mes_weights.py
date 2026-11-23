"""Weighted MES: a weight-w voter must behave as w identical voters.

Invariance instances are tie-free by construction (random large costs and
utilities): exact ties are broken by `unordered_map` order in the native
bindings, so weighted vs expanded may legitimately differ on ties.
"""

import random

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpSolver, LpVariable, lpSum

from muoblpsolvers import (
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesUtilitySolver,
)

SOLVERS = [
    MethodOfEqualSharesUtilitySolver,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
]

# (voter -> (weight, {candidate: utility})), costs, budget
Spec = tuple[dict[str, tuple[float, dict[str, int]]], dict[str, int], int]


def build(spec: Spec, expand: bool) -> MultiObjectiveLpProblem:
    """Weighted problem, or its expansion (w copies, no weights)."""
    ballots, costs, budget = spec
    variables = {c: LpVariable(c, cat="Binary") for c in costs}
    objectives = []
    weights: dict[str, float] = {}
    for voter, (weight, utilities) in ballots.items():
        copies = (
            [f"{voter}_{k}" for k in range(int(weight))] if expand else [voter]
        )
        for name in copies:
            objectives.append(
                LpAffineExpression(
                    {variables[c]: u for c, u in utilities.items()},
                    name=name,
                )
            )
        if not expand:
            weights[voter] = weight
    problem = MultiObjectiveLpProblem(
        "weighted", objectives=objectives, objectives_weights=weights
    )
    problem += (
        lpSum(cost * variables[c] for c, cost in costs.items()) <= budget,
        "pb",
    )
    return problem


def solve(solver_cls: type[LpSolver], problem: MultiObjectiveLpProblem):
    solver = solver_cls(msg=False)
    if not solver.available():
        pytest.skip("muoblpbindings not installed")
    problem.solve(solver)
    return sorted(v.name for v in problem.variables() if v.value() == 1)


# bloc b (w=4) alone affords A (cost 200) only when weighted:
# weighted W=6 -> 50/copy, bloc holds 200; unweighted n=3 -> 100/voter.
# B (90, x+y) first (rho 45); then weighted: A (rho 50), C unaffordable;
# unweighted: A unaffordable, C (rho 50, x/y hold 55 each).
BLOC: Spec = (
    {
        "b": (4, {"A": 1}),
        "x": (1, {"B": 1, "C": 1}),
        "y": (1, {"B": 1, "C": 1}),
    },
    {"A": 200, "B": 90, "C": 100},
    300,
)


@pytest.mark.parametrize(
    "solver_cls",
    [MethodOfEqualSharesUtilitySolver, MethodOfEqualSharesAdd1Solver],
)
def test_weighted_bloc_affords_project(solver_cls):
    assert solve(solver_cls, build(BLOC, expand=False)) == ["A", "B"]


@pytest.mark.parametrize(
    "solver_cls",
    [MethodOfEqualSharesUtilitySolver, MethodOfEqualSharesAdd1Solver],
)
def test_unit_weights_ignore_bloc(solver_cls):
    ballots, costs, budget = BLOC
    unit = {v: (1.0, u) for v, (_, u) in ballots.items()}
    assert solve(solver_cls, build((unit, costs, budget), False)) == [
        "B",
        "C",
    ]


@pytest.mark.parametrize("solver_cls", SOLVERS)
def test_float_and_scaled_weights(solver_cls):
    """Float weights accepted; MES invariant to scaling all weights."""
    ballots, costs, budget = BLOC
    for scale in (1.0, 0.5, 2.5):
        scaled = {v: (w * scale, u) for v, (w, u) in ballots.items()}
        problem = build((scaled, costs, budget), expand=False)
        assert solve(solver_cls, problem) == ["A", "B"], scale


def random_spec(seed: int) -> Spec:
    rng = random.Random(seed)
    n_voters = rng.randint(1, 12)
    candidates = [f"p{j}" for j in range(rng.randint(1, 8))]
    ballots: dict[str, tuple[float, dict[str, int]]] = {}
    for i in range(n_voters):
        approved = rng.sample(candidates, rng.randint(1, len(candidates)))
        ballots[f"v{i}"] = (
            rng.randint(1, 3),
            {c: rng.randint(1, 10**6) for c in approved},
        )
    costs = {c: rng.randint(10**3, 10**6) for c in candidates}
    return ballots, costs, sum(costs.values()) // 2 + 1


@pytest.mark.parametrize("solver_cls", SOLVERS)
@pytest.mark.parametrize("spec", [BLOC], ids=["bloc"])
def test_invariance_handcrafted(solver_cls, spec):
    assert solve(solver_cls, build(spec, False)) == solve(
        solver_cls, build(spec, True)
    )


@pytest.mark.parametrize("solver_cls", SOLVERS)
@pytest.mark.parametrize("seed", range(40))
def test_invariance_random(solver_cls, seed):
    spec = random_spec(seed)
    assert solve(solver_cls, build(spec, False)) == solve(
        solver_cls, build(spec, True)
    )
