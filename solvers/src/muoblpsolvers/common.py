from collections import defaultdict
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


def validate_problem_data(lp: MultiObjectiveLpProblem) -> None:
    if lp.constraints["C_ub_total_budget"] is None:
        raise Exception("Problem does not have total budget")
    # TODO: add more checks


def prepare_mes_parameters(
    lp: MultiObjectiveLpProblem,
) -> tuple[
    list[str],
    list[str],
    dict[str, float],
    dict[str, list[tuple[str, float]]],
    float,
]:
    projects = [
        variable.name
        for variable in lp.variables()
        if variable.name != "__dummy"
    ]
    voters = [objective.name for objective in lp.objectives]
    costs = {
        variable.name: coefficient
        # TODO: some constraints can have repeated variables, but we just override them with the same value
        for constraint in lp.constraints.values()
        for variable, coefficient in constraint.items()
    }
    approvals_utilities = defaultdict(list)
    for objective in lp.objectives:
        for variable, coefficient in objective.items():
            approvals_utilities[variable.name] += [
                (objective.name, coefficient)
            ]

    validate_problem_data(lp)
    total_budget = abs(lp.constraints["C_ub_total_budget"].constant)
    return projects, voters, costs, approvals_utilities, total_budget


def set_selected_candidates(
    problem: MultiObjectiveLpProblem, selected: list[str]
) -> None:
    for variable in problem.variables():
        variable.setInitialValue(1 if variable.name in selected else 0)
