import logging
from collections import defaultdict
from typing import TypedDict

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpConstraint, LpConstraintLE, LpSolver

logger = logging.getLogger(__name__)


class Election(TypedDict):
    candidates: dict[str, int]
    voters: dict[str, list[str]]


class ElectionSolver(LpSolver):
    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs):
        election = molp_to_simple_election(lp)

        self._solve_election(lp, election, kwargs=kwargs)

    def _solve_election(
        self, lp: MultiObjectiveLpProblem, election: Election, **kwargs
    ):
        raise NotImplementedError(
            "Subclasses must implement the solve_election method."
        )


def validate_pb_constraint(lp: MultiObjectiveLpProblem) -> LpConstraint:
    all_candidates: set[str] = set(
        [
            variable.name
            for variable in lp.variables()
            if variable.name != "__dummy"
        ]
    )

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
    voters: dict[str, list[str]] = defaultdict(list)

    candidates: list[str] = [
        candidate.name
        for candidate in lp.variables()
        if candidate.name != "__dummy"
    ]

    pb_constraint = validate_pb_constraint(lp)
    candidates_coefs: dict[str, float] = {
        candidate.name: coef for candidate, coef in pb_constraint.items()
    }

    if len(set(candidates).difference(set(candidates_coefs.keys()))) != 0:
        raise Exception(
            "Candidates mismatch between variables and constraints"
        )

    for voter in lp.objectives:
        for candidate, _ in voter.items():
            voters[voter.name].append(candidate.name)

    return {"candidates": candidates_coefs, "voters": voters}
