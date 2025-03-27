import time
from collections import defaultdict

from pulp import LpSolver
from muoblpsolvers.mes.binding.build.mes import equal_shares

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpsolvers.mes_constrains.utils import (
    set_selected_candidates,
    get_infeasible_constraints,
    get_feasibility_ratio,
)

MAX_ITERATIONS = 100


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

        iteration = 0
        while iteration < MAX_ITERATIONS:
            # Run MES
            start_time = time.time()
            selected = equal_shares(voters, projects, costs, approvals, total_budget)
            print(f"FINISHED MES {time.time() - start_time:.2f} s")
            set_selected_candidates(lp, selected)

            # Check constraints
            infeasible = get_infeasible_constraints(lp)
            for c in infeasible:
                print(
                    f"FEAS_RATIO|{iteration}|{c.name}|{get_feasibility_ratio(c):.4f}\n"
                )

            if len(infeasible) == 0:
                print("============== all constraints fulfilled ==============")
                break

            # Modify prices
            for constraint in infeasible:
                feasibility_ratio = get_feasibility_ratio(constraint)  # ratio: [0, inf)
                cost_modification_ratio = feasibility_ratio * (
                    1.005**iteration
                )  # exponential backoff
                affected_candidates = [
                    candidate.name for candidate in constraint.keys()
                ]
                print(
                    f"Modifying cost of {len(affected_candidates)} variables with ratio {cost_modification_ratio:.4f}"
                )
                for candidate in affected_candidates:
                    costs[candidate] = int(costs[candidate] * cost_modification_ratio)

            iteration += 1
