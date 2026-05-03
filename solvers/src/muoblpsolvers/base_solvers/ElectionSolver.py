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
    lpSum,
)

from muoblpsolvers.types import CandidateId, Cost, Utility, VoterId

logger = logging.getLogger(__name__)


class Election(TypedDict):
    profile: dict[CandidateId, dict[VoterId, Utility]]
    candidates: dict[CandidateId, Cost]
    voters: dict[VoterId, int]


class ElectionSolver(LpSolver):
    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs):
        election = molp_to_simple_election(lp)

        self._solve_election(lp, election, kwargs=kwargs)

    @staticmethod
    def is_feasible(lp: MultiObjectiveLpProblem) -> bool:
        has_lowerbound_constraint = any(
            c.sense == LpConstraintGE for c in lp.constraints.values()
        )
        if not has_lowerbound_constraint:
            return lp.valid()

        candidates = [v.name for v in lp.variables() if v.name != "__dummy"]
        variables = lp.variablesDict()
        new_variables = {
            name: LpVariable(name, cat="Binary") for name in candidates
        }
        prob = LpProblem("feasibility", LpMinimize)
        prob += 0
        for candidate in candidates:
            if variables[candidate].varValue == 1:
                new_variables[candidate].lowBound = 1
        for name, constraint in lp.constraints.items():
            items = [
                (new_variables[v.name], coef)
                for v, coef in constraint.items()
                if v.name in new_variables
            ]
            if items:
                prob += LpConstraint(
                    lpSum(coef * v for v, coef in items),
                    sense=constraint.sense,
                    rhs=-constraint.constant,
                    name=name,
                )
        status = prob.solve(PULP_CBC_CMD(msg=False))
        return status == LpStatusOptimal

    def _solve_election(
        self, lp: MultiObjectiveLpProblem, election: Election, **kwargs
    ):
        raise NotImplementedError(
            "Subclasses must implement the solve_election method."
        )


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
        raise Exception("Problem does not have PB constraint")
    if len(pb_constraints) > 1:
        raise Exception("Problem has too many PB constraint")
    return pb_constraints[0]


def molp_to_simple_election(lp: MultiObjectiveLpProblem) -> Election:
    approvals_utilities: dict[CandidateId, dict[VoterId, Utility]] = (
        defaultdict(dict)
    )

    voters: dict[VoterId, int] = {}
    for voter in (
        lp.objectives
    ):  # [T_6080: 80550 V_BO.D10.14_24 + 340000 V_BO.D10.1_24, ....]
        voters[voter.name] = lp.objectives_weights.get(voter.name, 1)
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
