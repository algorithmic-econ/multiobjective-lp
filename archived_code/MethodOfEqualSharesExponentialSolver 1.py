# from typing import TypedDict
#
# from pulp import LpSolver
# # from muoblpbindings import equal_shares_utils
#
# from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
#
# from muoblpsolvers.common import (
#     prepare_mes_parameters, set_selected_candidates,
# )
# from muoblpsolvers.types import CandidateId, VoterId
#
#
# class SolverOptions(TypedDict):
#     budget_init: int
#
# 
# class MethodOfEqualSharesExponentialSolver(LpSolver):
#     """
#     Info:
#         Method Of Equal Shares Exponential variant solver
#     """
#
#     def __init__(self, solver_options):
#         super().__init__()
#         self.solver_options: SolverOptions = solver_options
#
#     def actualSolve(self, lp: MultiObjectiveLpProblem):
#         print(
#             f"Starting MethodOfEqualSharesExponentialSolver {self.solver_options}"
#         )
#         """
#         Parameters:
#             lp: Instance of MultiObjectiveLpProblem
#         """
#         projects, costs, voters, approvals_utilities, total_utilities, total_budget = (
#             prepare_mes_parameters(lp)
#         )
#
#         selected_global: list[CandidateId] = []
#         init_budget_per_voter = total_budget / len(voters)
#         budget_global: dict[VoterId, float] = {voter: init_budget_per_voter for voter in voters}
#         cost_global: float = 0
#         budget_modifier = 2
#
#         current_costs = costs.copy()
#         current_approvals_utilities = approvals_utilities.copy()
#         current_total_utilities = total_utilities.copy()
#
#         while len(current_approvals_utilities) > 0:
#             current_projects = list(current_approvals_utilities.keys())
#
#             # Run internal MES with fixed budget
#             print(f"Budget global before C++ call: {min(budget_global.values())} {sum(budget_global.values())} {max(budget_global.values())}")
#             selected_global, budget_global = equal_shares_utils_precomputed(
#                 voters, current_projects, current_costs, current_approvals_utilities, current_total_utilities,
#                 total_budget, budget_global, selected_global
#             )
#             print(f"Budget global after C++ call: {min(budget_global.values())} {sum(budget_global.values())} {max(budget_global.values())}")
#             print(f"Selected {len(selected_global)} projects")
#             cost_global = sum([costs[project] for project in selected_global])
#
#             # remove selected
#             for project in selected_global:
#                 if project in current_approvals_utilities:
#                     del current_approvals_utilities[project]
#                 if project in current_costs:
#                     del current_costs[project]
#                 if project in current_total_utilities:
#                     del current_total_utilities[project]
#
#             # remove infeasible
#             # TODO: move inside equal_shares
#             # TODO: How to deal with infeasible constraints - set variable = 1 , check feasilbity, if broken delete
#             infeasible_projects = [project for project in list(current_approvals_utilities.keys())
#                                    if project not in selected_global and cost_global + current_costs[project] > total_budget]
#
#             print(f"Removing {len(infeasible_projects)} infeasible projects")
#             for project in infeasible_projects:
#                 # Remove from all dictionaries to ensure consistency for the next iteration
#                 if project in current_approvals_utilities:
#                     del current_approvals_utilities[project]
#                 if project in current_costs:
#                     del current_costs[project]
#                 if project in current_total_utilities:
#                     del current_total_utilities[project]
#
#             # TODO: parametrize budget_init strategy
#             # increase voter budgets and keep remaining money from previous rounds
#             for voter in budget_global.keys():
#                 budget_global[voter] += (init_budget_per_voter * budget_modifier)
#             budget_modifier *= 2
#
#         set_selected_candidates(lp, selected_global)
