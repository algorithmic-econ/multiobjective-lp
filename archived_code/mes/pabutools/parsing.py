import os
from typing import TypeAlias, Set, Dict, Tuple

from pabutools.election import Instance, Profile, parse_pabulib

from examples.mes.pabutools.model import EnhancedProject, EnhancedProfile

District: TypeAlias = str


def instance_to_enhanced_projects(
    instance: Instance, district: District
) -> Set[EnhancedProject]:
    return {
        EnhancedProject(project=project, district=district, costs=[project.cost])
        for project in instance
    }


def profile_to_enhanced_profile(
    profile: Profile, district: District
) -> EnhancedProfile:
    return EnhancedProfile(profile=profile, district=district)


def load_pabulib_to_enhanced_projects_and_district_profiles(
    directory_path: str,
) -> Tuple[
    Dict[str, EnhancedProject], Dict[District, EnhancedProfile], Dict[District, int]
]:
    merged_projects: Dict[str, EnhancedProject] = {}
    profiles: Dict[District, EnhancedProfile] = {}
    budgets: Dict[District, int] = {}
    for filename in os.listdir(directory_path):
        if filename.endswith(".pb"):
            instance, profile = parse_pabulib(directory_path + filename)
            district = (
                instance.meta["subunit"] if "subunit" in instance.meta else "citywide"
            )
            merged_projects |= {
                p.project.name: p
                for p in instance_to_enhanced_projects(instance, district)
            }
            profiles[district] = profile_to_enhanced_profile(profile, district)
            budgets[district] = (
                int(instance.meta["budget"]) if "budget" in instance.meta else 0
            )
    return merged_projects, profiles, budgets
