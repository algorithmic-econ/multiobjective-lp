from typing import TypedDict

from pulp import LpSolver

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

import logging

logger = logging.getLogger(__name__)


class Election(TypedDict):
    candidates: dict[str, int]
    voters: dict[str, list[str]]


class GreedySolver(LpSolver):
    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs):
        election: Election = kwargs["election"]
        logger.debug("Start solver")

        vote_counts: dict[str, int] = {}

        for candidate in election["candidates"].keys():
            vote_counts[candidate] = 0

        for approved in election["voters"].values():
            for candidate in approved:
                vote_counts[candidate] += 1

        results = list(vote_counts.items())
        results.sort(key=lambda t: t[1], reverse=True)
        results = [r for r in results if r[1] > 0]

        try:
            for candidate, _ in results:
                candidate_variable = lp.variablesDict()[candidate]
                candidate_variable.setInitialValue(1)
                if not lp.valid():
                    candidate_variable.setInitialValue(0)
        except Exception as err:
            logger.error("Boom", extra={"error": err})
            raise err
