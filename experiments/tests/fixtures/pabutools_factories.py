from typing import Dict, List, Set, Tuple

import pytest
from pabutools.election import (
    ApprovalBallot,
    ApprovalProfile,
    CumulativeBallot,
    CumulativeProfile,
    Instance,
    OrdinalBallot,
    OrdinalProfile,
    Project,
)
from pulp import LpVariable


def make_project(
    name: str, cost: int, categories: Set[str] | None = None
) -> Project:
    return Project(name=name, cost=cost, categories=categories or set())


def make_instance(projects: List[Project], budget: int) -> Instance:
    cats = set()
    for p in projects:
        cats |= p.categories
    return Instance(
        init=projects,
        budget_limit=budget,
        categories=cats,
        meta={"budget": str(budget)},
    )


def make_approval_profile(
    ballots_dict: Dict[str, List[str]],
    projects_by_name: Dict[str, Project],
) -> ApprovalProfile:
    profile = ApprovalProfile()
    for voter_id, project_names in ballots_dict.items():
        ballot = ApprovalBallot(
            [projects_by_name[n] for n in project_names],
        )
        # pabutools bug: AbstractApprovalBallot.__init__ resets meta/name
        ballot.meta = {"voter_id": voter_id}
        ballot.name = voter_id
        profile.append(ballot)
    return profile


def make_ordinal_profile(
    ballots_dict: Dict[str, List[str]],
    projects_by_name: Dict[str, Project],
) -> OrdinalProfile:
    profile = OrdinalProfile()
    for voter_id, project_names in ballots_dict.items():
        ballot = OrdinalBallot(
            [projects_by_name[n] for n in project_names],
        )
        ballot.meta = {"voter_id": voter_id}
        ballot.name = voter_id
        profile.append(ballot)
    return profile


def make_cumulative_profile(
    ballots_dict: Dict[str, Dict[str, int]],
    projects_by_name: Dict[str, Project],
) -> CumulativeProfile:
    profile = CumulativeProfile()
    for voter_id, points_map in ballots_dict.items():
        ballot = CumulativeBallot(
            {projects_by_name[n]: pts for n, pts in points_map.items()},
        )
        ballot.meta = {"voter_id": voter_id}
        ballot.name = voter_id
        profile.append(ballot)
    return profile


def make_project_variables(
    projects: List[Project],
) -> Dict[str, LpVariable]:
    variables = LpVariable.dicts("V", [p.name for p in projects], cat="Binary")
    for v in variables.values():
        v.setInitialValue(0)
    return variables


# ---------- Composite fixtures ----------


@pytest.fixture
def single_district_setup() -> Tuple[
    Dict[str, Instance],
    Dict[str, ApprovalProfile],
    Dict[str, Project],
    Dict[str, LpVariable],
]:
    """1 district, 3 projects, budget 500, categories {edu, env}."""
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    p3 = make_project("p3", 300, {"edu", "env"})
    projects = [p1, p2, p3]
    by_name = {p.name: p for p in projects}

    instance = make_instance(projects, 500)
    profile = make_approval_profile(
        {"v1": ["p1", "p2"], "v2": ["p2", "p3"]}, by_name
    )

    instances = {"d1": instance}
    profiles = {"d1": profile}
    variables = make_project_variables(projects)
    return instances, profiles, by_name, variables


@pytest.fixture
def multi_district_setup() -> Tuple[
    Dict[str, Instance],
    Dict[str, ApprovalProfile],
    Dict[str, Project],
    Dict[str, LpVariable],
]:
    """2 districts (d1: budget 300, d2: budget 200), 4 projects, mixed cats."""
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    p3 = make_project("p3", 150, {"edu"})
    p4 = make_project("p4", 50, {"env"})
    by_name = {p.name: p for p in [p1, p2, p3, p4]}

    inst1 = make_instance([p1, p2], 300)
    inst2 = make_instance([p3, p4], 200)

    prof1 = make_approval_profile({"v1": ["p1", "p2"]}, by_name)
    prof2 = make_approval_profile({"v2": ["p3", "p4"]}, by_name)

    instances = {"d1": inst1, "d2": inst2}
    profiles = {"d1": prof1, "d2": prof2}
    variables = make_project_variables([p1, p2, p3, p4])
    return instances, profiles, by_name, variables
