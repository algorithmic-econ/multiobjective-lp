from functools import reduce
from operator import itemgetter, ior
from typing import Dict, TypeAlias, List, TypedDict, Literal

from pabutools.election import Instance, Profile
from pulp import LpVariable, LpAffineExpression, LpConstraint, lpSum, LpConstraintLE, LpConstraintGE

from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem

District: TypeAlias = str
AgentId: TypeAlias = str


class ConstraintConfig(TypedDict):
    category: str
    bound: Literal['UPPER', 'LOWER']
    budget_ratio: float


def pabutools_to_multi_objective_lp(instances: Dict[District, Instance],
                                    profiles: Dict[District, Profile],
                                    constraints_configs: List[ConstraintConfig]) -> MultiObjectiveLpProblem:
    problem = MultiObjectiveLpProblem('election')

    project_variables = create_projects_variables(instances)
    problem.addVariables(project_variables.values())

    objectives = create_voter_objectives(profiles, project_variables)
    problem.setObjectives(list(objectives.values()))

    district_constraints = create_baseline_constraints(instances, project_variables)
    for constraint in district_constraints:
        problem.addConstraint(constraint)

    category_constraints = create_constraints_from_config(constraints_configs, instances, project_variables)
    for constraint in category_constraints:
        problem.addConstraint(constraint)

    return problem


#
# Variables
#
def create_projects_variables(instances: Dict[District, Instance]) -> Dict[AgentId, LpVariable]:
    projects_ids = [project.name for instance in instances.values() for project in instance]
    variables = LpVariable.dicts("", projects_ids, cat='Binary')
    for variable in variables.values():
        variable.setInitialValue(0)
    return variables


#
# Objectives
#
def create_voter_objectives(profiles: Dict[District, Profile],
                            projects_variables: Dict[AgentId, LpVariable]) -> Dict[str, LpAffineExpression]:
    votes = {
        f"{district}_{ballot.meta['voter_id']}": [str(c) for c in ballot]
        for district, profile in profiles.items()
        for ballot in profile
    }

    return {
        voter: define_voter_objective(f"target_{voter}", approved_candidates, projects_variables)
        for voter, approved_candidates in votes.items()
    }


def define_voter_objective(name: str, approved_projects: List[AgentId],
                           projects_variables: Dict[AgentId, LpVariable]) -> LpAffineExpression:
    approved_projects_variables = [projects_variables[candidate_id] for candidate_id in approved_projects]
    return LpAffineExpression([[variable, 1] for variable in approved_projects_variables], name=name)


#
# Constraints
#
def create_baseline_constraints(instances: Dict[District, Instance],
                                projects_variables: Dict[AgentId, LpVariable]) -> List[LpConstraint]:
    budgets: Dict[District, int] = {
        district: int(instance.meta['budget']) if 'budget' in instance.meta else 0
        for district, instance in instances.items()
    }
    projects_costs: Dict[District, Dict[AgentId, int]] = {
        district: {project.name: int(project.cost) for project in instance}
        for district, instance in instances.items()
    }

    return [define_constraint_ub(district, projects_variables, projects_costs[district], budgets[district])
            for district in instances.keys()]


def create_constraints_from_config(constraints_configs: List[ConstraintConfig],
                                   instances: Dict[District, Instance],
                                   projects_variables: Dict[AgentId, LpVariable]) -> List[LpConstraint]:
    total_budget: int = sum([int(instance.meta['budget'])
                             if 'budget' in instance.meta else 0
                             for district, instance in instances.items()])
    allowed_categories = reduce(ior, [instance.categories for instance in instances.values()], set())

    projects = [project for instance in instances.values() for project in instance]
    constraints = []
    for constraint_config in constraints_configs:
        category, bound, budget_ratio = itemgetter('category', 'bound', 'budget_ratio')(constraint_config)
        if category not in allowed_categories:
            continue
        projects_costs = reduce(ior, [{project.name: int(project.cost)} for project in projects if category in project.categories], {})
        constraint_limit = int(budget_ratio * total_budget)
        if bound == 'UPPER':
            constraints.append(
                define_constraint_ub(category, projects_variables, projects_costs, constraint_limit))
        if bound == 'LOWER':
            constraints.append(
                define_constraint_lb(category, projects_variables, projects_costs, constraint_limit))

    return constraints


def define_constraint_ub(name: str,
                         all_projects_variables: Dict[AgentId, LpVariable],
                         participating_projects_costs: Dict[AgentId, int],
                         maximum_cost: int) -> LpConstraint:
    # Σ (selected[i] * cost[i]) <= budget
    return LpConstraint(
        e=lpSum(all_projects_variables[project_id] * project_cost for project_id, project_cost in
                participating_projects_costs.items()),
        sense=LpConstraintLE,
        rhs=maximum_cost, name=f"ub_{name}")


def define_constraint_lb(name: str,
                         all_projects_variables: Dict[AgentId, LpVariable],
                         participating_projects_costs: Dict[AgentId, int],
                         minimum_cost: int) -> LpConstraint:
    # Σ (selected[i] * cost[i]) >= minimumCost
    return LpConstraint(
        e=lpSum(all_projects_variables[project_id] * project_cost for project_id, project_cost in
                participating_projects_costs.items()),
        sense=LpConstraintGE,
        rhs=minimum_cost, name=f"lb_{name}")
