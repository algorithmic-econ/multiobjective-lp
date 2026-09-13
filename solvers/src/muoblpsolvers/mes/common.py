import logging
from collections import defaultdict
from typing import cast

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpConstraint, LpConstraintLE, PulpSolverError

from muoblpsolvers.types import (
    CandidateId,
    Cost,
    TotalBudget,
    Utility,
    VoterId,
)

logger = logging.getLogger(__name__)


def get_total_budget_constraint(lp: MultiObjectiveLpProblem) -> LpConstraint:
    all_candidates: set[CandidateId] = {
        variable.name
        for variable in lp.variables()
        if variable.name != "__dummy"
    }

    pb_constraints = []
    for constraint in lp.constraints.values():
        candidates = {variable.name for variable in constraint}
        if candidates == all_candidates and constraint.sense == LpConstraintLE:
            pb_constraints.append(constraint)

    if len(pb_constraints) == 0:
        raise PulpSolverError("Problem does not have PB constraint")
    if len(pb_constraints) > 1:
        raise PulpSolverError("Problem has too many PB constraint")
    return pb_constraints[0]


def binding_utilities(
    approvals_utilities: dict[CandidateId, list[tuple[VoterId, Utility]]],
    total_utilities: dict[CandidateId, Utility],
) -> tuple[dict[str, list[tuple[str, int]]], dict[str, int]]:
    """Narrow utilities to the MES bindings' `int` signature (C++ long long).

    Type-only: utilities are ints at runtime (B6 int-utility invariant, core
    writer enforces it); pybind11 rejects floats, so no conversion here.
    """
    return (
        cast(dict[str, list[tuple[str, int]]], approvals_utilities),
        cast(dict[str, int], total_utilities),
    )


def prepare_mes_parameters(
    lp: MultiObjectiveLpProblem,
    msg: bool = True,
) -> tuple[
    list[CandidateId],
    dict[CandidateId, Cost],
    dict[VoterId, float],
    dict[CandidateId, list[tuple[VoterId, Utility]]],
    dict[CandidateId, Utility],
    TotalBudget,
]:
    projects: list[CandidateId] = [
        candidate.name
        for candidate in lp.variables()
        if candidate.name != "__dummy"
    ]

    costs: dict[CandidateId, Cost] = {
        candidate.name: cost
        # TODO: some constraints have repeated variables, but we just override them with the same value
        for constraint in lp.constraints.values()  # [C_ub_Bieńczyce: 25000 V_BO.D16.10_24 + 40500 V_BO.D16.11_24 <= 100000, ...]
        for candidate, cost in constraint.items()
    }

    # named: validate_election_program rejects unnamed objectives
    voter_ids: list[VoterId] = [
        cast(VoterId, voter.name) for voter in lp.objectives
    ]
    voters: dict[VoterId, float] = {
        voter_id: lp.objectives_weights.get(voter_id, 1)
        for voter_id in voter_ids
    }

    approvals_utilities: dict[CandidateId, list[tuple[VoterId, Utility]]] = (
        defaultdict(list)
    )
    for voter_id, voter in zip(
        voter_ids, lp.objectives
    ):  # [T_6080: 80550 V_BO.D10.14_24 + 340000 V_BO.D10.1_24, ....]
        for candidate, utility in voter.items():
            approvals_utilities[candidate.name] += [(voter_id, utility)]

    total_utilities: dict[CandidateId, Utility] = {
        candidate: sum(voters[v] * u for v, u in voters_utilities)
        for candidate, voters_utilities in approvals_utilities.items()
    }

    no_vote_projects = []
    for project in projects:
        if project not in approvals_utilities:
            no_vote_projects.append(project)

    for project in no_vote_projects:
        if msg:
            logger.info("Removing project with zero votes %s", project)
        projects.remove(project)
        del costs[project]

    total_budget = abs(get_total_budget_constraint(lp).constant)
    return (
        projects,
        costs,
        voters,
        approvals_utilities,
        total_utilities,
        total_budget,
    )
