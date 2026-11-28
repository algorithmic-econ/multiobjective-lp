"""Native PhragmenNative == python Phragmen (same rank, incl. tie order)."""

import random
from collections.abc import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpAffineExpression,
    LpStatusNotSolved,
    LpStatusOptimal,
    LpVariable,
    PulpSolverError,
    lpSum,
)

from muoblpsolvers import PhragmenNativeSolver
from muoblpsolvers.election_solver import (
    molp_to_simple_election,
    validate_election_program,
)
from muoblpsolvers.phragmen import phragmen_cardinal

from .test_phragmen_weights import build, random_spec


def selected(problem: MultiObjectiveLpProblem) -> list[str]:
    return sorted(v.name for v in problem.variables() if v.value() == 1)


def python_rank(problem: MultiObjectiveLpProblem, **options) -> list[str]:
    pb = validate_election_program(problem, allow_lower_bound=False)
    election = molp_to_simple_election(problem, pb)
    for var in problem.variables():
        var.varValue = 0
    return phragmen_cardinal(problem, election, **options)


def native_rank(problem: MultiObjectiveLpProblem, **options) -> list[str]:
    from muoblpbindings import phragmen

    pb = validate_election_program(problem, allow_lower_bound=False)
    election = molp_to_simple_election(problem, pb)
    rank, timed_out = phragmen(
        list(election["voters"].items()),
        [(c, list(u.items())) for c, u in election["profile"].items()],
        election["candidates"],
        [
            (c.sense, c.constant, [(v.name, x) for v, x in c.items()])
            for c in problem.constraints.values()
        ],
        **options,
    )
    assert not timed_out
    return rank


def random_problem(seed: int, kind: str) -> MultiObjectiveLpProblem:
    """Random PB; kind: COST (int u = cost), APPR (u = 1), FLOAT (float u,
    some <= eps). Float weights, optional extra LE + EQ constraints."""
    rng = random.Random(seed)
    candidates = [f"p{j}" for j in range(rng.randint(2, 12))]
    costs = {c: rng.randint(1, 400) for c in candidates}
    variables = {c: LpVariable(c, cat="Binary") for c in candidates}
    objectives, weights = [], {}
    for i in range(rng.randint(2, 20)):
        approved = rng.sample(candidates, rng.randint(1, len(candidates)))
        if kind == "COST":
            utilities = {c: costs[c] for c in approved}
        elif kind == "APPR":
            utilities = {c: 1 for c in approved}
        else:
            utilities = {
                c: rng.choice([1e-7, rng.uniform(0, 5)]) for c in approved
            }
        objectives.append(
            LpAffineExpression(
                {variables[c]: u for c, u in utilities.items()}, name=f"v{i}"
            )
        )
        weights[f"v{i}"] = rng.choice([1, 2, 0.5, rng.uniform(0.1, 3)])
    problem = MultiObjectiveLpProblem(
        "random", objectives=objectives, objectives_weights=weights
    )
    budget = rng.randint(max(costs.values()), sum(costs.values()))
    problem += (
        lpSum(cost * variables[c] for c, cost in costs.items()) <= budget,
        "pb",
    )
    if rng.random() < 0.5:
        district = rng.sample(candidates, rng.randint(1, len(candidates) - 1))
        cap = rng.randint(1, sum(costs[c] for c in district))
        problem += (
            lpSum(costs[c] * variables[c] for c in district) <= cap,
            "district",
        )
    if rng.random() < 0.3:
        problem += (variables[rng.choice(candidates)] == 0, "banned")
    return problem


@pytest.mark.parametrize("kappa", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("increasing_scalings", [False, True])
@pytest.mark.parametrize("bos_version", [False, True])
@pytest.mark.parametrize("kind", ["COST", "APPR", "FLOAT"])
@pytest.mark.parametrize("seed", range(25))
def test_native_rank_equals_python(
    seed, kind, bos_version, increasing_scalings, kappa
):
    options = {
        "bos_version": bos_version,
        "increasing_scalings": increasing_scalings,
        "kappa": kappa,
    }
    problem = random_problem(seed, kind)
    expected = python_rank(problem, **options)
    assert native_rank(problem, **options) == expected


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E", "_F"]),
        ("COST", ["_A", "_C", "_E", "_F"]),
    ],
)
def test_native_solver(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
    expected: list[str],
):
    problem = basic_pb_factory(utility_type)
    problem.solve(PhragmenNativeSolver(msg=False))

    assert problem.status == LpStatusOptimal
    assert selected(problem) == sorted(expected)


@pytest.mark.parametrize("bos_version", [False, True])
@pytest.mark.parametrize("cost_utility", [True, False], ids=["COST", "APPR"])
@pytest.mark.parametrize("seed", range(20))
def test_native_weighted_equals_shuffled_expansion(
    seed, cost_utility, bos_version
):
    spec = random_spec(seed, cost_utility)
    results = []
    for expand in (False, True):
        problem = build(spec, expand=expand, seed=seed)
        problem.solve(PhragmenNativeSolver(msg=False, bos_version=bos_version))
        results.append(selected(problem))
    assert results[0] == results[1]


def test_native_rejects_lower_bound(
    pb_with_lb_factory: Callable[[str], MultiObjectiveLpProblem],
):
    with pytest.raises(PulpSolverError, match="lower-bound"):
        pb_with_lb_factory("APPROVAL").solve(PhragmenNativeSolver(msg=False))


def test_native_time_limit(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
):
    problem = basic_pb_factory("APPROVAL")
    problem.solve(PhragmenNativeSolver(msg=False, timeLimit=1e-9))

    assert problem.status == LpStatusNotSolved
    assert all(v.value() in (0, 1) for v in problem.variables())
    assert problem.valid()
