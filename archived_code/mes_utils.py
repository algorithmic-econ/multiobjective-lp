def break_ties(voters, projects, cost, approvers, choices):
    total_utility = {}
    for c in projects:
        total_utility[c] = sum([utility for voter_id, utility in approvers[c]])
    remaining = choices.copy()
    best_cost = min(cost[c] for c in remaining)
    remaining = [c for c in remaining if cost[c] == best_cost]
    best_count = max(total_utility[c] for c in remaining)
    remaining = [c for c in remaining if total_utility[c] == best_count]
    return remaining


def equal_shares_fixed_budget(
    voters: list[str],  # List[VoterId]
    projects: list[str],  # List[CandidateId]
    cost: dict[str, float],  # Dict[CandidateId, float]
    approvers: dict[
        str, list[tuple[str, float]]
    ],  # Dict[CandidateId, List[Tuple[VoterId,Utility(V,C)]]]
    total_budget: float,
):
    print("PYTHON MES UTILS")
    budget = {i: total_budget / len(voters) for i in voters}  # Dict[VoterId, float]
    remaining = {}  # remaining candidate -> previous effective vote count Dict[CandidateId, int]
    for c in projects:
        if cost[c] > 0 and len(approvers[c]) > 0:
            remaining[c] = sum([utility for voter_id, utility in approvers[c]])
    winners = []
    while True:
        best = []
        best_eff_vote_count = 0
        # go through remaining candidates in order of decreasing previous effective vote count
        remaining_sorted = sorted(remaining, key=lambda c: remaining[c], reverse=True)
        for c in remaining_sorted:
            previous_eff_vote_count = remaining[c]
            if previous_eff_vote_count < best_eff_vote_count:
                # c cannot be better than the best so far
                break
            money_behind_now = sum(budget[voter] for voter, _ in approvers[c])
            if money_behind_now < cost[c]:
                # c is not affordable
                del remaining[c]
                continue
            # calculate the effective vote count of c
            approvers[c].sort(
                key=lambda voter_utility: budget[voter_utility[0]] / voter_utility[1]
            )
            paid_so_far = 0
            denominator = remaining[c]  # total utility of c
            for voter, utility in approvers[c]:
                # compute payment if remaining approvers pay proportional to their utility
                max_payment = (cost[c] - paid_so_far) / denominator
                eff_vote_count = cost[c] / max_payment
                if max_payment * utility > budget[voter]:
                    # voter cannot afford the payment, so pays entire remaining budget
                    paid_so_far += budget[voter]
                    denominator -= utility
                else:
                    # i (and all later approvers) can afford the payment; stop here
                    remaining[c] = eff_vote_count
                    if eff_vote_count > best_eff_vote_count:
                        best_eff_vote_count = eff_vote_count
                        best = [c]
                    elif eff_vote_count == best_eff_vote_count:
                        best.append(c)
                    break
        if not best:
            # no remaining candidates are affordable
            break
        best = break_ties(voters, projects, cost, approvers, best)
        if len(best) > 1:
            raise Exception(
                f"Tie-breaking failed: tie between projects {best} could not be resolved. Another tie-breaking needs to be added."
            )
        best = best[0]
        winners.append(best)
        del remaining[best]
        # charge the approvers of best
        best_max_payment = cost[best] / best_eff_vote_count
        for voter, utility in approvers[best]:
            payment = best_max_payment * utility
            budget[voter] -= min(payment, budget[voter])

    return winners
