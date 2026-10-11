#pragma once

#include <pybind11/pybind11.h>

#include <string>
#include <unordered_map>
#include <vector>

#include "../common.hpp"

namespace metrics {

// Snapshot of a solved MuoblpProblem for metric computation. Holds variable
// values (var.varValue) and sparse per-voter objectives in pulp dict order.
// Constraints, costs and weights are intentionally not extracted.
struct SolvedInstance {
  struct Term {
    CandidateId candidate;
    double coef;
  };
  struct Voter {
    double constant;
    std::vector<Term> terms;
  };

  std::vector<std::string> candidate_names;
  std::unordered_map<std::string, CandidateId> candidate_ids;
  std::vector<double> candidate_values;
  std::vector<Voter> voters;

  static SolvedInstance from_MuoblpProblem(py::object prob);
};

}  // namespace metrics
