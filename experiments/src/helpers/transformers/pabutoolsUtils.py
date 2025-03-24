from typing import Dict, Tuple, TypeAlias, Callable, List
import os
from pabutools.election import Instance, Profile, parse_pabulib, Project

District: TypeAlias = str
AgentId: TypeAlias = str


def load_pabutools_by_district(directory_path: str) -> \
        Tuple[Dict[District, Instance], Dict[District, Profile]]:
    instances: Dict[District, Instance] = {}
    profiles: Dict[District, Profile] = {}
    for filename in os.listdir(directory_path):
        if filename.endswith('.pb'):
            instance, profile = parse_pabulib(f"{directory_path}/{filename}")
            district = instance.meta['subunit'] if 'subunit' in instance.meta else 'citywide'
            instances[district] = instance
            profiles[district] = profile
    return instances, profiles


def filter_projects(condition: Callable[[Project], bool],
                    projects: Dict[AgentId, Project]) -> List[AgentId]:
    return [p_id for p_id, project in projects.items() if condition(project)]


def by_district(district: str) -> Callable[[Project], bool]:
    return lambda project: project.district == district
