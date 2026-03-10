import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    PULP_CBC_CMD,
    LpConstraint,
    LpConstraintGE,
    LpMinimize,
    LpProblem,
    LpStatusOptimal,
    LpVariable,
    lpSum,
)

from muoblpsolvers.base_solvers.ElectionSolver import Election, ElectionSolver
from muoblpsolvers.types import CandidateId

logger = logging.getLogger(__name__)


def _is_feasible(
    lp: MultiObjectiveLpProblem,
    cand_cost: dict[CandidateId, float],
) -> bool:
    has_lowerbound_constraint = any(
        c.sense == LpConstraintGE for c in lp.constraints.values()
    )
    if not has_lowerbound_constraint:
        return lp.valid()

    var_dict = lp.variablesDict()
    new_vars = {n: LpVariable(n, cat="Binary") for n in cand_cost}
    prob = LpProblem("feasibility", LpMinimize)
    prob += 0
    for n in cand_cost:
        if var_dict[n].varValue == 1:
            new_vars[n].lowBound = 1
    for cname, c in lp.constraints.items():
        items = [
            (new_vars[v.name], coef)
            for v, coef in c.items()
            if v.name in new_vars
        ]
        if items:
            prob += LpConstraint(
                lpSum(coef * v for v, coef in items),
                sense=c.sense,
                rhs=-c.constant,
                name=cname,
            )
    status = prob.solve(PULP_CBC_CMD(msg=0))
    return status == LpStatusOptimal


class GreedySolver(ElectionSolver):
    def __init__(self):
        super().__init__()

    def _solve_election(
        self,
        lp: MultiObjectiveLpProblem,
        election: Election,
        **kwargs,
    ):
        candidates = election["candidates"]
        voters = election["voters"]
        profile = election["profile"]

        start_time = time.time()

        logger.info(
            "SOLVER START",
            extra={"candidates": len(candidates), "voters": len(voters)},
        )

        total_utility: dict[CandidateId, float] = {}
        for candidate, votes in profile.items():
            total_utility[candidate] = sum(votes.values())

        sorted_candidates = list(candidates.keys())
        sorted_candidates.sort(
            key=lambda candidate: (
                total_utility[candidate] / candidates[candidate]
            ),
            reverse=True,
        )
        sorted_candidates = [
            candidate
            for candidate in sorted_candidates
            if total_utility[candidate] > 0
        ]

        for candidate in sorted_candidates:
            candidate_variable = lp.variablesDict()[candidate]
            candidate_variable.setInitialValue(1)
            if not _is_feasible(lp, candidates):
                candidate_variable.setInitialValue(0)

        logger.info("SOLVER END", extra={"time": (time.time() - start_time)})
