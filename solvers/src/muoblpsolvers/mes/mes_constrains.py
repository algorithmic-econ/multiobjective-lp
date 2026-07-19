import logging
import time
from typing import cast

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpConstraint,
    LpConstraintGE,
    LpConstraintLE,
    LpSolver,
    LpStatusNotSolved,
    LpStatusOptimal,
)

from muoblpsolvers.election_solver import validate_election_program
from muoblpsolvers.utils import bindings_available, set_solved

from .common import prepare_mes_parameters

logger = logging.getLogger(__name__)


def get_feasibility_ratio(constraint: LpConstraint) -> float:
    """
    :rtype: object
    """
    # ratio: [0, inf)
    # constraint.value() is typed Optional by pulp 3.3.2 but every candidate
    # variable is assigned via setInitialValue before any constraint is read
    # (actualSolve's per-iteration loop) — never None in practice.
    value = cast(float, constraint.value())
    target = constraint.constant
    return (value - target) / abs(target)


# def get_modification_ratio(feasibility_ratio: float, lower: float, upper: float) -> float:
#     return lower + (upper - lower) * feasibility_ratio


def get_infeasible_constraints(
    problem: MultiObjectiveLpProblem,
) -> list[LpConstraint]:
    return [
        constraint
        for constraint in problem.constraints.values()
        if (
            constraint.sense == LpConstraintGE
            and cast(float, constraint.value()) < 0
        )
        or (
            constraint.sense == LpConstraintLE
            and cast(float, constraint.value()) > 0
        )
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
        validate_election_program(lp)
        from muoblpbindings import equal_shares_utils

        if self.msg:
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
        ) = prepare_mes_parameters(lp, msg=self.msg)

        # zero all vars up front so an abort before iteration 1 yields a
        # fully-defined 0 assignment (incl. pulp's lazy __dummy)
        for variable in lp.variables():
            variable.setInitialValue(0)

        deadline = (
            time.monotonic() + self.timeLimit
            if self.timeLimit is not None
            else None
        )
        status = LpStatusOptimal
        selected: list[str] = []
        iteration = 0
        while iteration < self.optionsDict["max_iterations"]:
            if deadline is not None and time.monotonic() > deadline:
                status = LpStatusNotSolved
                break
            # Run MES
            # TODO: weight-aware via binding update
            selected = equal_shares_utils(
                list(voters.keys()),
                projects,
                costs,
                approvals_utilities,
                total_utilities,
                total_budget,
            )
            if self.msg:
                logger.debug("FINISHED MES iteration %d", iteration)
            for variable in lp.variables():
                variable.setInitialValue(1 if variable.name in selected else 0)

            # Check constraints
            infeasible = get_infeasible_constraints(lp)
            if self.msg:
                for constraint in infeasible:
                    logger.debug(
                        f"FEAS_RATIO|{iteration}|{constraint.name}|{get_feasibility_ratio(constraint):.6f}"
                    )

            if len(infeasible) == 0:
                if self.msg:
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
                if self.msg:
                    logger.debug(
                        f"Modifying cost of {len(affected_candidates)} variables with ratio {cost_modification_ratio:.4f}"
                    )
                for candidate in affected_candidates:
                    costs[candidate] = int(
                        costs[candidate] * cost_modification_ratio
                    )

            iteration += 1
        if self.msg:
            logger.info("SOLVER END")

        set_solved(lp, selected, status)
        return lp.status
