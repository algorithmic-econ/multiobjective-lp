import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.base_solvers.ElectionSolver import Election, ElectionSolver
from muoblpsolvers.types import CandidateId

logger = logging.getLogger(__name__)


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
            key=lambda candidate: total_utility[candidate]
            / candidates[candidate],
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
            if not lp.valid():
                candidate_variable.setInitialValue(0)

        logger.info("SOLVER END", extra={"time": (time.time() - start_time)})
