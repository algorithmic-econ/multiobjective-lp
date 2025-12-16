import copy
import logging
import time
from typing import TypedDict

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpVariable

from muoblpsolvers.base_solvers.ElectionSolver import Election, ElectionSolver
from muoblpsolvers.common import set_selected_candidates
from muoblpsolvers.types import CandidateId, Cost, VoterId

logger = logging.getLogger(__name__)


class SolverOptions(TypedDict):
    increasing_scalings: bool
    kappa: float
    bos_version: bool
    eps: float


class PhragmenSolver(ElectionSolver):
    def __init__(self, solver_options):
        super().__init__()
        self.solver_options: SolverOptions = solver_options

    def _solve_election(
        self,
        lp: MultiObjectiveLpProblem,
        election: Election,
        **kwargs,
    ):
        start_time = time.time()
        logger.info(
            "SOLVER START",
            extra={"options": self.solver_options, "instance": lp.name},
        )
        selected = phragmen_cardinal(
            lp,
            election,
            increasing_scalings=self.solver_options.get(
                "increasing_scalings", False
            ),
            kappa=self.solver_options.get("kappa", 1.0),
            bos_version=self.solver_options.get("bos_version", False),
            eps=self.solver_options.get("eps", 1e-6),
        )
        set_selected_candidates(lp, selected)
        logger.info(
            "SOLVER END",
            extra={"time": (time.time() - start_time), "instance": lp.name},
        )


def update_local_scalings(
    local_scalings,
    remaining,
    timestamp,
    m_spent,
    sorted_utils,
    candidates: dict[CandidateId, Cost],
):
    for candidate in remaining:
        scaling_for_c = 0
        sum_money = sum(
            [(timestamp - m_spent[v]) for v, _ in sorted_utils[candidate]]
        )
        for voter, utility in sorted_utils[candidate]:
            alpha = sum_money / candidates[candidate]
            scaling_for_c = max(alpha * utility, scaling_for_c)
            local_scalings[voter] = max(local_scalings[voter], scaling_for_c)
            sum_money -= timestamp - m_spent[voter]


def compute_local_cap(timestamp, m_spent, ut, local_scaling, kappa, eps=1e-6):
    high_cap = (
        2 * max((timestamp - m_spent), 0) * ut / (ut + max(ut, local_scaling))
    )
    low_cap = (
        (1 + eps) * max((timestamp - m_spent), 0) * ut / max(ut, local_scaling)
    )

    return kappa * high_cap + (1 - kappa) * low_cap


def phragmen_cardinal(
    lp: MultiObjectiveLpProblem,
    election: Election,
    increasing_scalings=False,
    kappa=1.0,
    bos_version=False,
    eps=1e-6,
) -> set[str]:
    timestamp_step = 1

    profile: dict[CandidateId, dict[VoterId, float]] = {}
    variables: dict[CandidateId, LpVariable] = lp.variablesDict()
    for candidate, approvers_utilities in election["profile"].items():
        candidate_variable = variables[candidate]
        candidate_variable.setInitialValue(1)
        if not lp.valid():
            candidate_variable.setInitialValue(0)
            continue
        candidate_variable.setInitialValue(0)

        votes = {
            voter: utility
            for voter, utility in approvers_utilities.items()
            if utility > eps
        }
        if sum(votes.values()) > eps:
            profile[candidate] = votes

    sorted_utils = {
        candidate: sorted(
            [
                (voter, profile[candidate][voter])
                for voter in profile[candidate]
            ],
            key=lambda voter_utility: voter_utility[1],
        )
        for candidate in profile.keys()
    }

    money_spent = {voter: 0 for voter in election["voters"]}
    timestamp_low = 0
    timestamp_high = timestamp_low + timestamp_step
    rank = []
    remaining = set(
        [candidate for candidate in profile.keys() if candidate not in rank]
    )

    local_caps = {
        candidate: {voter: 0 for voter in profile[candidate].keys()}
        for candidate in profile.keys()
    }
    global_scalings = {voter: 0 for voter in election["voters"]}

    while remaining:
        select_candidate = False
        while not select_candidate:
            if increasing_scalings:
                local_scalings = {
                    v: global_scalings[v] for v in election["voters"]
                }
            else:
                local_scalings = {voter: 0 for voter in election["voters"]}
            update_local_scalings(
                local_scalings,
                remaining,
                timestamp_high,
                money_spent,
                sorted_utils,
                election["candidates"],
            )
            for candidate in remaining:
                for voter, utility in sorted_utils[candidate]:
                    local_caps[candidate][voter] = compute_local_cap(
                        timestamp=timestamp_high,
                        m_spent=money_spent[voter],
                        ut=utility,
                        local_scaling=local_scalings[voter],
                        kappa=kappa,
                    )
                if sum(local_caps[candidate].values()) >= election[
                    "candidates"
                ][candidate] * (1 - eps):
                    select_candidate = True
            if not select_candidate:
                timestamp_high *= 2

        timestamp_low = timestamp_high / 2
        local_caps_tmp = {
            candidate: {voter: 0 for voter in profile[candidate].keys()}
            for candidate in profile.keys()
        }

        while timestamp_high > timestamp_low + timestamp_step:
            timestemp_med = (timestamp_low + timestamp_high) / 2
            select_candidate = False
            if increasing_scalings:
                local_scalings_tmp = {
                    voter: global_scalings[voter]
                    for voter in election["voters"]
                }
            else:
                local_scalings_tmp = {voter: 0 for voter in election["voters"]}
            update_local_scalings(
                local_scalings_tmp,
                remaining,
                timestemp_med,
                money_spent,
                sorted_utils,
                election["candidates"],
            )
            for candidate in remaining:
                for voter, utility in sorted_utils[candidate]:
                    local_caps_tmp[candidate][voter] = compute_local_cap(
                        timestamp=timestemp_med,
                        m_spent=money_spent[voter],
                        ut=utility,
                        local_scaling=local_scalings_tmp[voter],
                        kappa=kappa,
                    )
                if sum(local_caps_tmp[candidate].values()) >= election[
                    "candidates"
                ][candidate] * (1 - eps):
                    select_candidate = True
            if select_candidate:
                timestamp_high = timestemp_med
                local_caps = copy.deepcopy(local_caps_tmp)
                local_scalings = local_scalings_tmp
            else:
                timestamp_low = timestemp_med

        lowest_rho = float("inf")
        lowest_ratio = float("inf")
        best_alpha = 0
        best_util = 0
        next_candidate = None

        for candidate in remaining:
            if bos_version:
                supporters_sorted = sorted(
                    list(election["profile"][candidate].keys()),
                    key=lambda voter: local_caps[candidate][voter]
                    / election["profile"][candidate][voter],
                )
                total_utility = sum(election["profile"][candidate].values())
                money_used = 0
                last_rho = 0
                new_ratio = float("inf")
                new_alpha = 0
                for voter in supporters_sorted:
                    alpha = min(
                        1.0,
                        (
                            money_used
                            + total_utility
                            * (
                                local_caps[candidate][voter]
                                / election["profile"][candidate][voter]
                            )
                        )
                        / election["candidates"][candidate],
                    )
                    if round(alpha, 5) > 0 and round(total_utility, 5) > 0:
                        rho = (
                            (alpha * election["candidates"][candidate])
                            - money_used
                        ) / (alpha * total_utility)
                        if rho < last_rho:
                            break
                        if rho / alpha < new_ratio:
                            new_ratio = rho / alpha
                            new_rho = rho
                            new_alpha = alpha
                    total_utility -= election["profile"][candidate][voter]
                    money_used += local_caps[candidate][voter]
                    last_rho = (
                        local_caps[candidate][voter]
                        / election["profile"][candidate][voter]
                    )
                if new_ratio < lowest_ratio:
                    lowest_ratio = new_ratio
                    lowest_rho = new_rho
                    next_candidate = candidate
                    best_alpha = new_alpha
                    # TODO: check best_util calculation
                    best_util = sum(election["profile"][candidate].values())
                elif new_ratio == lowest_ratio:
                    total_utility = sum(
                        election["profile"][candidate].values()
                    )
                    if total_utility > best_util:
                        next_candidate = candidate
                        best_util = total_utility
                        lowest_rho = new_rho
                        best_alpha = new_alpha
            elif sum(local_caps[candidate].values()) >= election["candidates"][
                candidate
            ] * (1 - eps):
                supporters_sorted = sorted(
                    profile[candidate],
                    key=lambda v: local_caps[candidate][v]
                    / profile[candidate][v],
                )
                price = election["candidates"][candidate]
                total_utility = sum(profile[candidate].values())
                for voter in supporters_sorted:
                    if (
                        local_caps[candidate][voter] * total_utility
                        >= price * profile[candidate][voter]
                    ):
                        break
                    price -= local_caps[candidate][voter]
                    total_utility -= profile[candidate][voter]
                if price > eps and total_utility > eps:
                    rho = price / total_utility
                else:
                    rho = (
                        local_caps[candidate][supporters_sorted[-1]]
                        / profile[candidate][supporters_sorted[-1]]
                    )
                if rho < lowest_rho:
                    next_candidate = candidate
                    lowest_rho = rho

        assert next_candidate is not None
        variables: dict[CandidateId, LpVariable] = lp.variablesDict()
        rank.append(next_candidate)
        variables[next_candidate].setInitialValue(1)
        remaining.remove(next_candidate)

        candidates_to_remove = []
        for candidate in remaining:
            candidate_variable = variables[candidate]
            candidate_variable.setInitialValue(1)
            if not lp.valid():
                candidates_to_remove.append(candidate)
            candidate_variable.setInitialValue(0)

        for candidate in candidates_to_remove:
            remaining.remove(candidate)

        if increasing_scalings:
            for voter in global_scalings.keys():
                global_scalings[voter] = max(
                    global_scalings[voter], local_scalings[voter]
                )
        if bos_version:
            total_overspending = election["candidates"][next_candidate] * (
                1.0 - best_alpha
            )
            total_utility = sum(profile[next_candidate].values())
            for voter in profile[next_candidate]:
                payment = (
                    min(
                        lowest_rho * profile[next_candidate][voter],
                        local_caps[next_candidate][voter],
                    )
                    + (total_overspending * profile[next_candidate][voter])
                    / total_utility
                )
                if payment > eps:
                    money_spent[voter] += payment
        else:
            for voter in profile[next_candidate]:
                payment = min(
                    lowest_rho * profile[next_candidate][voter],
                    local_caps[next_candidate][voter],
                )
            if payment > eps:
                money_spent[voter] += payment

    return rank
