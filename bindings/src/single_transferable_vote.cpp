#include <pybind11/pytypes.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <format>
#include <limits>
#include <numeric>
#include <stdexcept>

#include "common.hpp"
#include "methods.hpp"

namespace {

std::vector<CandidateId> solve(
    const std::vector<std::vector<CandidateId>>& rankings,
    const std::vector<double>& weights, const double quota, const size_t m) {
  const size_t n = rankings.size();
  assert(quota > 0);
  assert(rankings.size() == weights.size());

  std::vector<double> money_left(n, 0);
  std::vector<std::vector<CandidateId>> reversed_rankings(
      n, std::vector<CandidateId>{});
  std::vector<double> backing_money(m, 0);
  std::vector<std::vector<VoterId>> supporters(m, std::vector<VoterId>{});
  std::vector<bool> alive(m, true);
  uint32_t alive_count = m;
  std::vector<CandidateId> passing_quota;
  std::vector<CandidateId> committee;

  const auto approve_next = [&](VoterId i) {
    while (!reversed_rankings[i].empty() &&
           !alive.at(reversed_rankings[i].back())) {
      reversed_rankings[i].pop_back();
    }
    if (reversed_rankings[i].empty()) {
      return;
    }
    CandidateId c = reversed_rankings[i].back();
    if (backing_money[c] < quota && backing_money[c] + money_left[i] >= quota) {
      passing_quota.emplace_back(c);
    }
    backing_money[c] += money_left[i];
    supporters[c].emplace_back(i);
  };

  for (VoterId i = 0; i < n; i++) {
    money_left[i] = weights[i];
    reversed_rankings[i] =
        std::vector<CandidateId>(rankings[i].rbegin(), rankings[i].rend());
    approve_next(i);
  }

  while (alive_count > 0) {
    if (passing_quota.empty()) {
      CandidateId c =
          std::ranges::min_element(backing_money) - backing_money.begin();
      assert(alive.at(c));
      alive[c] = false;
      alive_count--;
      backing_money[c] = std::numeric_limits<double>::infinity();
      for (const VoterId& i : supporters[c]) {
        assert(!reversed_rankings[i].empty());
        approve_next(i);
      }
    } else {
      const CandidateId c = passing_quota.back();
      passing_quota.pop_back();
      assert(alive.at(c));

      committee.emplace_back(c);

      alive[c] = false;
      alive_count--;
      backing_money[c] = std::numeric_limits<double>::infinity();

      // Pay for the candidate
      double to_pay = quota;
      while (to_pay > 0) {
        assert(!supporters[c].empty());
        const VoterId i = supporters[c].back();
        if (to_pay < money_left[i]) {
          money_left[i] -= to_pay;
          to_pay = 0;
        } else {
          to_pay -= money_left[i];
          money_left[i] = 0;
          supporters[c].pop_back();
        }
      }

      // Pass the rest of supporters
      for (const VoterId& i : supporters[c]) {
        assert(!reversed_rankings[i].empty());
        approve_next(i);
      }

      supporters[c].clear();
    }
  }

  return committee;
}

}  // namespace

std::vector<std::string> single_transferable_vote(py::object prob) {
  Instance instance = Instance::from_MuoblpProblem(prob);

  for (size_t i = 0; i < instance.candidate_costs.size(); i++) {
    if (instance.candidate_costs[i] != 1) {
      throw std::invalid_argument(std::format(
          "All candidates are expected to have weight 1, but candidate {} has "
          "{}",
          instance.candidate_names[i], instance.candidate_costs[i]));
    }
  }

  double quota = std::accumulate(instance.voter_weights.begin(),
                                 instance.voter_weights.end(), 0.) /
                 instance.budget;

  const size_t m = instance.candidate_names.size();
  std::vector<CandidateId> committee =
      solve(get_rankings(instance.voters, m), instance.voter_weights, quota, m);

  return instance.map_names(committee);
}
