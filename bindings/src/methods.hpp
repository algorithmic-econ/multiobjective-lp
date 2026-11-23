#pragma once

#include <pybind11/pybind11.h>

#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace py = pybind11;

// MES: voters = id -> weight (weight-w voter == w identical voters, each
// with own budget B / sum(w)); total_utility = weighted sum per candidate.
std::vector<std::string> equal_shares_add1(
    const std::unordered_map<std::string, double>& voters,
    const std::vector<std::string>& projects,
    const std::unordered_map<std::string, double>& cost,
    const std::unordered_map<std::string,
                             std::vector<std::pair<std::string, long long>>>&
        approvers_utilities,
    const std::unordered_map<std::string, double>& total_utility,
    double total_budget);

std::vector<std::string> equal_shares_utils(
    const std::unordered_map<std::string, double>& voters,
    const std::vector<std::string>& projects,
    const std::unordered_map<std::string, double>& cost,
    const std::unordered_map<std::string,
                             std::vector<std::pair<std::string, long long>>>&
        approvers_utilities,
    const std::unordered_map<std::string, double>& total_utility,
    double total_budget);

std::vector<std::string> expanding_approvals(py::object lp_problem);

std::vector<std::string> single_transferable_vote(py::object lp_problem);

std::vector<std::string> solid_coalition_refinement(py::object lp_problem);
