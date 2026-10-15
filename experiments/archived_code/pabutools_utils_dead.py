# Archived in T25 (dead code sweep).
# Origin: experiments/src/helpers/transformers/pabutools_utils.py
# Both functions had zero call sites since before the roadmap started.
# `AgentId` is a TypeAlias still live in the origin module (imported by
# pabutools_to_molp.py); redeclared here so this file stands alone.

from typing import TypeAlias
from collections.abc import Callable

from pabutools.election import Project

AgentId: TypeAlias = str


def filter_projects(
    condition: Callable[[Project], bool], projects: dict[AgentId, Project]
) -> list[AgentId]:
    return [p_id for p_id, project in projects.items() if condition(project)]


def by_district(district: str) -> Callable[[Project], bool]:
    return lambda project: project.district == district
