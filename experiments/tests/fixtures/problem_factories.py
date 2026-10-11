import random

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable, lpSum


def make_tiny_problem() -> MultiObjectiveLpProblem:
    """2 candidates: p1 ($100, selected), p2 ($200, not selected).
    2 voters: v1 approves p1, v2 approves both."""
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p1.setInitialValue(1)
    p2.setInitialValue(0)

    v1 = LpAffineExpression({p1: 100})
    v2 = LpAffineExpression({p1: 100, p2: 200})

    problem = MultiObjectiveLpProblem(
        "tiny", objectives=[v1, v2], objectives_weights={}
    )
    # PB constraint: covers all candidates, sense <=
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"
    return problem


def make_ejr_violation_problem() -> MultiObjectiveLpProblem:
    """4 voters, budget 250. p1 ($100, selected), p2 ($10, NOT selected).

    v1/v2 approve only p1 (satisfaction 100 each); v3/v4 approve only p2
    (satisfaction 0 each, since p2 is unselected). p2 is cheap and has a
    2-voter support group that got nothing -> EJR+ violation.
    """
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p1.setInitialValue(1)
    p2.setInitialValue(0)

    v1 = LpAffineExpression({p1: 100})
    v2 = LpAffineExpression({p1: 100})
    v3 = LpAffineExpression({p2: 10})
    v4 = LpAffineExpression({p2: 10})

    problem = MultiObjectiveLpProblem(
        "ejr_violation", objectives=[v1, v2, v3, v4], objectives_weights={}
    )
    problem += 100 * p1 + 10 * p2 <= 250, "pb_constraint"
    return problem


def make_all_excluded_problem() -> MultiObjectiveLpProblem:
    """Nothing selected -> every voter's objective is 0 (ratio 1.0)."""
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p1.setInitialValue(0)
    p2.setInitialValue(0)

    v1 = LpAffineExpression({p1: 100})
    v2 = LpAffineExpression({p1: 100, p2: 200})
    v3 = LpAffineExpression({p2: 200})

    problem = MultiObjectiveLpProblem(
        "all_excluded", objectives=[v1, v2, v3], objectives_weights={}
    )
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"
    return problem


def make_none_excluded_problem() -> MultiObjectiveLpProblem:
    """p1, p2 selected, p3 not; every voter approves a selected candidate
    (ratio 0.0)."""
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p3 = LpVariable("p3", cat="Binary")
    p1.setInitialValue(1)
    p2.setInitialValue(1)
    p3.setInitialValue(0)

    v1 = LpAffineExpression({p1: 10})
    v2 = LpAffineExpression({p2: 20, p3: 30})
    v3 = LpAffineExpression({p1: 10, p2: 20, p3: 30})

    problem = MultiObjectiveLpProblem(
        "none_excluded", objectives=[v1, v2, v3], objectives_weights={}
    )
    problem += 10 * p1 + 20 * p2 + 30 * p3 <= 100, "pb_constraint"
    return problem


def make_objective_only_variable_problem() -> MultiObjectiveLpProblem:
    """p3 (selected), p4 (not selected) appear in objectives only, in no
    constraint -> `problem.variables()` lists just p1, p2.

    v1 = 10 (p1 sel), v2 = 0 (p2 unsel), v3 = 7 (p3 sel, objective-only),
    v4 = 0 (p4 unsel, objective-only) -> ratio 0.5. Ignoring p3 would give
    0.75.
    """
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p3 = LpVariable("p3", cat="Binary")
    p4 = LpVariable("p4", cat="Binary")
    p1.setInitialValue(1)
    p2.setInitialValue(0)
    p3.setInitialValue(1)
    p4.setInitialValue(0)

    v1 = LpAffineExpression({p1: 10})
    v2 = LpAffineExpression({p2: 20})
    v3 = LpAffineExpression({p3: 7})
    v4 = LpAffineExpression({p4: 9})

    problem = MultiObjectiveLpProblem(
        "objective_only", objectives=[v1, v2, v3, v4], objectives_weights={}
    )
    problem += 10 * p1 + 20 * p2 <= 25, "pb_constraint"
    return problem


def make_multi_constraint_problem() -> MultiObjectiveLpProblem:
    """5 candidates, 4 constraints: total budget + district caps (<=) +
    one lower-bound (>=). p1, p3 selected; positive int coefficients and
    non-empty named objectives (survives the LP roundtrip).

    v1 = 10, v2 = 0 (p2), v3 = 5 (p3), v4 = 0 (p4), v5 = 1 (p1),
    v6 = 0 (p5) -> 3 of 6 excluded -> 0.5.
    """
    p = {i: LpVariable(f"p{i}", cat="Binary") for i in range(1, 6)}
    for i, var in p.items():
        var.setInitialValue(1 if i in (1, 3) else 0)

    objectives = [
        LpAffineExpression({p[1]: 10}, name="v1"),
        LpAffineExpression({p[2]: 10}, name="v2"),
        LpAffineExpression({p[3]: 5, p[4]: 5}, name="v3"),
        LpAffineExpression({p[4]: 8}, name="v4"),
        LpAffineExpression({p[1]: 1, p[5]: 2}, name="v5"),
        LpAffineExpression({p[5]: 4}, name="v6"),
    ]
    problem = MultiObjectiveLpProblem(
        "multi_constraint", objectives=objectives, objectives_weights={}
    )
    problem += (
        10 * p[1] + 20 * p[2] + 30 * p[3] + 40 * p[4] + 50 * p[5] <= 100,
        "total_budget",
    )
    problem += 10 * p[1] + 20 * p[2] <= 25, "district_a"
    problem += 30 * p[3] + 40 * p[4] + 50 * p[5] <= 80, "district_b"
    problem += 30 * p[3] + 40 * p[4] >= 20, "district_b_min"
    return problem


def make_weighted_objectives_problem() -> MultiObjectiveLpProblem:
    """Named objectives with `objectives_weights` != 1 (as after
    deduplicate_objectives). Both implementations ignore weights.

    T_v1 = 100, T_v2 = 0, T_v3 = 100 (p1 selected) -> 1 of 3 excluded.
    """
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p1.setInitialValue(1)
    p2.setInitialValue(0)

    objectives = [
        LpAffineExpression({p1: 100}, name="T_v1"),
        LpAffineExpression({p2: 200}, name="T_v2"),
        LpAffineExpression({p1: 100, p2: 200}, name="T_v3"),
    ]
    problem = MultiObjectiveLpProblem(
        "weighted",
        objectives=objectives,
        objectives_weights={"T_v1": 3, "T_v2": 2.5, "T_v3": 0.5},
    )
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"
    return problem


def make_float_constant_problem() -> MultiObjectiveLpProblem:
    """Float coefficients + constants; all of p1, p2, p3 selected.

    a: 1.5 - 1.5 = 0 exactly -> excluded
    b: 2.5 + 0.5 = 3.0 -> kept
    c: constant-only 3.0 -> kept
    d: constant-only 0 -> excluded
    e: 0.1 + 0.2 - 0.3 = 5.55e-17 (float rounding, NOT 0) -> kept
    -> 2 of 5 excluded -> 0.4.
    """
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p3 = LpVariable("p3", cat="Binary")
    for var in (p1, p2, p3):
        var.setInitialValue(1)

    objectives = [
        LpAffineExpression({p1: 1.5, p2: -1.5}),
        LpAffineExpression({p1: 0.5}, constant=2.5),
        LpAffineExpression(constant=3.0),
        LpAffineExpression(constant=0),
        LpAffineExpression({p1: 0.1, p2: 0.2, p3: -0.3}),
    ]
    problem = MultiObjectiveLpProblem(
        "float_constant", objectives=objectives, objectives_weights={}
    )
    problem += 10 * p1 + 10 * p2 + 10 * p3 <= 100, "pb_constraint"
    return problem


def make_random_problem(seed: int) -> MultiObjectiveLpProblem:
    """Deterministic per seed: 1-40 voters, 1-15 candidates, each voter
    approves a random (possibly empty) subset with int utilities 1-100;
    selection is none / all / random; one budget constraint."""
    rng = random.Random(seed)
    n_voters = rng.randint(1, 40)
    n_candidates = rng.randint(1, 15)

    candidates = [
        LpVariable(f"p{j}", cat="Binary") for j in range(n_candidates)
    ]
    mode = rng.choice(["none", "all", "random"])
    for candidate in candidates:
        if mode == "none":
            selected = 0
        elif mode == "all":
            selected = 1
        else:
            selected = rng.randint(0, 1)
        candidate.setInitialValue(selected)

    objectives = []
    for _ in range(n_voters):
        approved = rng.sample(candidates, rng.randint(0, n_candidates))
        objectives.append(
            LpAffineExpression(
                {candidate: rng.randint(1, 100) for candidate in approved}
            )
        )

    problem = MultiObjectiveLpProblem(
        f"random_{seed}", objectives=objectives, objectives_weights={}
    )
    costs = [rng.randint(1, 100) for _ in candidates]
    problem += (
        lpSum(cost * c for cost, c in zip(costs, candidates))
        <= sum(costs) // 2 + 1,
        "pb_constraint",
    )
    return problem


HANDCRAFTED_FACTORIES = (
    make_tiny_problem,
    make_ejr_violation_problem,
    make_all_excluded_problem,
    make_none_excluded_problem,
    make_objective_only_variable_problem,
    make_multi_constraint_problem,
    make_weighted_objectives_problem,
    make_float_constant_problem,
)
