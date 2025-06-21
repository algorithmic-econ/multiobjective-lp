import time
from typing import TypedDict

from pulp import LpSolver
from muoblpbindings import equal_shares_utils

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.common import (
    prepare_mes_parameters,
    set_selected_candidates,
)
from muoblpsolvers.mes_constrains.utils import (
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
        (
            projects,
            costs,
            voters,
            approvals_utilities,
            total_utilities,
            total_budget,
        ) = prepare_mes_parameters(lp)

        iteration = 0
        while iteration < self.solver_options["max_iterations"]:
            # Run MES
            start_time = time.time()
            selected = equal_shares_utils(
                voters, projects, costs, approvals_utilities, total_budget
            )
            print(f"FINISHED MES {time.time() - start_time:.2f} s\n")
            set_selected_candidates(lp, selected)

            # Check constraints
            infeasible = get_infeasible_constraints(lp)
            for constraint in infeasible:
                print(
                    f"FEAS_RATIO|{iteration}|{constraint.name}|{get_feasibility_ratio(constraint):.6f}"
                )

            if len(infeasible) == 0:
                print(
                    "============== all constraints fulfilled =============="
                )
                break

            # TODO: Extract to parametrized strategy
            # Modify prices
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
