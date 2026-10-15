#include "solved_instance.hpp"

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

  return instance;
}

}  // namespace metrics
