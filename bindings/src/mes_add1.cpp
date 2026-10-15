#include "methods.hpp"

#include <vector>
#include <unordered_map>
#include <algorithm>
#include <numeric>
#include <string>

using namespace std;

using VoterId = string;
using CandidateId = string;
using Utility = long long;
using Cost = double;

vector<CandidateId> equal_shares_add1(
    const vector<VoterId>& voters,
    const vector<CandidateId>& projects,
    const unordered_map<CandidateId, Cost>& cost,
    const unordered_map<CandidateId, vector<pair<VoterId, Utility>>>& approvals_utilities,
    const unordered_map<CandidateId, Utility>& total_utility,
    double total_budget) {
    // Step 1: Start with a fixed budget method
    vector<CandidateId> mes = equal_shares_utils(voters, projects, cost, approvals_utilities, total_utility, total_budget);

    // Step 2: Initialize integral per-voter budget
    double budget = static_cast<int>(total_budget / voters.size()) * voters.size();
    double current_cost = accumulate(mes.begin(), mes.end(), 0.0,
                                      [&cost](double sum, const string& c) { return sum + cost.at(c); });

    // Step 3: Add projects while the budget allows
    while (true) {
        bool is_exhaustive = true;
        for (const auto& extra : projects) {
            if (find(mes.begin(), mes.end(), extra) == mes.end() && current_cost + cost.at(extra) <= total_budget) {
                is_exhaustive = false;
                break;
            }
        }

        // If exhaustive, stop
        if (is_exhaustive) {
            break;
        }

        // Try the next higher budget
        double next_budget = budget + voters.size();
        vector<string> next_mes = equal_shares_utils(voters, projects, cost, approvals_utilities, total_utility, next_budget);

        current_cost = accumulate(next_mes.begin(), next_mes.end(), 0.0,
                                  [&cost](double sum, const string& c) { return sum + cost.at(c); });
        if (current_cost <= total_budget) {
            // Update budget and project list if within budget
            budget = next_budget;
            mes = next_mes;
        } else {
            break;
        }
    }

    return mes;
}
