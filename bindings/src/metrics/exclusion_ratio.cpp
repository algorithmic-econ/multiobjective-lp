#include <stdexcept>

#include "metrics.hpp"

namespace metrics {

double exclusion_ratio(const SolvedInstance& instance) {
  const size_t n = instance.voters.size();
  if (n == 0) {
    throw std::invalid_argument(
        "Cannot compute exclusion ratio: no objectives");
  }
  size_t zero_count = 0;
  for (const SolvedInstance::Voter& voter : instance.voters) {
    double s = voter.constant;
    for (const SolvedInstance::Term& term : voter.terms) {
      s += instance.candidate_values[term.candidate] * term.coef;
    }
    if (s == 0) {
      zero_count++;
    }
  }
  return static_cast<double>(zero_count) / static_cast<double>(n);
}

}  // namespace metrics
