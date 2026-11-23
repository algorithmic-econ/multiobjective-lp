import math
from collections.abc import Callable
from typing import cast

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpsolvers.election_solver import validate_pb_constraint
from pulp import LpAffineExpression

from muoblpanalyzers import native_metrics
from muoblpanalyzers.metric import Metric


def get_metrics(
    metrics: list[Metric], problem: MultiObjectiveLpProblem
) -> dict[str, dict]:
    # native handle built once per problem, only if a native metric is asked
    instance = (
        native_metrics.build_solved_instance(problem)
        if any(m in native_metrics.NATIVE_STRATEGIES for m in metrics)
        else None
    )
    results: dict[str, dict] = {}
    for metric in metrics:
        if instance is not None and metric in native_metrics.NATIVE_STRATEGIES:
            results[metric] = native_metrics.NATIVE_STRATEGIES[metric](
                instance
            )
        else:
            results[metric] = get_metric_strategy(metric)(problem)
    return results


def get_metric_strategy(
    metric: Metric,
) -> Callable[[MultiObjectiveLpProblem], dict]:
    # native metrics have no python strategy (see NATIVE_STRATEGIES)
    try:
        return PYTHON_STRATEGIES[metric]
    except KeyError:
        raise NotImplementedError("Metric not implemented") from None


def _weight(
    problem: MultiObjectiveLpProblem, objective: LpAffineExpression
) -> float:
    # voter multiplicity (deduplicated identical voters); unnamed objective
    # or name missing from objectives_weights -> 1
    name = objective.name
    if name is None:
        return 1
    weight = problem.objectives_weights.get(name, 1)
    if not (math.isfinite(weight) and weight > 0):
        raise ValueError(
            f"Objective {name} has invalid weight {weight} (expected finite"
            " and > 0)"
        )
    return weight


def _voter_count(problem: MultiObjectiveLpProblem) -> float:
    # summed in objectives order (native mirrors it -> bit-identical)
    return sum(_weight(problem, obj) for obj in problem.objectives)


def exclusion_ratio(problem: MultiObjectiveLpProblem) -> dict:
    zero_weight = sum(
        _weight(problem, obj) for obj in problem.objectives if obj.value() == 0
    )
    return {
        "exclusion_ratio": zero_weight / _voter_count(problem),
    }


def sum_objectives(problem: MultiObjectiveLpProblem) -> dict:
    # expects a solved problem: every variable has a value, so value() is
    # never None here
    return {
        "sum": sum(
            _weight(problem, obj) * cast(float, obj.value())
            for obj in problem.objectives
        ),
    }


def total_cost(problem: MultiObjectiveLpProblem) -> dict:
    pb_constraint = validate_pb_constraint(problem)
    costs = {candidate.name: cost for candidate, cost in pb_constraint.items()}
    selected = [v for v in problem.variables() if v.value() == 1.0]
    return {
        "total_cost": sum(costs[c.name] for c in selected),
    }


def invalid_constraints(problem: MultiObjectiveLpProblem) -> dict:
    total_budget_constraint = validate_pb_constraint(problem)
    return {
        "pb_constraint": total_budget_constraint.valid(),
        "invalid_count": sum(
            1 if not c.valid() else 0 for c in problem.constraints.values()
        ),
    }


def instance_size(problem: MultiObjectiveLpProblem) -> dict:
    return {"size": len(problem.variables())}


def ejr_plus(problem: MultiObjectiveLpProblem) -> dict:
    # TODO: Check if utility was COST based
    # TODO: Introduce metric options, i.e., pass up_to_one as config parameter
    up_to_one = True

    costs: dict[str, int] = {
        candidate.name: cost
        for constraint in problem.constraints.values()
        for candidate, cost in constraint.items()
    }

    total_budget = abs(validate_pb_constraint(problem).constant)

    # (voter, satisfaction, weight); weight w == w identical voters
    voter_satisfaction = sorted(
        [
            (voter, cast(float, voter.value()), _weight(problem, voter))
            for voter in problem.objectives
        ],
        key=lambda v_sat_w: v_sat_w[1],
    )
    voter_count = _voter_count(problem)
    failures = []

    for project in problem.variables():
        if project.value() == 1:  # skip elected
            continue
        coalition_size = 0
        for voter, satisfaction, weight in voter_satisfaction:
            # if voter approved of project
            if project in voter:
                # w identical voters share satisfaction: checking only the
                # largest coalition (strictest threshold) is equivalent
                coalition_size += weight
                ejr_satisfied = satisfaction >= (
                    coalition_size / voter_count
                ) * total_budget - (costs[project.name] if up_to_one else 0)
                if not ejr_satisfied:
                    failures.append(project.name)
                    break

    return {"ejr_plus": len(failures)}


PYTHON_STRATEGIES: dict[Metric, Callable[[MultiObjectiveLpProblem], dict]] = {
    Metric.EXCLUSION_RATIO: exclusion_ratio,
    Metric.SUM_OBJECTIVES: sum_objectives,
    Metric.EJR_PLUS: ejr_plus,
    Metric.CONSTRAINTS: invalid_constraints,
    Metric.INSTANCE_SIZE: instance_size,
    Metric.TOTAL_COST: total_cost,
}
