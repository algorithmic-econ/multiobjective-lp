#include <algorithm>
#include <format>
#include <numeric>
#include <ranges>

#include "common.hpp"
#include "methods.hpp"

namespace {

using SolidCoalition = std::pair<double, std::vector<CandidateId>>;

std::vector<SolidCoalition> get_all_coalitions(
    const std::vector<std::vector<CandidateId>>& rankings,
    const std::vector<double>& weights) {
  assert(rankings.size() == weights.size());
  std::vector<SolidCoalition> res;
  for (VoterId i = 0; i < rankings.size(); i++) {
    for (size_t r = 0; r < rankings[i].size(); r++) {
      std::unordered_set<CandidateId> candidates(rankings[i].begin(),
                                                 rankings[i].begin() + r + 1);
      double weight = 0;
      for (VoterId j = 0; j < rankings.size(); j++) {
        bool prefix_matches = true;
        for (size_t r2 = 0; r2 <= r; r2++) {
          if (!candidates.contains(rankings[j][r2])) {
            prefix_matches = false;
            break;
          }
        }
        if (prefix_matches) {
          if (j < i) {
            // This coalition has already been considered
            break;
          } else {
            weight += weights[j];
          }
        }
      }
      if (weight > 0) {
        std::vector<CandidateId> sorted_candidates(candidates.begin(),
                                                   candidates.end());
        std::ranges::sort(sorted_candidates);
        res.emplace_back(weight, std::move(sorted_candidates));
      }
    }
  }
  return res;
}

template <std::ranges::input_range R1, std::ranges::input_range R2>
size_t set_intersection_size(const R1& r1, const R2& r2) {
  auto i1 = std::ranges::begin(r1);
  auto i2 = std::ranges::begin(r2);
  auto e1 = std::ranges::end(r1);
  auto e2 = std::ranges::end(r2);

  size_t res = 0;
  while (i1 != e1 && i2 != e2) {
    if (*i1 < *i2) {
      ++i1;
    } else if (*i2 < *i1) {
      ++i2;
    } else {
      ++res;
      ++i1;
      ++i2;
    }
  }
  return res;
}

std::vector<CandidateId> solve(
    const std::vector<std::vector<CandidateId>>& rankings,
    const std::vector<double>& weights, const size_t committee_size,
    const size_t m) {
  const size_t n = rankings.size();
  assert(rankings.size() == weights.size());

  std::vector<SolidCoalition> coalitions =
      get_all_coalitions(rankings, weights);
  std::vector<CandidateId> committee;         // Maintains the insertion order
  std::vector<CandidateId> sorted_committee;  // For quicker intersections

  auto underrepresentation_value =
      [&sorted_committee](const SolidCoalition& coalition) {
        return coalition.first /
               (set_intersection_size(coalition.second, sorted_committee) + 1);
      };

  std::vector<CandidateId> all_candidates(m);
  std::iota(all_candidates.begin(), all_candidates.end(), 0);

  for (size_t k = 0; k < committee_size; k++) {
    std::vector<CandidateId> const* curr = &all_candidates;
    while (curr->size() - set_intersection_size(*curr, sorted_committee) > 1) {
      double best_value = 0;
      std::vector<CandidateId> const* best = nullptr;
      for (const SolidCoalition& coalition : coalitions) {
        if (coalition.second.size() >= curr->size() ||
            set_intersection_size(coalition.second, *curr) <
                coalition.second.size() ||
            set_intersection_size(coalition.second, sorted_committee) ==
                coalition.second.size()) {
          continue;
        }
        double value = underrepresentation_value(coalition);
        if (value > best_value) {
          best_value = value;
          best = &coalition.second;
        }
      }
      assert(best_value > 0);
      curr = best;
    }

    for (const CandidateId& c : *curr) {
      auto it = std::ranges::lower_bound(sorted_committee, c);
      if (it == sorted_committee.end() || *it != c) {
        sorted_committee.emplace(it, c);
        committee.emplace_back(c);
      }
    }
  }

  return committee;
}

}  // namespace

std::vector<std::string> solid_coalition_refinement(py::object prob) {
  Instance instance = Instance::from_MuoblpProblem(prob);

  for (size_t i = 0; i < instance.candidate_costs.size(); i++) {
    if (instance.candidate_costs[i] != 1) {
      throw std::invalid_argument(std::format(
          "All candidates are expected to have weight 1, but candidate {} has "
          "{}",
          instance.candidate_names[i], instance.candidate_costs[i]));
    }
  }

  const size_t m = instance.candidate_names.size();
  std::vector<CandidateId> committee =
      solve(get_rankings(instance.voters, m), instance.voter_weights,
            instance.budget, m);

  return instance.map_names(committee);
}
