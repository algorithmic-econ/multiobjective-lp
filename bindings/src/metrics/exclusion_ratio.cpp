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
    if (voter_value(instance, voter) == 0) {
      zero_count++;
    }
  }
  return static_cast<double>(zero_count) / static_cast<double>(n);
}

}  // namespace metrics
