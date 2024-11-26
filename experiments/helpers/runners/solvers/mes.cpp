// Author: Mateusz Słuszniak
#include <iostream>
#include <utility>
#include <vector>
#include <unordered_map>
#include <fstream>
#include <sstream>
#include <numeric>
#include <ctime>
#include <cmath>
#include <algorithm>

constexpr double infinity{__builtin_inf()};

std::vector<int> break_ties(const std::vector<double>& cost, const std::vector<std::vector<int>>& approvers, const std::vector<int>& choices){
    if(choices.size() == 1) return choices;
    std::vector<int> min_cost{};
    double curr_min{infinity};
    for(const auto elem : choices){
        if(cost[elem] < curr_min){
            curr_min = cost[elem];
            min_cost = std::vector<int>{elem};
        }
        else if(cost[elem] == curr_min)
            min_cost.push_back(elem);
    }

    std::vector<int> max_size{};
    size_t curr_max{0};
    for(const auto elem : min_cost){
        if(approvers[elem].size() > curr_max){
            curr_max = approvers[elem].size();
            max_size = std::vector<int>{elem};
        }
        else if(approvers[elem].size() == curr_max)
            max_size.push_back(elem);
    }
    return max_size;
}

std::vector<std::pair<int, double>> reverse_sort(const std::unordered_map<int, double>& map) {
    std::vector<std::pair<int, double>> A(map.begin(), map.end());
    sort(A.begin(), A.end(), [](const std::pair<int, double>& a, const std::pair<int, double>& b) {
        return a.second > b.second;
    });
    return A;
}

std::vector<int> equal_shares_fixed_budget(size_t N, const std::vector<int>& C, const std::vector<double>& cost,
                                           std::vector<std::vector<int>>& approvers, double B) {
    std::vector<double> budget(N, B / static_cast<double>(N));
    std::unordered_map<int, double> remaining;

    for (const auto c: C) {
        size_t approvers_size = approvers[c].size();
        if (cost[c] > 0 and approvers_size > 0)
            remaining[c] = static_cast<double>(approvers_size);
    }

    std::vector<int> winners{};
    while (true) {
        std::vector<int> best{};
        double best_eff_vote_count{0.0};
        const auto remaining_sorted{reverse_sort(remaining)};
        for (auto& [c, previous_vote_count]: remaining_sorted) {
            const double cost_c{cost[c]};
            if (previous_vote_count < best_eff_vote_count) {
                break;
            }
            double money_behind_now{0.0};
            for (const auto i: approvers[c]) {
                money_behind_now += budget[i];
            }
            if (money_behind_now < cost_c) {
                remaining.erase(c);
                continue;
            }
            std::sort(approvers[c].begin(), approvers[c].end(),
                      [&budget](int elem1, int elem2) { return budget[elem1] < budget[elem2];});
            double paid_so_far{0.0};
            size_t denominator{approvers[c].size()};
            for (const auto i: approvers[c]) {
                const double max_payment{(cost_c - paid_so_far) / static_cast<double>(denominator)};
                const double eff_vote_count{cost_c / max_payment};
                const double budget_i{budget[i]};
                if (max_payment > budget_i) {
                    paid_so_far += budget_i;
                    --denominator;
                } else {
                    remaining[c] = eff_vote_count;
                    if (eff_vote_count > best_eff_vote_count) {
                        best_eff_vote_count = eff_vote_count;
                        best = std::vector<int>{c};
                    }
                    else if(eff_vote_count == best_eff_vote_count){
                        best.push_back(c);
                    }
                    break;
                }
            }
        }
        if (best.empty())
            break;

        best = break_ties(cost, approvers, best);
        if (best.size() > 1) {
            std::cout << "Tie-breaking failed, candidates that have tie are:" << std::endl;
            for(const auto c : best)
                std::cout << c << " ";

            return std::vector<int>{};
        }

        const int best_candidate{best[0]};
        winners.push_back(best_candidate);
        remaining.erase(best_candidate);
        const double best_max_payment{cost[best_candidate] / best_eff_vote_count};
        for (const auto i: approvers[best_candidate]) {
            budget[i] -= std::min(best_max_payment, budget[i]);
        }
    }
    return winners;
}

std::vector<int> equal_shares(size_t N, const std::vector<int>& C, const std::vector<double>& cost,
                              std::vector<std::vector<int>>& approvers, double B) {
    auto mes{equal_shares_fixed_budget(N, C, cost, approvers, B)};
    // for exact version uncomment
    size_t budget{N * static_cast<size_t>(B / static_cast<double>(N))};
    double curr_cost{0.0};
    for (const auto c: mes) {
        curr_cost += cost[c];
    }
    // double B_scaled = B;
    while (true) {
        bool is_exhaustive{true};
        std::vector<int> taken(cost.size(), 0);
        for(const auto x : mes) taken[x]++;
        int j{0};
        for(size_t i{0}; i < taken.size(); ++i) {
            if (i == C[j]) {
                if (!taken[i] and curr_cost + cost[i] <= B) {
                    is_exhaustive = false;
                    break;
                }
                j++;
            }
        }
        if (is_exhaustive) {
            break;
        }
        // for exact version uncomment and comment B_scaled and pass next_budget to equal_shares_fixed_budget
        const size_t next_budget{budget + N};
        // B_scaled *= 1.01;
        auto next_mes{equal_shares_fixed_budget(N, C, cost, approvers, static_cast<double>(next_budget))};
        curr_cost = 0.0;
        for (const auto c: next_mes) {
            curr_cost += cost[c];
        }
        if (curr_cost <= B) {
            // for exact version uncomment
            budget = next_budget;
            mes = std::move(next_mes);
        } else {
            break;
        }
    }
    return mes;
}

int main() {
    // WARNING
    // Many lines describing project in Pabulib have ;; at the end, this causes inner getline to throw exception
    // Before running algorith make sure that the ; is actually a delimiter so replace ;; at the and with ;#;# or any valid sequence

    // path to file
    const std::string path{"path_to_pb_instance"};
    bool verbose{false};


    std::ifstream csvfile(path);
    if (!csvfile.is_open()) {
        std::cerr << "Error opening file: " << path << std::endl;
        return 1;
    }

    std::unordered_map<std::string, std::string> meta;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> projects;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> votes;
    std::string section{};
    std::vector<std::string> header{};

    std::string line{};
    while (std::getline(csvfile, line)) {
        std::istringstream iss(line);
        std::vector<std::string> row;
        std::string cell;

        while (std::getline(iss, cell, ';')) {
            row.push_back(cell);
        }

        if (row[0] == "META" || row[0] == "PROJECTS" || row[0] == "VOTES") {
            section = row[0];
            std::getline(csvfile, line);  // Read the header line
            std::istringstream header_iss(line);
            header.clear();

            while (std::getline(header_iss, cell, ';'))
                header.push_back(cell);

        } else if (section == "META") {
            meta[row[0]] = row[1];
        } else if (section == "PROJECTS") {
            projects[row[0]] = {};
            for (size_t i = 1; i < header.size(); ++i) {
                projects[row[0]][header[i]] = row[i];
            }
        } else if (section == "VOTES") {
            votes[row[0]] = {};
            for (size_t i = 1; i < header.size(); ++i) {
                votes[row[0]][header[i]] = row[i];
            }
        }
    }

    double budget{1.0 * stoi(meta["budget"])};
    const size_t num_voters{votes.size()};

    const size_t num_candidates{projects.size()};
    std::vector<int> candidates(num_candidates);
    iota(candidates.begin(), candidates.end(), 0);

    std::unordered_map<std::string, int> candidate_to_id;
    std::unordered_map<int, std::string> id_to_candidate;
    std::vector<double> cost(num_candidates);

    int index{0};
    for (auto& [project_name, content]: projects){
        candidate_to_id[project_name] = index;
        id_to_candidate[index] = project_name;
        cost[index++] = 1.0 * stoi(content["cost"]);
    }

    std::vector<std::vector<int>> approvers(num_candidates, std::vector<int>{});
    std::string segment;
    std::vector<std::string> seglist;

    index = 0;

    for (auto& [vote_id, content]: votes) {
        std::stringstream vs(content["vote"]);
        while(std::getline(vs, segment, ',')){
            approvers[candidate_to_id[segment]].push_back(index);
        }
        ++index;
    }

    std::vector<int> v(num_candidates), temp{};
    std::iota(v.begin(), v.end(), 0);

    // COMPUTING CLASSIC MES
    constexpr size_t number_of_measurements{10};

    std::vector<double> times{};
    std::vector<int> result;
    for(size_t i{0}; i < number_of_measurements; ++i) {
        clock_t begin = clock();
        result = equal_shares(num_voters, candidates, cost, approvers, budget);
        clock_t end = clock();
        times.push_back(static_cast<double>(end - begin) / CLOCKS_PER_SEC);
    }

    const double mean_time = std::accumulate(times.begin(), times.end(), 0.0) / number_of_measurements;
    double var{0};
    for(const auto time : times){
        var += (time - mean_time) * (time - mean_time);
    }
    var /= number_of_measurements;
    const double sd{sqrt(var)};
    std::cout << "C++: Mean Runtime = " << mean_time << "s, Standard Deviation = " << sd << "s\n";

    std::cout << "[";
    for(const auto i : result) std::cout << id_to_candidate[i] << ", ";
    std::cout << "\b\b";
    std::cout << "]";

    if(verbose) {
        std::cout << "META" << std::endl;
        for (auto& [key, val]: meta) std::cout << key << " " << val << std::endl;

        std::cout << "PROJECT" << std::endl;
        for (const auto& [project_name, content]: projects) {
            std::cout << project_name << std::endl;
            for (const auto& [param, val]: content) {
                std::cout << "    " << param << " " << val << std::endl;
            }
        }

        std::cout << "VOTES" << std::endl;
        for (const auto& [vote_id, content]: votes) {
            std::cout << "Vote id: " << vote_id << std::endl;
            for (const auto& [param, val]: content) {
                std::cout << "    " << param << " " << val << std::endl;
            }
        }
    }

    return 0;
}
