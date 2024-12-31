import time
from collections import defaultdict

from pulp import LpSolver

from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem
# from ..solvers.mes_add1.build.mes_add1 import equal_shares_add1
from ..solvers.mes.build.mes import equal_shares
# from ..solvers.python_mes import equal_shares_fixed_budget as equal_shares

class MethodOfEqualSharesSolver(LpSolver):
    """

    Info:
        Solver that executes Methods of Equal Shares to find solution

    """

    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        projects = [variable.name for variable in lp.variables() if variable.name != '__dummy']
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
        # TODO: calculation of total_budget assumes that all constraints are district UB constraint
        total_budget = sum([constraint.constant for constraint in lp.constraints.values()
                            if constraint.name.startswith('C_ub_')]) * -1

        print(f"STARTING MES {time.time()}")
        selected = equal_shares(voters, projects, costs, approvals, total_budget)
        print(f"FINISHED MES {time.time()}")

        for variable in lp.variables():
            variable.setInitialValue(1 if variable.name in selected else 0)
        return

