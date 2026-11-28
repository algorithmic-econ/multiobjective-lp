// 1:1 port of solvers muoblpsolvers/phragmen.py::phragmen_cardinal.
// Bit parity with python: same operation order, left-to-right sums in python
// iteration order, stable sorts, compiled with -ffp-contract=off (no FMA).
// std::max(a, b) / std::min(a, b) pick the same operand as python max/min.

#include "phragmen.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>

namespace phragmen {

namespace {

using Clock = std::chrono::steady_clock;
constexpr double kInf = std::numeric_limits<double>::infinity();
// compute_local_cap default eps; python never passes the solver eps there
constexpr double kCapEps = 1e-6;
constexpr double kTimestampStep = 1;

struct SortedUtil {
  Index voter;
  double utility;
  size_t pos;  // position in candidate's supporters (profile order)
};

struct Candidate {
  Index id;  // index into Input (profile order)
  double cost;
  std::vector<std::pair<Index, double>> supporters;  // eps-filtered
  std::vector<SortedUtil> sorted_utils;              // ascending utility
};

// python max(x, 0)
inline double positive_part(double x) { return std::max(x, 0.0); }

// python round(x, 5) > 0: the double 5e-6 lies above the real 0.000005
inline bool round5_positive(double x) { return x >= 5e-6; }

double compute_local_cap(double timestamp, double m_spent, double ut,
                         double local_scaling, double kappa) {
  const double money = positive_part(timestamp - m_spent);
  const double high_cap = 2 * money * ut / (ut + std::max(ut, local_scaling));
  const double low_cap =
      (1 + kCapEps) * money * ut / std::max(ut, local_scaling);
  return kappa * high_cap + (1 - kappa) * low_cap;
}

void update_local_scalings(std::vector<double>& local_scalings,
                           const std::vector<size_t>& remaining,
                           double timestamp,
                           const std::vector<double>& m_spent,
                           const std::vector<Candidate>& candidates,
                           const std::vector<double>& weights) {
  for (const size_t k : remaining) {
    const Candidate& candidate = candidates[k];
    double scaling_for_c = 0;
    double sum_money = 0;
    for (const SortedUtil& su : candidate.sorted_utils) {
      sum_money +=
          weights[su.voter] * positive_part(timestamp - m_spent[su.voter]);
    }
    for (const SortedUtil& su : candidate.sorted_utils) {
      const double alpha = sum_money / candidate.cost;
      scaling_for_c = std::max(alpha * su.utility, scaling_for_c);
      local_scalings[su.voter] =
          std::max(local_scalings[su.voter], scaling_for_c);
      sum_money -=
          weights[su.voter] * positive_part(timestamp - m_spent[su.voter]);
    }
  }
}

// Fill caps for every remaining candidate at `timestamp`; true iff some
// candidate is affordable (sum of caps >= cost * (1 - eps)).
bool compute_caps(std::vector<std::vector<double>>& caps,
                  const std::vector<size_t>& remaining, double timestamp,
                  const std::vector<double>& m_spent,
                  const std::vector<double>& local_scalings,
                  const std::vector<Candidate>& candidates,
                  const std::vector<double>& weights, double kappa,
                  double eps) {
  bool select_candidate = false;
  for (const size_t k : remaining) {
    const Candidate& candidate = candidates[k];
    for (const SortedUtil& su : candidate.sorted_utils) {
      caps[k][su.pos] =
          weights[su.voter] *
          compute_local_cap(timestamp, m_spent[su.voter], su.utility,
                            local_scalings[su.voter], kappa);
    }
    double total_caps = 0;
    for (const double cap : caps[k]) {
      total_caps += cap;
    }
    if (total_caps >= candidate.cost * (1 - eps)) {
      select_candidate = true;
    }
  }
  return select_candidate;
}

// Supporter positions sorted (stable) by cap / (w * u), as python `sorted`.
std::vector<size_t> sort_by_cap_ratio(const Candidate& candidate,
                                      const std::vector<double>& caps,
                                      const std::vector<double>& weights) {
  const size_t s = candidate.supporters.size();
  std::vector<double> keys(s);
  for (size_t i = 0; i < s; i++) {
    const auto& [voter, utility] = candidate.supporters[i];
    keys[i] = caps[i] / (weights[voter] * utility);
  }
  std::vector<size_t> order(s);
  std::iota(order.begin(), order.end(), 0);
  std::ranges::stable_sort(
      order, [&](size_t a, size_t b) { return keys[a] < keys[b]; });
  return order;
}

double weighted_utility(const Candidate& candidate,
                        const std::vector<double>& weights) {
  double total = 0;
  for (const auto& [voter, utility] : candidate.supporters) {
    total += weights[voter] * utility;
  }
  return total;
}

class FeasibilityChecker {
 public:
  FeasibilityChecker(const std::vector<Constraint>& constraints, size_t m)
      : constraints_(constraints), selected_(m, false) {}

  // lp.valid() with `selected_` + `candidate` set to 1, rest 0
  bool check(Index candidate) const {
    for (const Constraint& constraint : constraints_) {
      double value = constraint.constant;
      for (const auto& [c, coef] : constraint.items) {
        if (selected_[c] || c == candidate) {
          value += coef;
        }
      }
      const bool valid =
          constraint.equality ? std::abs(value) <= 0 : value <= 0;
      if (!valid) {
        return false;
      }
    }
    return true;
  }

  void select(Index candidate) { selected_[candidate] = true; }

 private:
  const std::vector<Constraint>& constraints_;
  std::vector<bool> selected_;
};

}  // namespace

Result solve(const Input& input, const Options& options) {
  const auto start = Clock::now();
  const auto deadline_passed = [&]() {
    return options.time_limit.has_value() &&
           std::chrono::duration<double>(Clock::now() - start).count() >
               *options.time_limit;
  };

  const double eps = options.eps;
  const double kappa = options.kappa;
  const std::vector<double>& weights = input.weights;
  const size_t n = weights.size();
  const size_t m = input.profile.size();
  FeasibilityChecker checker(input.constraints, m);

  // individually feasible candidates with non-negligible utility
  std::vector<Candidate> candidates;
  for (Index c = 0; c < m; c++) {
    if (!checker.check(c)) {
      continue;
    }
    Candidate candidate{c, input.costs[c], {}, {}};
    double total = 0;
    for (const auto& [voter, utility] : input.profile[c]) {
      if (utility > eps) {
        candidate.supporters.emplace_back(voter, utility);
        total += utility;
      }
    }
    if (total > eps) {
      for (size_t i = 0; i < candidate.supporters.size(); i++) {
        const auto& [voter, utility] = candidate.supporters[i];
        candidate.sorted_utils.push_back({voter, utility, i});
      }
      std::ranges::stable_sort(candidate.sorted_utils,
                               [](const SortedUtil& a, const SortedUtil& b) {
                                 return a.utility < b.utility;
                               });
      candidates.push_back(std::move(candidate));
    }
  }

  std::vector<double> money_spent(n, 0);
  double timestamp_low = 0;
  double timestamp_high = timestamp_low + kTimestampStep;
  Result result;

  std::vector<size_t> remaining(candidates.size());
  std::iota(remaining.begin(), remaining.end(), 0);

  std::vector<std::vector<double>> local_caps(candidates.size());
  for (size_t k = 0; k < candidates.size(); k++) {
    local_caps[k].assign(candidates[k].supporters.size(), 0);
  }
  std::vector<std::vector<double>> local_caps_tmp = local_caps;
  std::vector<double> global_scalings(n, 0);
  std::vector<double> local_scalings(n, 0);
  std::vector<double> local_scalings_tmp(n, 0);

  const auto reset_scalings = [&](std::vector<double>& scalings) {
    if (options.increasing_scalings) {
      scalings = global_scalings;
    } else {
      std::ranges::fill(scalings, 0.0);
    }
  };

  while (!remaining.empty()) {
    if (deadline_passed()) {
      break;
    }

    // doubling: smallest power-of-2 timestamp with an affordable candidate
    while (true) {
      reset_scalings(local_scalings);
      update_local_scalings(local_scalings, remaining, timestamp_high,
                            money_spent, candidates, weights);
      if (compute_caps(local_caps, remaining, timestamp_high, money_spent,
                       local_scalings, candidates, weights, kappa, eps)) {
        break;
      }
      timestamp_high *= 2;
    }

    // bisection down to timestamp_step
    timestamp_low = timestamp_high / 2;
    while (timestamp_high > timestamp_low + kTimestampStep) {
      const double timestamp_med = (timestamp_low + timestamp_high) / 2;
      reset_scalings(local_scalings_tmp);
      update_local_scalings(local_scalings_tmp, remaining, timestamp_med,
                            money_spent, candidates, weights);
      if (compute_caps(local_caps_tmp, remaining, timestamp_med, money_spent,
                       local_scalings_tmp, candidates, weights, kappa, eps)) {
        timestamp_high = timestamp_med;
        for (const size_t k : remaining) {
          local_caps[k] = local_caps_tmp[k];
        }
        local_scalings = local_scalings_tmp;
      } else {
        timestamp_low = timestamp_med;
      }
    }

    double lowest_rho = kInf;
    double lowest_ratio = kInf;
    double best_alpha = 0;
    double best_util = 0;
    std::optional<size_t> next_candidate;

    for (const size_t k : remaining) {
      const Candidate& candidate = candidates[k];
      const std::vector<double>& caps = local_caps[k];
      if (options.bos_version) {
        const std::vector<size_t> supporters_sorted =
            sort_by_cap_ratio(candidate, caps, weights);
        const double candidate_utility = weighted_utility(candidate, weights);
        double total_utility = candidate_utility;
        double money_used = 0;
        double last_rho = 0;
        double new_ratio = kInf;
        double new_rho = kInf;
        double new_alpha = 0;
        for (const size_t i : supporters_sorted) {
          const auto& [voter, utility] = candidate.supporters[i];
          const double alpha = std::min(
              1.0, (money_used +
                    total_utility * (caps[i] / (weights[voter] * utility))) /
                       candidate.cost);
          if (round5_positive(alpha) && round5_positive(total_utility)) {
            const double rho = ((alpha * candidate.cost) - money_used) /
                               (alpha * total_utility);
            if (rho < last_rho) {
              break;
            }
            if (rho / alpha < new_ratio) {
              new_ratio = rho / alpha;
              new_rho = rho;
              new_alpha = alpha;
            }
          }
          total_utility -= weights[voter] * utility;
          money_used += caps[i];
          last_rho = caps[i] / (weights[voter] * utility);
        }
        if (new_ratio == kInf) {
          continue;  // no rho found: unaffordable at this timestamp
        }
        // ties on ratio -> higher total weighted utility
        if (new_ratio < lowest_ratio ||
            (new_ratio == lowest_ratio && candidate_utility > best_util)) {
          lowest_ratio = new_ratio;
          lowest_rho = new_rho;
          next_candidate = k;
          best_alpha = new_alpha;
          best_util = candidate_utility;
        }
      } else {
        double total_caps = 0;
        for (const double cap : caps) {
          total_caps += cap;
        }
        if (!(total_caps >= candidate.cost * (1 - eps))) {
          continue;
        }
        const std::vector<size_t> supporters_sorted =
            sort_by_cap_ratio(candidate, caps, weights);
        double price = candidate.cost;
        double total_utility = weighted_utility(candidate, weights);
        for (const size_t i : supporters_sorted) {
          const auto& [voter, utility] = candidate.supporters[i];
          if (caps[i] * total_utility >= price * weights[voter] * utility) {
            break;
          }
          price -= caps[i];
          total_utility -= weights[voter] * utility;
        }
        double rho;
        if (price > eps && total_utility > eps) {
          rho = price / total_utility;
        } else {
          const size_t last = supporters_sorted.back();
          const auto& [voter, utility] = candidate.supporters[last];
          rho = caps[last] / (weights[voter] * utility);
        }
        if (rho < lowest_rho) {
          next_candidate = k;
          lowest_rho = rho;
        }
      }
    }

    if (!next_candidate.has_value()) {
      throw std::runtime_error("Phragmen: no candidate selected");
    }
    const size_t next = *next_candidate;
    const Candidate& selected = candidates[next];
    result.rank.push_back(selected.id);
    checker.select(selected.id);

    std::erase(remaining, next);
    std::erase_if(remaining, [&](size_t k) {
      return !checker.check(candidates[k].id);
    });

    if (options.increasing_scalings) {
      for (size_t v = 0; v < n; v++) {
        global_scalings[v] = std::max(global_scalings[v], local_scalings[v]);
      }
    }

    const std::vector<double>& caps = local_caps[next];
    double total_overspending = 0;
    double total_utility = 1;
    if (options.bos_version) {
      total_overspending = selected.cost * (1.0 - best_alpha);
      total_utility = weighted_utility(selected, weights);
    }
    for (size_t i = 0; i < selected.supporters.size(); i++) {
      const auto& [voter, utility] = selected.supporters[i];
      const double per_indiv_cap = caps[i] / weights[voter];
      double payment = std::min(lowest_rho * utility, per_indiv_cap);
      if (options.bos_version) {
        payment += (total_overspending * utility) / total_utility;
      }
      if (payment > eps) {
        money_spent[voter] += payment;
      }
    }
  }

  result.timed_out = deadline_passed();
  return result;
}

}  // namespace phragmen
