import time
from collections import defaultdict
from typing import TypedDict

from pulp import LpSolver
from muoblpsolvers.mes.binding.build.mes import equal_shares

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpsolvers.mes_constrains.utils import (
    set_selected_candidates,
    get_infeasible_constraints,
    get_feasibility_ratio,
)


class SolverOptions(TypedDict):
    cost_modification_base: float
    max_iterations: int


class MethodOfEqualSharesConstrainsSolver(LpSolver):
    """

    Info:
        Method Of Equal Shares with Constraints solver
    """

    def __init__(self, solver_options):
        super().__init__()
        self.solver_options = solver_options

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        print(
            f"Starting MethodOfEqualSharesConstrainsSolver {self.solver_options}"
        )
        """
        Parameters:
            lp: Instance of MultiObjectiveLpProblem
        """
        projects = [
            variable.name
            for variable in lp.variables()
            if variable.name != "__dummy"
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
        while iteration < self.solver_options["max_iterations"]:
            # Run MES
            start_time = time.time()
            selected = equal_shares(
                voters, projects, costs, approvals, total_budget
            )
            print(f"FINISHED MES {time.time() - start_time:.2f} s\n")
            set_selected_candidates(lp, selected)

            # Check constraints
            infeasible = get_infeasible_constraints(lp)
            for c in infeasible:
                print(
                    f"FEAS_RATIO|{iteration}|{c.name}|{get_feasibility_ratio(c):.4f}"
                )

            if len(infeasible) == 0:
                print(
                    "============== all constraints fulfilled =============="
                )
                break

            # Modify prices
            # TODO: Extract to parametrized strategy
            for constraint in infeasible:
                feasibility_ratio = get_feasibility_ratio(
                    constraint
                )  # ratio: [0, inf)
                cost_modification_ratio = feasibility_ratio * (
                    self.solver_options["cost_modification_base"] ** iteration
                )  # exponential backoff
                affected_candidates = [
                    candidate.name for candidate in constraint.keys()
                ]
                print(
                    f"Modifying cost of {len(affected_candidates)} variables with ratio {cost_modification_ratio:.4f}"
                )
                for candidate in affected_candidates:
                    costs[candidate] = int(
                        costs[candidate] * cost_modification_ratio
                    )

            iteration += 1
