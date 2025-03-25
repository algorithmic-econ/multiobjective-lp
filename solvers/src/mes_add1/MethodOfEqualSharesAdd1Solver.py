import time
from collections import defaultdict

from pulp import LpSolver

from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem
from solvers.mes_add1.binding.build.mes_add1 import equal_shares_add1


class MethodOfEqualSharesAdd1Solver(LpSolver):
    """

    Info:
        Solver that executes Methods of Equal Shares to find solution

    """

    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        projects = [
            variable.name for variable in lp.variables() if variable.name != "__dummy"
        ]
        voters = [objective.name for objective in lp.objectives]
        costs = {
            variable.name: coefficient
            for constraint in lp.constraints.values()
            for variable, coefficient in constraint.items()
        }
        approvals = defaultdict(list)
        for objective in lp.objectives:
            for variable in objective:
                approvals[variable.name] += [objective.name]
        total_budget = abs(lp.constraints["C_ub_total_budget"].constant)

        start_time = time.time()
        print(f"STARTING MES_ADD1 {start_time}")
        selected = equal_shares_add1(voters, projects, costs, approvals, total_budget)
        print(f"FINISHED MES_ADD1 {time.time() - start_time}")

        for variable in lp.variables():
            variable.setInitialValue(1 if variable.name in selected else 0)
        return
