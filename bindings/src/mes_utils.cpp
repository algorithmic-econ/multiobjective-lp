#include "methods.hpp"

#include <vector>
#include <unordered_map>
#include <algorithm>
#include <string>
#include <set>
#include <ranges>

using namespace std;

using VoterId = string;
using CandidateId = string;
using Utility = long long;
using Cost = double;

namespace {

CandidateId break_ties(const unordered_map<CandidateId, Cost>& cost,
                       const unordered_map<CandidateId, Utility>& total_utility,
                       vector<CandidateId> choices) {
    // COST
    double best_cost = cost.at(*ranges::min_element(choices, [&](const CandidateId& a, const CandidateId& b) {
        return cost.at(a) < cost.at(b);
    }));
    auto filtered_by_cost = choices | views::filter([&](const CandidateId& candidate) {
        return cost.at(candidate) == best_cost;
    });
    choices = vector<CandidateId>(filtered_by_cost.begin(), filtered_by_cost.end()); // Assign back to choices

    // UTILITY
    Utility best_utility = total_utility.at(*ranges::max_element(choices, [&](const CandidateId& a, const CandidateId& b) {
        return total_utility.at(a) < total_utility.at(b);
    }));
    auto filtered_by_utility = choices | views::filter([&](const CandidateId& candidate) {
        return total_utility.at(candidate) == best_utility;
    });
    choices = vector<CandidateId>(filtered_by_utility.begin(), filtered_by_utility.end()); // Assign back to choices

//    if (choices.size() > 1) {
//        string tie_failed_msg = "Tie-breaking failed: ";
//        for (const auto& candidate : choices) {
//            tie_failed_msg += candidate + " ";
//        }
//        throw runtime_error(tie_failed_msg);
//    }
    return choices[0];
}

}

vector<CandidateId> equal_shares_utils(
    const vector<VoterId>& voters,
    const vector<CandidateId>& projects,
    const unordered_map<CandidateId, Cost>& cost,
    const unordered_map<CandidateId, vector<pair<VoterId, Utility>>>& approvals_utilities,
    const unordered_map<CandidateId, Utility>& total_utility,
    double total_budget) {

    unordered_map<VoterId, double> budget;
    for (const auto& voter : voters) {
        budget[voter] = total_budget / voters.size();
    }

    unordered_map<CandidateId, Utility> remaining;
    for (const auto& candidate : projects) {
        if (cost.at(candidate) > 0 && !approvals_utilities.at(candidate).empty()) {
            remaining[candidate] = total_utility.at(candidate);
        }
    }

    vector<CandidateId> winners;
    while (!remaining.empty()) {
        vector<CandidateId> best_candidates;
        double best_eff_vote_count = 0.0;

        // Sort remaining candidates by decreasing previous effective vote count
        vector<CandidateId> remaining_sorted(remaining.size()); // Initialize with size
        transform(remaining.begin(), remaining.end(),
            remaining_sorted.begin(), [](const auto& candidate_utility) { return candidate_utility.first; }
            );
        sort(remaining_sorted.begin(), remaining_sorted.end(),
                  [&](const CandidateId& a, const CandidateId& b) { return remaining[a] > remaining[b]; }
                  );

        set<CandidateId> unaffordable_candidates;

        for (const auto& candidate : remaining_sorted) {
            double previous_eff_vote_count = remaining[candidate];
            if (previous_eff_vote_count < best_eff_vote_count) {
                // Cannot be better then the best so far
                break;
            }

            // Check if candidate is affordable
            double money_behind_now = 0.0;
            for (const auto& [voter, _] : approvals_utilities.at(candidate)) {
                money_behind_now += budget[voter];
            }
            if (money_behind_now < cost.at(candidate)) {
                unaffordable_candidates.insert(candidate);
                continue;
            }

            // Sort current approvers
            vector<pair<VoterId, Utility>> current_approvers_utilities = approvals_utilities.at(candidate);
            sort(current_approvers_utilities.begin(), current_approvers_utilities.end(),
                      [&](const auto& a, const auto& b) {
                          const auto& [voter_a, utility_a] = a;
                          const auto& [voter_b, utility_b] = b;
                          return (budget[voter_a] / utility_a) < (budget[voter_b] / utility_b);
                      });

            double paid_so_far = 0.0;
            double denominator = static_cast<double>(total_utility.at(candidate));

            for (const auto& [voter, utility] : current_approvers_utilities) {
                double payment_factor = (cost.at(candidate) - paid_so_far) / denominator;
                double eff_vote_count = cost.at(candidate) / payment_factor;

                if (payment_factor * utility > budget[voter]) {
                    paid_so_far += budget[voter];
                    denominator -= utility;
                } else {
                    remaining[candidate] = eff_vote_count;
                    if (eff_vote_count > best_eff_vote_count) {
                        best_eff_vote_count = eff_vote_count;
                        best_candidates = {candidate};
                    } else if (eff_vote_count == best_eff_vote_count) {
                        best_candidates.push_back(candidate);
                    }
                    break;
                }
            }
        }
        // Remove candidates that were marked for removal in this iteration
        for (const auto& candidate_to_remove : unaffordable_candidates) {
            remaining.erase(candidate_to_remove);
        }

        if (best_candidates.empty()) {
            break;
        }

        CandidateId selected_candidate = break_ties(cost, total_utility, best_candidates);
        winners.push_back(selected_candidate);
        remaining.erase(selected_candidate);

        // Charge approvers
        double best_max_payment = cost.at(selected_candidate) / best_eff_vote_count;
        for (const auto& [voter, utility] : approvals_utilities.at(selected_candidate)) {
            double payment = best_max_payment * utility;
            budget[voter] -= min(payment, budget[voter]);
        }
    }

    return winners;
}
