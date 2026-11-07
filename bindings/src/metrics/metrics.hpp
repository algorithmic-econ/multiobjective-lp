#pragma once

#include "solved_instance.hpp"

namespace metrics {

// Objective value of a voter: constant + sum of varValue * coef, accumulated
// in pulp dict order (same as LpAffineExpression.value() -> bit-identical)
inline double voter_value(const SolvedInstance& instance,
                          const SolvedInstance::Voter& voter) {
  double s = voter.constant;
  for (const SolvedInstance::Term& term : voter.terms) {
    s += instance.candidate_values[term.candidate] * term.coef;
  }
  return s;
}

// Fraction of voters whose objective value is exactly zero.
// Pybind-free: safe to call with the GIL released.
double exclusion_ratio(const SolvedInstance& instance);

// Number of unelected candidates (from prob.variables()) violating EJR+:
// walking approvers by ascending satisfaction, the k-th one has
// satisfaction < (k / n) * budget - (up_to_one ? cost : 0).
// Pybind-free: safe to call with the GIL released.
size_t ejr_plus(const SolvedInstance& instance, bool up_to_one);

}  // namespace metrics
