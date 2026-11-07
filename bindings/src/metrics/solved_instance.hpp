#pragma once

#include <pybind11/pybind11.h>

#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "../common.hpp"

namespace metrics {

// Snapshot of a solved MuoblpProblem for metric computation. Holds variable
// values (var.varValue), sparse per-voter objectives in pulp dict order,
// candidate costs and the PB budget. Weights are intentionally not extracted.
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

  // ids [0, num_problem_candidates) come from prob.variables(), the rest
  // appear in objectives only
  size_t num_problem_candidates = 0;
  // coef per candidate over all constraints, last write wins (mirrors the
  // python ejr_plus); nullopt = candidate in no constraint
  std::vector<std::optional<double>> candidate_costs;
  // abs(constant) of the unique PB constraint (LE over all candidates);
  // nullopt -> budget_error says why, raised only by metrics needing it
  std::optional<double> total_budget;
  std::string budget_error;

  static SolvedInstance from_MuoblpProblem(py::object prob);
};

}  // namespace metrics
