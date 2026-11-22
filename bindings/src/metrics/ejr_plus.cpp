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
  const double total_weight = instance.total_weight;

  std::vector<double> satisfaction(n);
  for (size_t i = 0; i < n; i++) {
    satisfaction[i] = voter_value(instance, instance.voters[i]);
  }
  std::vector<VoterId> order(n);
  std::iota(order.begin(), order.end(), 0);
  std::stable_sort(order.begin(), order.end(), [&](VoterId a, VoterId b) {
    return satisfaction[a] < satisfaction[b];
  });

  // approvers[c] = (satisfaction, weight) of voters with c in their
  // objective, ascending satisfaction (filled in sorted voter order)
  struct Approver {
    double satisfaction;
    double weight;
  };
  std::vector<std::vector<Approver>> approvers(
      instance.num_problem_candidates);
  for (VoterId v : order) {
    for (const SolvedInstance::Term& term : instance.voters[v].terms) {
      if (term.candidate < instance.num_problem_candidates) {
        approvers[term.candidate].push_back(
            {satisfaction[v], instance.voters[v].weight});
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
    // weight w == w identical voters: checking only the largest coalition
    // (strictest threshold) is equivalent
    double coalition = 0;
    for (const Approver& approver : approvers[c]) {
      coalition += approver.weight;
      const double threshold = (coalition / total_weight) * budget - cost;
      if (!(approver.satisfaction >= threshold)) {
        failures++;
        break;
      }
    }
  }
  return failures;
}

}  // namespace metrics
