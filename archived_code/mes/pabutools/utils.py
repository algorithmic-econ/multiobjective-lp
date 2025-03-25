from pulp import LpConstraint
from typing import List, Dict, Callable, Set

from examples.mes.lp_election_model import AgentId
from examples.mes.pabutools.model import EnhancedProject, EnhancedProfile
from gmpy2 import mpq


def filter_projects(
    condition: Callable[[EnhancedProject], bool],
    projects: Dict[AgentId, EnhancedProject],
) -> List[AgentId]:
    return [p_id for p_id, project in projects.items() if condition(project)]


def by_district(district: str) -> Callable[[EnhancedProject], bool]:
    return lambda project: project.district == district


def by_category(category: str) -> Callable[[EnhancedProject], bool]:
    return lambda enhanced_project: category in enhanced_project.project.categories


def get_all_categories(projects: Dict[AgentId, EnhancedProject]) -> Set[str]:
    result = set()
    for enhanced_project in projects.values():
        result = result.union(enhanced_project.project.categories)
    return result


def merge_voter_preferences_by_district(
    profiles: Dict[str, EnhancedProfile],
) -> Dict[AgentId, List[AgentId]]:
    return {
        f"{voter.meta['voter_id']}_{district}": [str(c) for c in voter]
        for district, profile in profiles.items()
        for voter in profile.profile
    }


def get_candidates_ids_from_constraint(constraint: LpConstraint) -> List[AgentId]:
    # name is selected_candidate_{ID}
    return [candidate.name.split("_")[-1] for candidate in constraint.keys()]


def get_feasibility_ratio(constraint: LpConstraint) -> float:
    """

    :rtype: object
    """
    # ratio: [0, inf)
    value = constraint.value()
    target = constraint.constant
    return (value - target) / abs(target)


def get_modification_ratio(
    feasibility_ratio: float, smallest: float, largest: float
) -> float:
    # ratio: [smallest, largest + delta]
    delta = largest - smallest
    return smallest + delta * feasibility_ratio


def use_modified_price(enhanced_project: EnhancedProject) -> EnhancedProject:
    latest_price = enhanced_project.costs[-1]
    enhanced_project.project.cost = mpq(latest_price)
    return enhanced_project
