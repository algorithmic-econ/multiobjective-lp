from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.types import CandidateId, VoterId

import logging

logger = logging.getLogger(__name__)


def break_ties(
    cost: dict[CandidateId, float],
    total_utility: dict[CandidateId, int],
    choices: list[CandidateId],
) -> CandidateId:
    remaining = choices.copy()
    best_cost = min(cost[c] for c in remaining)
    remaining = [c for c in remaining if cost[c] == best_cost]
    best_count = max(total_utility[c] for c in remaining)
    remaining = [c for c in remaining if total_utility[c] == best_count]
    if len(remaining) > 1:
        logger.warning(
            "Tie-breakign failed: tie between projects. Selecting first one.",
            extra={"remaining": remaining},
        )
    return remaining[0]


def equal_shares_exponential(
    voters: list[VoterId],
    projects: list[CandidateId],
    cost: dict[CandidateId, float],
    approvals_utilities: dict[CandidateId, list[tuple[VoterId, int]]],
    total_utility: dict[CandidateId, int],
    lp: MultiObjectiveLpProblem,
    budget_init: float,
):
    budget: dict[VoterId, float] = {voter: budget_init for voter in voters}
    remaining = {}  # remaining candidate -> previous effective vote count Dict[CandidateId, int]
    for candidate in projects:
        if cost[candidate] > 0 and len(approvals_utilities[candidate]) > 0:
            remaining[candidate] = total_utility[candidate]
    winners = []
    i = 0
    while len(remaining) and max(remaining.values()) > 0:
        i += 1
        budget_init *= 2
        try:
            for voter in voters:
                budget[voter] += budget_init
        except OverflowError:
            print(i)
            break

        while len(remaining):
            best: list[CandidateId] = []
            best_eff_vote_count = 0
            # go through remaining candidates in order of decreasing previous effective vote count
            remaining_sorted = sorted(
                remaining, key=lambda c: remaining[c], reverse=True
            )
            for candidate in remaining_sorted:
                previous_eff_vote_count = remaining[candidate]
                if previous_eff_vote_count < best_eff_vote_count:
                    # c cannot be better than the best so far
                    break
                money_behind_now = sum(
                    budget[voter]
                    for voter, _ in approvals_utilities[candidate]
                )
                if money_behind_now < cost[candidate]:
                    # c is not affordable in this round - try again after increasing budgets
                    # del remaining[c]
                    continue

                # calculate the effective vote count of c
                approvals_utilities[candidate].sort(
                    key=lambda voter_utility: budget[voter_utility[0]]
                    / voter_utility[1]
                )
                paid_so_far = 0
                denominator = remaining[candidate]  # total utility of c
                for voter, utility in approvals_utilities[candidate]:
                    # compute payment if remaining approvers pay proportional to their utility
                    max_payment = (cost[candidate] - paid_so_far) / denominator
                    eff_vote_count = cost[candidate] / max_payment
                    if max_payment * utility > budget[voter]:
                        # voter cannot afford the payment, so pays entire remaining budget
                        paid_so_far += budget[voter]
                        denominator -= utility
                    else:
                        # i (and all later approvers) can afford the payment; stop here
                        # TODO: make sure not to drop eff_vote_count below zero
                        remaining[candidate] = eff_vote_count
                        if eff_vote_count > best_eff_vote_count:
                            best_eff_vote_count = eff_vote_count
                            best = [candidate]
                        elif eff_vote_count == best_eff_vote_count:
                            best.append(candidate)
                        break
            if not best:
                # no remaining candidates are affordable
                break
            selected = break_ties(cost, total_utility, best)
            ### Try selecting best
            candidate_variable = [
                variable
                for variable in lp.variables()
                if variable.name == selected
            ][0]
            candidate_variable.setInitialValue(1)

            ### remove if selecting c breaks feasibility
            if not lp.valid():
                candidate_variable.setInitialValue(0)
                del remaining[selected]
                continue

            winners.append(selected)
            del remaining[selected]
            # charge the approvers of selected
            best_max_payment = cost[selected] / best_eff_vote_count
            for voter, utility in approvals_utilities[selected]:
                payment = best_max_payment * utility
                budget[voter] -= min(payment, budget[voter])

    return winners
