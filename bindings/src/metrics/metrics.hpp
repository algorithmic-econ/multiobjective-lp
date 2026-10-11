#pragma once

#include "solved_instance.hpp"

namespace metrics {

// Fraction of voters whose objective value (constant + sum of
// varValue * coef, accumulated in pulp dict order) is exactly zero.
// Pybind-free: safe to call with the GIL released.
double exclusion_ratio(const SolvedInstance& instance);

}  // namespace metrics
