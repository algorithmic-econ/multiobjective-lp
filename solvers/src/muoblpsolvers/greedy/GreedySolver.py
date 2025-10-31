import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.base_solvers.ElectionSolver import Election, ElectionSolver

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

        start_time = time.time()

        logger.info(
            "SOLVER START",
            extra={"candidates": len(candidates), "voters": len(voters)},
        )

        vote_counts: dict[str, int] = {}

        for candidate in candidates.keys():
            vote_counts[candidate] = 0

        for approved in voters.values():
            for candidate in approved:
                vote_counts[candidate] += 1

        sorted_candidates = list(vote_counts.items())
        sorted_candidates.sort(
            key=lambda cand_count: candidates[cand_count[0]] / cand_count[1],
        )
        sorted_candidates = [
            cand_count for cand_count in sorted_candidates if cand_count[1] > 0
        ]

        for candidate, _ in sorted_candidates:
            candidate_variable = lp.variablesDict()[candidate]
            candidate_variable.setInitialValue(1)
            if not lp.valid():
                candidate_variable.setInitialValue(0)

        logger.info("SOLVER END", extra={"time": (time.time() - start_time)})
