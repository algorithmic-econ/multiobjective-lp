from collections import defaultdict

from pulp import LpSolver

from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem


class MethodOfEqualSharesConstrainsSolver(LpSolver):
    """

    Info:
        Method Of Equal Shares with Constraints solver
    """

    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        """
        Parameters:
            lp: Instance of MultiObjectiveLpProblem
        """
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
        total_budget = abs(lp.constraints['C_ub_total_budget'].constant)



