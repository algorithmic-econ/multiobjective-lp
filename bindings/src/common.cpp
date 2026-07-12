#include "common.hpp"

#include <format>
#include <stdexcept>

Instance Instance::from_MuoblpProblem(py::object prob) {
  Instance instance;

  // Create names->ids mapping
  py::list vars = prob.attr("variables")();
  const size_t m = vars.size();
  if (m > std::numeric_limits<CandidateId>::max()) {
    throw std::invalid_argument(
        std::format("Too many candidates. Got {} while the maximum is {}", m,
                    std::numeric_limits<CandidateId>::max()));
  }
  for (py::handle var : vars) {
    std::string name = var.attr("name").cast<std::string>();
    instance.candidate_names.emplace_back(name);
    auto cat = var.attr("cat").cast<std::string>();
    if (cat != "Integer") {
      py::print(
          std::format("Warning: variable {} is defined as {}, but "
                      "treated as integer instead",
                      name, cat));
    }
  }

  // Construct the reverse ids->names mapping
  for (size_t i = 0; i < m; i++) {
    instance.candidate_ids[instance.candidate_names[i]] = i;
  }

  // Extract budget
  py::dict constraints = prob.attr("constraints");
  if (constraints.size() != 1) {
    throw std::invalid_argument(
        std::format("Provided {} constraints, expected 1", constraints.size()));
  }
  py::object constraint =
      py::reinterpret_borrow<py::object>(constraints.begin()->second);
  instance.budget = -constraint.attr("constant").cast<Cost>();

  // Extract candidate consts
  instance.candidate_costs.resize(m, 0);
  for (const auto& item : constraint.cast<py::dict>()) {
    py::object var = py::reinterpret_borrow<py::object>(item.first);
    std::string name = var.attr("name").cast<std::string>();
    Cost cost = item.second.cast<Cost>();
    instance.candidate_costs[instance.candidate_ids[name]] = cost;
  }

  // Extract voters
  py::list objectives = prob.attr("objectives");
  py::dict objectives_weights = prob.attr("objectives_weights");
  const size_t n = objectives.size();
  if (n > std::numeric_limits<VoterId>::max()) {
    throw std::invalid_argument(
        std::format("Too many voters. Got {} while the maximum is {}", n,
                    std::numeric_limits<VoterId>::max()));
  }
  instance.voters.resize(n, std::vector<Utility>(m, 0));
  instance.voter_weights.resize(n, 1);
  for (size_t i = 0; i < n; i++) {
    py::handle objective = objectives[i];
    py::object voter_name = objective.attr("name");
    py::object weight = objectives_weights[voter_name];
    instance.voter_weights[i] = weight.cast<double>();
    for (const auto& item : objective.cast<py::dict>()) {
      py::object var = py::reinterpret_borrow<py::object>(item.first);
      std::string name = var.attr("name").cast<std::string>();
      const CandidateId candidate_id = instance.candidate_ids.at(name);
      instance.voters[i][candidate_id] = item.second.cast<Utility>();
    }
  }

  return instance;
}

std::vector<std::vector<CandidateId>> get_rankings(
    const std::vector<std::vector<Utility>>& utility, const size_t m) {
  if (utility.empty()) {
    return {};
  }
  std::vector<std::vector<CandidateId>> res(utility.size());
  for (size_t i = 0; i < utility.size(); i++) {
    std::vector<CandidateId>& ranking = res[i];
    for (CandidateId c = 0; c < m; c++) {
      if (utility[i][c] > 0) {
        ranking.emplace_back(c);
      }
    }
    std::ranges::sort(ranking, [&](CandidateId a, CandidateId b) {
      return utility[i][a] > utility[i][b];
    });
    for (CandidateId a = 0; a + 1 < ranking.size(); a++) {
      if (utility[i][ranking[a]] <= utility[i][ranking[a + 1]]) {
        throw std::invalid_argument(
            std::format("Objective {} does not create a strict ranking "
                        "(candidates {} and {} are tied with utility {})",
                        i, ranking[a], ranking[a + 1], utility[i][ranking[a]]));
      }
    }
  }
  return res;
}
