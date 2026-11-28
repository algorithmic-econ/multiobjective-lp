#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "methods.hpp"
#include "metrics/metrics.hpp"
#include "metrics/solved_instance.hpp"
#include "phragmen.hpp"

#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

using NamedUtilities = std::vector<std::pair<std::string, double>>;
// pulp constraint: (sense, constant, [(variable name, coef)])
using NamedConstraint = std::tuple<int, double, NamedUtilities>;

constexpr int kSenseLE = -1;
constexpr int kSenseEQ = 0;

// Ordered (list) inputs: python profile / constraint item order drives
// tie-breaking and float summation order -> parity with phragmen.py.
std::pair<std::vector<std::string>, bool> phragmen_binding(
    const std::vector<std::pair<std::string, double>>& voters,
    const std::vector<std::pair<std::string, NamedUtilities>>& profile,
    const std::unordered_map<std::string, double>& costs,
    const std::vector<NamedConstraint>& constraints, bool increasing_scalings,
    double kappa, bool bos_version, double eps,
    std::optional<double> time_limit) {
  phragmen::Input input;
  std::unordered_map<std::string, phragmen::Index> voter_ids;
  for (const auto& [voter, weight] : voters) {
    if (!voter_ids.emplace(voter, input.weights.size()).second) {
      throw std::invalid_argument("Duplicate voter " + voter);
    }
    input.weights.push_back(weight);
  }

  std::unordered_map<std::string, phragmen::Index> candidate_ids;
  std::vector<std::string> candidate_names;
  for (const auto& [candidate, utilities] : profile) {
    if (!candidate_ids.emplace(candidate, candidate_names.size()).second) {
      throw std::invalid_argument("Duplicate candidate " + candidate);
    }
    candidate_names.push_back(candidate);
    input.costs.push_back(costs.at(candidate));
    auto& supporters = input.profile.emplace_back();
    for (const auto& [voter, utility] : utilities) {
      supporters.emplace_back(voter_ids.at(voter), utility);
    }
  }

  for (const auto& [sense, constant, items] : constraints) {
    if (sense != kSenseLE && sense != kSenseEQ) {
      throw std::invalid_argument(
          "Phragmen supports only <= and == constraints");
    }
    phragmen::Constraint& constraint = input.constraints.emplace_back();
    constraint.equality = sense == kSenseEQ;
    constraint.constant = constant;
    for (const auto& [name, coef] : items) {
      // non-profile variables are never selected (value 0): skip
      if (auto it = candidate_ids.find(name); it != candidate_ids.end()) {
        constraint.items.emplace_back(it->second, coef);
      }
    }
  }

  phragmen::Options options{increasing_scalings, kappa, bos_version, eps,
                            time_limit};
  phragmen::Result result;
  {
    py::gil_scoped_release release;
    result = phragmen::solve(input, options);
  }

  std::vector<std::string> rank;
  rank.reserve(result.rank.size());
  for (const phragmen::Index c : result.rank) {
    rank.push_back(candidate_names[c]);
  }
  return {rank, result.timed_out};
}

}  // namespace

PYBIND11_MODULE(muoblpbindings, m) {
  m.def("equal_shares_add1", &equal_shares_add1);
  m.def("equal_shares_utils", &equal_shares_utils);
  m.def("expanding_approvals", &expanding_approvals);
  m.def("single_transferable_vote", &single_transferable_vote);
  m.def("solid_coalition_refinement", &solid_coalition_refinement);
  m.def("phragmen", &phragmen_binding, py::arg("voters"), py::arg("profile"),
        py::arg("costs"), py::arg("constraints"), py::kw_only(),
        py::arg("increasing_scalings") = false, py::arg("kappa") = 1.0,
        py::arg("bos_version") = false, py::arg("eps") = 1e-6,
        py::arg("time_limit") = py::none());

  py::module_ metrics_module =
      m.def_submodule("metrics", "Native metrics over solved instances");
  py::class_<metrics::SolvedInstance>(metrics_module, "SolvedInstance")
      .def(py::init(&metrics::SolvedInstance::from_MuoblpProblem))
      .def_property_readonly(
          "num_voters",
          [](const metrics::SolvedInstance& inst) {
            return inst.voters.size();
          })
      .def_property_readonly("num_candidates",
                             [](const metrics::SolvedInstance& inst) {
                               return inst.candidate_names.size();
                             })
      .def_property_readonly("total_weight",
                             [](const metrics::SolvedInstance& inst) {
                               return inst.total_weight;
                             });
  metrics_module.def("exclusion_ratio",
                     [](const metrics::SolvedInstance& inst) {
                       py::gil_scoped_release release;
                       return metrics::exclusion_ratio(inst);
                     });
  metrics_module.def(
      "ejr_plus",
      [](const metrics::SolvedInstance& inst, bool up_to_one) {
        py::gil_scoped_release release;
        return metrics::ejr_plus(inst, up_to_one);
      },
      py::arg("instance"), py::arg("up_to_one") = true);
}
