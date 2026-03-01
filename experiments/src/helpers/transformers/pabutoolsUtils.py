from typing import Dict, Tuple, TypeAlias, Callable, List
import os
from pabutools.election import Instance, Profile, parse_pabulib, Project

from helpers.runners.model import Utility

District: TypeAlias = str
AgentId: TypeAlias = str

_VOTE_TYPE_TO_UTILITY: Dict[str, Utility] = {
    "approval": "COST",
    "ordinal": "COST_ORDINAL",
    "cumulative": "COST_CUMULATIVE",
    "choose-1": "COST",
}


def detect_utility_from_instances(
    instances: Dict[District, Instance],
) -> Utility:
    vote_types = set()
    for instance in instances.values():
        if "vote_type" not in instance.meta:
            raise ValueError(
                f"Instance missing vote_type in meta: {instance.meta}"
            )
        vote_types.add(instance.meta["vote_type"])

    if len(vote_types) > 1:
        raise ValueError(
            f"Inconsistent vote_types across districts: {vote_types}"
        )

    vote_type = vote_types.pop()
    if vote_type not in _VOTE_TYPE_TO_UTILITY:
        raise NotImplementedError(
            f"vote_type '{vote_type}' has no utility mapping"
        )

    return _VOTE_TYPE_TO_UTILITY[vote_type]


def load_pabutools_by_district(
    path: str,
) -> Tuple[Dict[District, Instance], Dict[District, Profile]]:
    instances: Dict[District, Instance] = {}
    profiles: Dict[District, Profile] = {}

    relevant_files: List[str] = []
    if os.path.isfile(path) and path.endswith(".pb"):
        relevant_files.append(path)

    if os.path.isdir(path):
        for filename in os.listdir(path):
            if filename.endswith(".pb"):
                relevant_files.append(os.path.join(path, filename))

    for filename in relevant_files:
        if filename.endswith(".pb"):
            instance, profile = parse_pabulib(filename)
            district = (
                instance.meta["subunit"]
                if "subunit" in instance.meta
                else "citywide"
            )
            instances[district] = instance
            profiles[district] = profile
    return instances, profiles


def filter_projects(
    condition: Callable[[Project], bool], projects: Dict[AgentId, Project]
) -> List[AgentId]:
    return [p_id for p_id, project in projects.items() if condition(project)]


def by_district(district: str) -> Callable[[Project], bool]:
    return lambda project: project.district == district
