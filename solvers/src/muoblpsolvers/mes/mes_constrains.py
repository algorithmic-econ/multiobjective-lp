import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpConstraint, LpConstraintGE, LpConstraintLE, LpSolver

from muoblpsolvers.utils import bindings_available

from .common import prepare_mes_parameters

logger = logging.getLogger(__name__)


def get_feasibility_ratio(constraint: LpConstraint) -> float:
    """
    :rtype: object
    """
    # ratio: [0, inf)
    value = constraint.value()
    target = constraint.constant
    return (value - target) / abs(target)  # pyright: ignore[reportOptionalOperand]  # constraint.value() Optional; None-guard is T13


# def get_modification_ratio(feasibility_ratio: float, lower: float, upper: float) -> float:
#     return lower + (upper - lower) * feasibility_ratio


def get_infeasible_constraints(
    problem: MultiObjectiveLpProblem,
) -> list[LpConstraint]:
    return [
        constraint
        for constraint in problem.constraints.values()
        if (constraint.sense == LpConstraintGE and constraint.value() < 0)  # pyright: ignore[reportOptionalOperand]  # pulp 3.3.2 constraint.value() Optional; None-guard T13
        or (constraint.sense == LpConstraintLE and constraint.value() > 0)  # pyright: ignore[reportOptionalOperand]
    ]


class MethodOfEqualSharesConstrainsSolver(LpSolver):
    name = "MethodOfEqualSharesConstrains"

    def __init__(
        self,
        mip=True,
        msg=True,
        options=None,
        timeLimit=None,
        *,
        cost_modification_base: float = 1.007,
        max_iterations: int = 200,
        **kwargs,
    ):
        super().__init__(
            mip=mip,
            msg=msg,
            options=options,
            timeLimit=timeLimit,
            cost_modification_base=cost_modification_base,
            max_iterations=max_iterations,
            **kwargs,
        )

    def available(self) -> bool:
        return bindings_available()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        from muoblpbindings import equal_shares_utils

        start_time = time.time()
        logger.info("SOLVER START", extra={"options": self.optionsDict})
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
        while iteration < self.optionsDict["max_iterations"]:
            # Run MES
            start_time = time.time()
            # TODO: weight-aware via binding update
            selected = equal_shares_utils(
                list(voters.keys()),
                projects,
                costs,
                approvals_utilities,
                total_utilities,
                total_budget,
            )
            logger.debug(f"FINISHED MES {time.time() - start_time:.2f} s\n")
            for variable in lp.variables():
                variable.setInitialValue(1 if variable.name in selected else 0)

            # Check constraints
            infeasible = get_infeasible_constraints(lp)
            for constraint in infeasible:
                logger.debug(
                    f"FEAS_RATIO|{iteration}|{constraint.name}|{get_feasibility_ratio(constraint):.6f}"
                )

            if len(infeasible) == 0:
                logger.debug(
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
                    self.optionsDict["cost_modification_base"] ** iteration
                )  # exponential backoff
                affected_candidates = [
                    candidate.name for candidate in constraint.keys()
                ]
                logger.debug(
                    f"Modifying cost of {len(affected_candidates)} variables with ratio {cost_modification_ratio:.4f}"
                )
                for candidate in affected_candidates:
                    costs[candidate] = int(
                        costs[candidate] * cost_modification_ratio
                    )

            iteration += 1
        logger.info("SOLVER END", extra={"time": (time.time() - start_time)})
