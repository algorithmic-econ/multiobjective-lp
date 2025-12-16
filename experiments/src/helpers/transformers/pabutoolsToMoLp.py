from collections import defaultdict
from functools import reduce
from operator import ior, itemgetter
from typing import Dict, List, Tuple, TypeAlias

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pabutools.election import (
    CumulativeProfile,
    Instance,
    OrdinalProfile,
    Profile,
    Project,
)
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintGE,
    LpConstraintLE,
    LpVariable,
    lpSum,
)

from ..runners.model import ConstraintConfig, Utility
from .pabutoolsConstants import (
    CONSTRAINT_PREFIX,
    TARGET_PREFIX,
    VARIABLE_PREFIX,
)

District: TypeAlias = str
AgentId: TypeAlias = str


def pabutools_to_multi_objective_lp(
    instances: Dict[District, Instance],
    profiles: Dict[District, Profile],
    constraints_configs: List[ConstraintConfig],
    utility: Utility,
) -> MultiObjectiveLpProblem:
    problem = MultiObjectiveLpProblem(f"election-{'-'.join(instances.keys())}")

    project_variables = create_projects_variables(instances)
    problem.addVariables(project_variables.values())

    objectives = create_voter_objectives(utility, profiles, project_variables)
    problem.setObjectives(list(objectives.values()))

    district_constraints = create_baseline_constraints(
        instances, project_variables
    )
    for constraint in district_constraints:
        problem.addConstraint(constraint)

    additional_constraints = create_constraints_from_config(
        constraints_configs,
        instances,
        project_variables,
    )
    for constraint in additional_constraints:
        problem.addConstraint(constraint)

    return problem


#
# Variables
#
def create_projects_variables(
    instances: Dict[District, Instance],
) -> Dict[AgentId, LpVariable]:
    projects_ids = [
        project.name for instance in instances.values() for project in instance
    ]
    variables = LpVariable.dicts(VARIABLE_PREFIX, projects_ids, cat="Binary")
    for variable in variables.values():
        variable.setInitialValue(0)
    return variables


#
# Objectives
#
def ballot_to_expression_strategy(
    utility: Utility,
) -> [str, int]:
    match utility:
        case "APPROVAL":
            return lambda ballot: [[str(c), 1] for c in ballot]
        case "COST":
            return lambda ballot: [[str(c), int(c.cost)] for c in ballot]
        case "ORDINAL":
            return lambda ballot: [
                [str(c), len(ballot) - idx] for idx, c in enumerate(ballot)
            ]
        case "CUMULATIVE":
            return lambda ballot: [
                [str(c), int(points)] for c, points in ballot.items()
            ]
        case "COST_ORDINAL":
            return lambda ballot: [
                [str(c), int(c.cost) * (len(ballot) - idx)]
                for idx, c in enumerate(ballot)
            ]
        case "COST_CUMULATIVE":
            return lambda ballot: [
                [str(c), int(c.cost) * int(points)]
                for c, points in ballot.items()
            ]
    raise Exception(f"Unknown utility ${utility}")


def validate_profile_type_matches_utility(
    profile: Profile, utility: Utility
) -> bool:
    match utility:
        case "APPROVAL":
            return True
        case "COST":
            return True
        case "ORDINAL" | "COST_ORDINAL":
            return isinstance(profile, OrdinalProfile)
        case "CUMULATIVE" | "COST_CUMULATIVE":
            return isinstance(profile, CumulativeProfile)
    raise Exception(f"Unknown utility ${utility}")


def create_voter_objectives(
    utility: Utility,
    profiles: Dict[District, Profile],
    projects_variables: Dict[AgentId, LpVariable],
) -> Dict[str, LpAffineExpression]:
    ballot_mapper_by_utility = ballot_to_expression_strategy(utility)
    votes = defaultdict(list)

    for district, profile in profiles.items():
        # TODO: Extract input data validation
        if not validate_profile_type_matches_utility(profile, utility):
            raise Exception(
                f"Profile for {district} does not match utility {utility}"
            )
        for ballot in profile:
            votes[ballot.meta["voter_id"]] += ballot_mapper_by_utility(ballot)

    return {
        voter: define_voter_objective(
            f"{TARGET_PREFIX}_{voter}", approved_candidates, projects_variables
        )
        for voter, approved_candidates in votes.items()
    }


def define_voter_objective(
    name: str,
    approved_projects_utilities: List[Tuple[AgentId, float]],
    projects_variables: Dict[AgentId, LpVariable],
) -> LpAffineExpression:
    approved_projects_variables = [
        [projects_variables[candidate_id], utility]
        for candidate_id, utility in approved_projects_utilities
    ]
    return LpAffineExpression(
        [
            [variable, utility]
            for variable, utility in approved_projects_variables
        ],
        name=name,
    )


#
# Base Constraints (total and per UB district)
#
def create_baseline_constraints(
    instances: Dict[District, Instance],
    projects_variables: Dict[AgentId, LpVariable],
) -> List[LpConstraint]:
    budgets: Dict[District, int] = {
        district: (
            int(float(instance.meta["budget"]))
            if "budget" in instance.meta
            else 0
        )
        for district, instance in instances.items()
    }
    projects_costs: Dict[District, Dict[AgentId, int]] = {
        district: {project.name: int(project.cost) for project in instance}
        for district, instance in instances.items()
    }

    all_projects_costs = {
        k: v
        for district_projects_costs in projects_costs.values()
        for k, v in district_projects_costs.items()
    }

    total_budget_constraint = define_constraint(
        "total_budget",
        LpConstraintLE,
        projects_variables,
        all_projects_costs,
        sum(budgets.values()),
    )

    if len(instances) == 1:
        return [total_budget_constraint]

    return [
        define_constraint(
            district,
            LpConstraintLE,
            projects_variables,
            projects_costs[district],
            budgets[district],
        )
        for district in instances.keys()
    ] + [total_budget_constraint]


def create_constraints_from_config(
    constraints_configs: List[ConstraintConfig],
    instances: Dict[District, Instance],
    projects_variables: Dict[AgentId, LpVariable],
) -> List[LpConstraint]:
    total_budget: int = sum(
        [
            int(float(instance.meta["budget"]))
            if "budget" in instance.meta
            else 0
            for district, instance in instances.items()
        ]
    )
    allowed_categories = reduce(
        ior, [instance.categories for instance in instances.values()], set()
    )

    projects = [
        project for instance in instances.values() for project in instance
    ]
    constraints = []
    for constraint_config in constraints_configs:
        if (
            constraint_config["key"] == "CATEGORY"
            and constraint_config["value"] in allowed_categories
        ):
            constraints.append(
                create_category_constraint(
                    constraint_config,
                    projects_variables,
                    projects,
                    total_budget,
                )
            )
        if (
            constraint_config["key"] == "DISTRICT"
            and constraint_config["value"] in instances.keys()
        ):
            constraints.append(
                create_district_constraint(
                    constraint_config,
                    projects_variables,
                    [
                        project
                        for project in instances[constraint_config["value"]]
                    ],
                    total_budget,
                )
            )
    return constraints


def create_category_constraint(
    constraint_config: ConstraintConfig,
    projects_variables: Dict[AgentId, LpVariable],
    projects: List[Project],
    total_budget: int,
) -> LpConstraint:
    category, bound, budget_ratio = itemgetter(
        "value", "bound", "budget_ratio"
    )(constraint_config)
    projects_costs = reduce(
        ior,
        [
            {project.name: int(project.cost)}
            for project in projects
            if category in project.categories
        ],
        {},
    )

    constraint_limit = int(budget_ratio * total_budget)
    sense = LpConstraintLE if bound == "UPPER" else LpConstraintGE
    return define_constraint(
        category, sense, projects_variables, projects_costs, constraint_limit
    )


def create_district_constraint(
    constraint_config: ConstraintConfig,
    projects_variables: Dict[AgentId, LpVariable],
    district_projects: List[Project],
    total_budget: int,
) -> LpConstraint:
    district, bound, budget_ratio = itemgetter(
        "value", "bound", "budget_ratio"
    )(constraint_config)
    projects_costs = reduce(
        ior,
        [{project.name: int(project.cost)} for project in district_projects],
        {},
    )

    constraint_limit = int(budget_ratio * total_budget)
    # TODO: Validate constraint config, district upper bound is created in baseline constraints
    sense = LpConstraintLE if bound == "UPPER" else LpConstraintGE
    return define_constraint(
        district, sense, projects_variables, projects_costs, constraint_limit
    )


def define_constraint(
    name: str,
    sense: LpConstraintGE | LpConstraintLE,
    all_projects_variables: Dict[AgentId, LpVariable],
    participating_projects_costs: Dict[AgentId, int],
    maximum_cost: int,
) -> LpConstraint:
    return LpConstraint(
        e=lpSum(
            all_projects_variables[project_id] * project_cost
            for project_id, project_cost in participating_projects_costs.items()
        ),
        sense=sense,
        rhs=maximum_cost,
        name=f"{CONSTRAINT_PREFIX}_{'ub' if sense == LpConstraintLE else 'lb'}_{name}",
    )
