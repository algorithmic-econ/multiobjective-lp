import time
from collections import defaultdict

from pulp import LpSolver

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpsolvers.mes.binding.build.mes import equal_shares


class MethodOfEqualSharesSolver(LpSolver):
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
        print(f"STARTING MES {start_time}")
        selected = equal_shares(voters, projects, costs, approvals, total_budget)
        print(f"FINISHED MES {time.time() - start_time}")

        for variable in lp.variables():
            variable.setInitialValue(1 if variable.name in selected else 0)
        return
