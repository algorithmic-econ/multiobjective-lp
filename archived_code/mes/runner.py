from examples.mes.lp_election_model import AgentId, LpElection
from examples.mes.pabutools.model import EnhancedProject, EnhancedProfile
from examples.mes.pabutools.parsing import load_pabulib_to_enhanced_projects_and_district_profiles
from examples.mes.pabutools.utils import use_modified_price, merge_voter_preferences_by_district, filter_projects, \
    by_district, by_category, get_feasibility_ratio, get_modification_ratio, get_candidates_ids_from_constraint
from pabutools.election import Instance, ApprovalProfile
from pabutools.rules import method_of_equal_shares
from pabutools.election.satisfaction import Cost_Sat
from typing import Tuple, List, Dict

from src.utils.logger import logger, LogKey, get_logs_from_stream
from src.utils.utils import flatten


def project_costs_interference(it: int, project: EnhancedProject) -> EnhancedProject:
    current_price_index = it + 1
    #
    # TODO: provide replacement_cost strategy as lambda
    #
    replacement_cost = sum(project.costs[current_price_index:]) / len(project.costs[current_price_index:])
    project.costs = project.costs[:current_price_index] + [replacement_cost]
    return project


def mes_wrapper(budget: int, _projects: List[EnhancedProject], _profiles: Dict[str, EnhancedProfile]) -> List[AgentId]:
    instance = Instance({use_modified_price(enhanced_project).project for enhanced_project in _projects}, budget)
    ballots = flatten([enhanced_profile.profile for _, enhanced_profile in _profiles.items()])
    # TODO: verify double usage of voter_id in citywide elections
    profile = ApprovalProfile(ballots)
    outcome = method_of_equal_shares(instance, profile, sat_class=Cost_Sat)
    return [_candidate.name for _candidate in outcome]


def run(max_iterations=10) -> Tuple[List[str], LpElection, Dict[AgentId, EnhancedProject]]:
    #
    # Load election from pabulib file
    #
    path = 'resources/warszawa_2023_test/'
    projects, profiles, budgets = load_pabulib_to_enhanced_projects_and_district_profiles(path)

    #
    # Create LpProblem, LpVariables, LpExpressions to represent election instance
    #
    election = LpElection(
        candidates=list(projects.keys()),
        voters_preferences=merge_voter_preferences_by_district(profiles)
    )

    #
    # Add constraints for all districts, e.g., LB: 75%
    #
    for district in profiles.keys():
        district_projects_costs = {p_id: int(projects[p_id].project.cost) for p_id in
                                   filter_projects(by_district(district), projects)}
        election.define_constraint_lb(district, district_projects_costs, int(budgets[district] * 0.8))
        election.define_constraint_ub(district, district_projects_costs, int(budgets[district] * 0.5))

    #
    # Add constraints for categories, e.g. 25% of total budget for education
    #
    education_projects_costs = {p_id: int(projects[p_id].project.cost) for p_id in
                                filter_projects(by_category('education'), projects)}
    election.define_constraint_lb('education', education_projects_costs, int(sum(budgets.values()) * 0.25))

    logger.info('============== start ==============')

    #
    # Run MES with price changes
    #
    iteration = 0
    selected_candidates: List[str] = []
    while iteration < max_iterations:
        # Run MES
        selected_candidates = mes_wrapper(sum(budgets.values()), list(projects.values()), profiles)
        election.set_selected_candidates_values(selected_candidates)

        # Check constraints
        infeasible = election.get_infeasible_constraints()

        for c in infeasible:
            logger.info(f"{LogKey.FEAS_RATIO.name}|{iteration}|{c.name}|{get_feasibility_ratio(c)}")

        if len(infeasible) == 0:
            logger.warn('============== all constraints fulfilled ==============')
            break

        # Modify prices
        for constraint in infeasible:
            feasibility_ratio = get_feasibility_ratio(constraint)  # ratio: [0, inf)
            cost_modification_ratio = get_modification_ratio(feasibility_ratio, 0.7, 1)
            affected_candidates = get_candidates_ids_from_constraint(constraint)
            for candidate in affected_candidates:
                try:
                    # use iteration as index if candidate is in multiple constraints
                    if len(projects[candidate].costs) < iteration:
                        # TODO: investigate hard to replicate (random) out of index error here
                        logger.error('boom')
                    previous_cost = projects[candidate].costs[iteration]
                    projects[candidate].costs.append(int(previous_cost * cost_modification_ratio))
                except:
                    logger.info(f"\n========crashed|{iteration}")
                    for p in projects.values():
                        logger.info(f"{LogKey.PROJECT.name}|{p.project.name}|{p.costs}")

        # Handle candidates modified by multiple constrains, for now, take avg of discounts
        for project in projects.values():
            if len(project.costs) > iteration + 2:
                project_costs_interference(iteration, project)

        iteration += 1

    return selected_candidates, election, projects


if __name__ == '__main__':
    sc, e, p = run(4)
    with open("output/latest.log", 'w', encoding="utf-8") as file:
        file.write(get_logs_from_stream())
    for project in p.values():
        logger.info(f"{LogKey.PROJECT.name}|{project.project.name}|{project.costs}")
