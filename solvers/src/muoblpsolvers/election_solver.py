import logging
from collections import defaultdict
from typing import TypedDict

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    PULP_CBC_CMD,
    LpConstraint,
    LpConstraintGE,
    LpConstraintLE,
    LpMinimize,
    LpProblem,
    LpSolver,
    LpStatusOptimal,
    LpVariable,
    PulpSolverError,
    lpSum,
)

from muoblpsolvers.types import CandidateId, Cost, Utility, VoterId

logger = logging.getLogger(__name__)


class Election(TypedDict):
    profile: dict[CandidateId, dict[VoterId, Utility]]
    candidates: dict[CandidateId, Cost]
    voters: dict[VoterId, float]


class ElectionSolver(LpSolver):
    def available(self) -> bool:
        return True

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs):
        validate_election_program(lp)
        election = molp_to_simple_election(lp)

        for var in lp.variables():
            var.varValue = 0

        return self._solve_election(lp, election, kwargs=kwargs)

    @staticmethod
    def is_feasible(lp: MultiObjectiveLpProblem) -> bool:
        """Single-shot feasibility check. Loops should reuse a
        ``FeasibilityChecker`` instead (avoids rebuilding the sub-model)."""
        return FeasibilityChecker(lp).check()

    def _solve_election(
        self, lp: MultiObjectiveLpProblem, election: Election, **kwargs
    ):
        raise NotImplementedError(
            "Subclasses must implement the solve_election method."
        )


class FeasibilityChecker:
    """Single feasibility impl, reused across candidate checks in a loop.

    ``lp.valid()`` alone is insufficient with lower-bound (GE) constraints:
    a partial assignment can violate a GE bound that later selections would
    satisfy, so a plain ``valid()`` would wrongly reject candidates. When GE
    constraints are present we instead LP-solve a completion problem
    (candidates currently set to 1 are fixed to 1, the rest stay free binary)
    and accept iff it is feasible.

    The completion sub-model is built ONCE at construction and reused: each
    ``check()`` only flips the fixed lowBounds and re-solves, instead of
    rebuilding a fresh CBC problem per candidate.
    """

    def __init__(self, lp: MultiObjectiveLpProblem) -> None:
        self.lp = lp
        self.has_lowerbound_constraint = any(
            c.sense == LpConstraintGE for c in lp.constraints.values()
        )
        self._candidates: list[str] = []
        self._new_variables: dict[str, LpVariable] = {}
        self._prob: LpProblem | None = None
        self._solver = None
        if self.has_lowerbound_constraint:
            self._build_completion_problem()

    def _build_completion_problem(self) -> None:
        self._candidates = [
            v.name for v in self.lp.variables() if v.name != "__dummy"
        ]
        self._new_variables = {
            name: LpVariable(name, cat="Binary") for name in self._candidates
        }
        prob = LpProblem("feasibility", LpMinimize)
        prob += 0
        for name, constraint in self.lp.constraints.items():
            items = [
                (self._new_variables[v.name], coef)
                for v, coef in constraint.items()
                if v.name in self._new_variables
            ]
            if items:
                prob += LpConstraint(
                    lpSum(coef * v for v, coef in items),
                    sense=constraint.sense,
                    rhs=-constraint.constant,
                    name=name,
                )
        self._prob = prob
        self._solver = PULP_CBC_CMD(msg=False)

    def check(self) -> bool:
        if not self.has_lowerbound_constraint:
            return self.lp.valid()

        assert self._prob is not None
        variables = self.lp.variablesDict()
        for name in self._candidates:
            self._new_variables[name].lowBound = (
                1 if variables[name].varValue == 1 else 0
            )
        status = self._prob.solve(self._solver)
        return status == LpStatusOptimal


def validate_pb_constraint(lp: MultiObjectiveLpProblem) -> LpConstraint:
    all_candidates: set[str] = set([
        variable.name
        for variable in lp.variables()
        if variable.name != "__dummy"
    ])

    pb_constraints = []
    for constraint in lp.constraints.values():
        candidates = set([variable.name for variable, _ in constraint.items()])
        if candidates == all_candidates and constraint.sense == LpConstraintLE:
            pb_constraints.append(constraint)

    if len(pb_constraints) == 0:
        raise PulpSolverError("Problem does not have PB constraint")
    if len(pb_constraints) > 1:
        raise PulpSolverError("Problem has too many PB constraint")
    return pb_constraints[0]


def validate_election_program(lp: MultiObjectiveLpProblem) -> None:
    """Reject programs outside the binary-PB shape every ElectionSolver assumes.

    See GH #36: no capability widening — this only rejects, it never
    implements the excluded features (continuous vars, arbitrary bounds,
    negative coefficients).
    """
    if not lp.objectives:
        raise PulpSolverError(f"Problem '{lp.name}' has no objectives")

    for variable in lp.variables():
        if variable.name == "__dummy":
            continue
        # pulp normalizes cat="Binary" -> cat="Integer" + lowBound=0/upBound=1
        # at LpVariable construction time; that's the only shape accepted here.
        if (
            variable.cat != "Integer"
            or variable.lowBound != 0
            or variable.upBound != 1
        ):
            raise PulpSolverError(
                f"Variable '{variable.name}' is not a 0/1 binary PB variable "
                f"(cat={variable.cat}, lowBound={variable.lowBound}, "
                f"upBound={variable.upBound})"
            )

    for voter in lp.objectives:
        for candidate, utility in voter.items():
            if utility < 0:
                raise PulpSolverError(
                    f"Objective '{voter.name}' has negative coefficient "
                    f"{utility} for variable '{candidate.name}'"
                )

    pb_constraint = validate_pb_constraint(lp)
    for candidate, cost in pb_constraint.items():
        if cost < 0:
            raise PulpSolverError(
                f"PB constraint '{pb_constraint.name}' has negative "
                f"coefficient {cost} for variable '{candidate.name}'"
            )


def molp_to_simple_election(lp: MultiObjectiveLpProblem) -> Election:
    approvals_utilities: dict[CandidateId, dict[VoterId, Utility]] = (
        defaultdict(dict)
    )

    voters: dict[VoterId, float] = {}
    for voter in (
        lp.objectives
    ):  # [T_6080: 80550 V_BO.D10.14_24 + 340000 V_BO.D10.1_24, ....]
        voters[voter.name] = lp.objectives_weights.get(voter.name, 1)  # pyright: ignore[reportCallIssue]  # pulp 3.3.2 LpElement.name Optional str
        for candidate, utility in voter.items():
            approvals_utilities[candidate.name][voter.name] = utility

    candidates = set([
        candidate.name
        for candidate in lp.variables()
        if candidate.name != "__dummy"
    ])

    pb_constraint = validate_pb_constraint(lp)
    candidates_costs: dict[str, float] = {
        candidate.name: coef for candidate, coef in pb_constraint.items()
    }

    if len(set(candidates).difference(set(candidates_costs.keys()))) != 0:
        raise Exception(
            "Candidates mismatch between variables and constraints"
        )

    return {
        "profile": approvals_utilities,
        "candidates": candidates_costs,
        "voters": voters,
    }
