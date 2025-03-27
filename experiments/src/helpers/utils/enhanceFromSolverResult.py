from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from src.helpers.runners.model import RunnerResult


def enhance_problem_from_solver_result(
    solver_result: RunnerResult, problem: MultiObjectiveLpProblem
) -> MultiObjectiveLpProblem:
    for variable in problem.variables():
        variable.setInitialValue(
            1 if variable.name in solver_result["selected"] else 0
        )
    return problem
