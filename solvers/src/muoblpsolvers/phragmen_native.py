import logging

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver, LpStatusNotSolved, LpStatusOptimal

from muoblpsolvers.election_solver import (
    molp_to_simple_election,
    validate_election_program,
)
from muoblpsolvers.utils import bindings_available, set_solved

logger = logging.getLogger(__name__)


class PhragmenNativeSolver(LpSolver):
    """C++ port of ``PhragmenSolver`` (identical selection, rank order).

    Feasibility mirrors ``lp.valid()`` over LE/EQ constraints; GE
    (lower-bound) constraints are rejected: the python FeasibilityChecker
    needs a CBC solve per check. Use ``PhragmenSolver`` for those.
    """

    name = "PhragmenNative"

    def __init__(
        self,
        mip=True,
        msg=True,
        options=None,
        timeLimit=None,
        *,
        increasing_scalings: bool = False,
        kappa: float = 1.0,
        bos_version: bool = False,
        eps: float = 1e-6,
        **kwargs,
    ):
        super().__init__(
            mip=mip,
            msg=msg,
            options=options,
            timeLimit=timeLimit,
            increasing_scalings=increasing_scalings,
            kappa=kappa,
            bos_version=bos_version,
            eps=eps,
            **kwargs,
        )

    def available(self) -> bool:
        return bindings_available()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **_):
        pb_constraint = validate_election_program(
            lp, allow_lower_bound=False, solver_name=self.name
        )
        from muoblpbindings import phragmen

        election = molp_to_simple_election(lp, pb_constraint)
        # as ElectionSolver: fully-defined 0 assignment (incl. pulp __dummy)
        for var in lp.variables():
            var.varValue = 0
        profile = [
            (candidate, list(utilities.items()))
            for candidate, utilities in election["profile"].items()
        ]
        constraints = [
            (
                constraint.sense,
                constraint.constant,
                [(var.name, coef) for var, coef in constraint.items()],
            )
            for constraint in lp.constraints.values()
        ]

        if self.msg:
            logger.info(
                "SOLVER START",
                extra={"options": self.optionsDict, "instance": lp.name},
            )
        selected, timed_out = phragmen(
            list(election["voters"].items()),
            profile,
            election["candidates"],
            constraints,
            increasing_scalings=self.optionsDict["increasing_scalings"],
            kappa=self.optionsDict["kappa"],
            bos_version=self.optionsDict["bos_version"],
            eps=self.optionsDict["eps"],
            time_limit=self.timeLimit,
        )
        if self.msg:
            logger.info(
                "SOLVER END",
                extra={"instance": lp.name, "selected": len(selected)},
            )

        set_solved(
            lp, selected, LpStatusNotSolved if timed_out else LpStatusOptimal
        )
        return lp.status
