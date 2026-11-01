#include "solved_instance.hpp"

#include <cmath>
#include <format>
#include <limits>
#include <stdexcept>

namespace metrics {

namespace {

CandidateId intern(SolvedInstance& instance, py::handle var,
                   const std::string& name) {
  auto it = instance.candidate_ids.find(name);
  if (it != instance.candidate_ids.end()) {
    return it->second;
  }
  py::object value = var.attr("varValue");
  if (value.is_none()) {
    throw std::invalid_argument(
        std::format("Variable {} has no value (varValue is None)", name));
  }
  if (instance.candidate_names.size() >=
      std::numeric_limits<CandidateId>::max()) {
    throw std::invalid_argument(
        std::format("Too many candidates. The maximum is {}",
                    std::numeric_limits<CandidateId>::max()));
  }
  const CandidateId id = instance.candidate_names.size();
  instance.candidate_names.emplace_back(name);
  instance.candidate_ids.emplace(name, id);
  instance.candidate_values.emplace_back(value.cast<double>());
  return id;
}

}  // namespace

SolvedInstance SolvedInstance::from_MuoblpProblem(py::object prob) {
  SolvedInstance instance;

  // Variables known to the problem (pulp skips objective-only variables)
  py::list vars = prob.attr("variables")();
  for (py::handle var : vars) {
    std::string name = var.attr("name").cast<std::string>();
    if (name == "__dummy") {
      // pulp injects __dummy while solving a problem without a scalar
      // objective; python-side validators skip it the same way
      continue;
    }
    intern(instance, var, name);
  }
  instance.num_problem_candidates = instance.candidate_names.size();

  // Voters; objective-only variables are interned on the fly
  py::list objectives = prob.attr("objectives");
  const size_t n = objectives.size();
  if (n > std::numeric_limits<VoterId>::max()) {
    throw std::invalid_argument(
        std::format("Too many voters. Got {} while the maximum is {}", n,
                    std::numeric_limits<VoterId>::max()));
  }
  instance.voters.resize(n);
  for (size_t i = 0; i < n; i++) {
    py::handle objective = objectives[i];
    SolvedInstance::Voter& voter = instance.voters[i];
    voter.constant = objective.attr("constant").cast<double>();
    py::dict terms = objective.cast<py::dict>();
    voter.terms.reserve(terms.size());
    for (const auto& item : terms) {
      py::handle var = item.first;
      std::string name = var.attr("name").cast<std::string>();
      const CandidateId id = intern(instance, var, name);
      voter.terms.push_back({id, item.second.cast<double>()});
    }
  }

  // Costs + PB constraint (mirrors validate_pb_constraint: sense LE and
  // variable set == prob.variables() without __dummy)
  py::dict constraints = prob.attr("constraints");
  size_t pb_count = 0;
  for (const auto& entry : constraints) {
    py::handle constraint = entry.second;
    std::vector<bool> covered(instance.num_problem_candidates, false);
    size_t covered_count = 0;
    bool only_problem_candidates = true;
    for (py::handle item : constraint.attr("items")()) {
      py::tuple pair = item.cast<py::tuple>();
      py::handle var = pair[0];
      std::string name = var.attr("name").cast<std::string>();
      const CandidateId id = intern(instance, var, name);
      if (id >= instance.candidate_costs.size()) {
        instance.candidate_costs.resize(id + 1);
      }
      instance.candidate_costs[id] = pair[1].cast<double>();
      if (id >= instance.num_problem_candidates) {
        only_problem_candidates = false;
      } else if (!covered[id]) {
        covered[id] = true;
        covered_count++;
      }
    }
    const bool is_le = constraint.attr("sense").cast<int>() == -1;
    if (is_le && only_problem_candidates &&
        covered_count == instance.num_problem_candidates) {
      pb_count++;
      instance.total_budget =
          std::abs(constraint.attr("constant").cast<double>());
    }
  }
  instance.candidate_costs.resize(instance.candidate_names.size());
  if (pb_count == 0) {
    instance.budget_error = "Problem does not have PB constraint";
  } else if (pb_count > 1) {
    instance.total_budget.reset();
    instance.budget_error = "Problem has too many PB constraint";
  }

  return instance;
}

}  // namespace metrics
