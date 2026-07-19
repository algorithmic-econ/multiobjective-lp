import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusNotSolved, LpStatusOptimal

from muoblpsolvers.election_solver import (
    Election,
    ElectionSolver,
    FeasibilityChecker,
)
from muoblpsolvers.types import CandidateId
from muoblpsolvers.utils import set_solved

logger = logging.getLogger(__name__)


class GreedySolver(ElectionSolver):
    name = "Greedy"

    def _solve_election(
        self,
        lp: MultiObjectiveLpProblem,
        election: Election,
        **kwargs,
    ):
        candidates = election["candidates"]
        voters = election["voters"]
        profile = election["profile"]

        if self.msg:
            logger.info(
                "SOLVER START",
                extra={"candidates": len(candidates), "voters": len(voters)},
            )

        total_utility: dict[CandidateId, float] = {}
        for candidate, votes in profile.items():
            total_utility[candidate] = sum(
                voters[v] * u for v, u in votes.items()
            )

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

        deadline = (
            time.monotonic() + self.timeLimit
            if self.timeLimit is not None
            else None
        )
        checker = FeasibilityChecker(lp)
        status = LpStatusOptimal
        selected: list[str] = []
        for candidate in sorted_candidates:
            if deadline is not None and time.monotonic() > deadline:
                status = LpStatusNotSolved
                break
            candidate_variable = lp.variablesDict()[candidate]
            candidate_variable.setInitialValue(1)
            if not checker.check():
                candidate_variable.setInitialValue(0)
                if self.msg:
                    logger.debug("removed %s: infeasible", candidate)
            else:
                selected.append(candidate)
                if self.msg:
                    logger.debug("elected %s", candidate)

        if self.msg:
            logger.info("SOLVER END", extra={"selected": len(selected)})

        set_solved(lp, selected, status)
        return lp.status
