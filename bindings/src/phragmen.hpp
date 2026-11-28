#pragma once

// Pure core (no pybind / Python API inside: runs with GIL released).
// 1:1 port of solvers muoblpsolvers/phragmen.py::phragmen_cardinal.

#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace phragmen {

using Index = uint32_t;

// pulp LpConstraint: value = constant + sum(coef * x) over items (pulp
// order); LE valid iff value <= 0, EQ valid iff |value| <= 0 (lp.valid()).
struct Constraint {
  bool equality;
  double constant;
  std::vector<std::pair<Index, double>> items;  // (candidate, coef)
};

struct Input {
  std::vector<double> weights;  // per voter
  // per candidate, in python `election["profile"]` order
  std::vector<double> costs;
  std::vector<std::vector<std::pair<Index, double>>> profile;  // (voter, u)
  std::vector<Constraint> constraints;
};

struct Options {
  bool increasing_scalings = false;
  double kappa = 1.0;
  bool bos_version = false;
  double eps = 1e-6;
  std::optional<double> time_limit;  // seconds
};

struct Result {
  std::vector<Index> rank;  // candidate indices, selection order
  bool timed_out = false;
};

Result solve(const Input& input, const Options& options);

}  // namespace phragmen
