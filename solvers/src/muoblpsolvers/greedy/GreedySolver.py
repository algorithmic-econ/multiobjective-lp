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


def _find_feasible_seed(
    lp: MultiObjectiveLpProblem,
    candidates: dict[CandidateId, float],
) -> set[CandidateId]:
    new_vars = {n: LpVariable(n, cat="Binary") for n in candidates}
    prob = LpProblem("seed", LpMinimize)
    prob += lpSum(candidates[n] * new_vars[n] for n in candidates)
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
    if status != LpStatusOptimal:
        raise Exception(f"No feasible solution: status={status}")
    return {n for n in candidates if new_vars[n].value() == 1.0}


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

        pre_selected: set[CandidateId] = set()
        if any(c.sense == LpConstraintGE for c in lp.constraints.values()):
            pre_selected = _find_feasible_seed(lp, candidates)
            for name in pre_selected:
                lp.variablesDict()[name].setInitialValue(1)
            zero_utility_seed = pre_selected - set(total_utility)
            if zero_utility_seed:
                logger.info(
                    "SEED zero-utility",
                    extra={"candidates": zero_utility_seed},
                )

        for candidate in sorted_candidates:
            if candidate in pre_selected:
                continue
            candidate_variable = lp.variablesDict()[candidate]
            candidate_variable.setInitialValue(1)
            if not lp.valid():
                candidate_variable.setInitialValue(0)

        logger.info("SOLVER END", extra={"time": (time.time() - start_time)})
