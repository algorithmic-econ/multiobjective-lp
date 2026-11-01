#include <algorithm>
#include <format>
#include <numeric>
#include <stdexcept>

#include "metrics.hpp"

namespace metrics {

size_t ejr_plus(const SolvedInstance& instance, bool up_to_one) {
  if (!instance.total_budget.has_value()) {
    throw std::invalid_argument(instance.budget_error);
  }
  const double budget = *instance.total_budget;
  const size_t n = instance.voters.size();

  std::vector<double> satisfaction(n);
  for (size_t i = 0; i < n; i++) {
    satisfaction[i] = voter_value(instance, instance.voters[i]);
  }
  std::vector<VoterId> order(n);
  std::iota(order.begin(), order.end(), 0);
  std::stable_sort(order.begin(), order.end(), [&](VoterId a, VoterId b) {
    return satisfaction[a] < satisfaction[b];
  });

  // approvers[c] = satisfactions of voters with c in their objective,
  // ascending (filled in sorted voter order)
  std::vector<std::vector<double>> approvers(instance.num_problem_candidates);
  for (VoterId v : order) {
    for (const SolvedInstance::Term& term : instance.voters[v].terms) {
      if (term.candidate < instance.num_problem_candidates) {
        approvers[term.candidate].push_back(satisfaction[v]);
      }
    }
  }

  size_t failures = 0;
  for (CandidateId c = 0; c < instance.num_problem_candidates; c++) {
    if (instance.candidate_values[c] == 1 || approvers[c].empty()) {
      continue;
    }
    double cost = 0;
    if (up_to_one) {
      if (!instance.candidate_costs[c].has_value()) {
        throw std::invalid_argument(std::format(
            "Candidate {} has no cost (in no constraint)",
            instance.candidate_names[c]));
      }
      cost = *instance.candidate_costs[c];
    }
    for (size_t k = 1; k <= approvers[c].size(); k++) {
      const double threshold =
          (static_cast<double>(k) / static_cast<double>(n)) * budget - cost;
      if (!(approvers[c][k - 1] >= threshold)) {
        failures++;
        break;
      }
    }
  }
  return failures;
}

}  // namespace metrics
