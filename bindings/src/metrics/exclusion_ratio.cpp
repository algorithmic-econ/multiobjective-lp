#include <stdexcept>

#include "metrics.hpp"

namespace metrics {

double exclusion_ratio(const SolvedInstance& instance) {
  const size_t n = instance.voters.size();
  if (n == 0) {
    throw std::invalid_argument(
        "Cannot compute exclusion ratio: no objectives");
  }
  // weighted, summed in voter order (bit-identical to python)
  double zero_weight = 0;
  for (const SolvedInstance::Voter& voter : instance.voters) {
    if (voter_value(instance, voter) == 0) {
      zero_weight += voter.weight;
    }
  }
  return zero_weight / instance.total_weight;
}

}  // namespace metrics
