from typing import Dict, Callable, List

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpsolvers.common import get_total_budget_constraint

from helpers.analyzers.model import Metric, AnalyzerResult


def get_metrics(
    metrics: List[Metric], problem: MultiObjectiveLpProblem
) -> Dict:
    result: AnalyzerResult = {"metrics": metrics}
    for metric in metrics:
        result |= {metric: get_metric_strategy(metric)(problem)}
    return result


def get_metric_strategy(
    metric: Metric,
) -> Callable[[MultiObjectiveLpProblem], Dict]:
    if metric == "EXCLUSION_RATION":
        return exclusion_ratio
    if metric == "SUM_OBJECTIVES":
        return sum_objectives
    if metric == "EJR_PLUS":
        return ejr_plus

    raise Exception("Metric not implemented")


def exclusion_ratio(problem: MultiObjectiveLpProblem) -> Dict:
    zero_count = len([1 for obj in problem.objectives if obj.value() == 0])
    return {
        "exclusion_ratio": zero_count / len(problem.objectives),
    }


def sum_objectives(problem: MultiObjectiveLpProblem) -> Dict:
    return {
        "sum": sum([obj.value() for obj in problem.objectives]),
    }


def ejr_plus(problem: MultiObjectiveLpProblem) -> Dict:
    # TODO: Check if utility was COST based
    # TODO: Introduce metric options, i.e., pass up_to_one as config parameter
    up_to_one = True

    costs: dict[str, int] = {
        candidate.name: cost
        for constraint in problem.constraints.values()
        for candidate, cost in constraint.items()
    }

    total_budget = get_total_budget_constraint(problem)

    voter_satisfaction = sorted(
        [(voter, voter.value()) for voter in problem.objectives],
        key=lambda v_sat: v_sat[1],
    )
    voter_count = len(problem.objectives)
    failures = []

    for project in problem.variables():
        if project.value() == 1:  # skip elected
            continue
        coalition_size = 0
        for voter, satisfaction in voter_satisfaction:
            # if voter approved of project
            if project in voter.keys():
                coalition_size += 1
                ejr_satisfied = satisfaction >= (
                    coalition_size / voter_count
                ) * total_budget - (costs[project.name] if up_to_one else 0)
                if not ejr_satisfied:
                    failures.append(project.name)
                    break

    return {"ejr_plus": len(failures)}


# def ejr_plus_violations(instance, profile, outcome, up_to_one=True):
#     utility = []
#     for vote in profile:
#         utility.append(Cost_Sat(instance, profile, vote).sat(outcome))
#     sorted_voters = sorted(enumerate(profile), key=lambda x: utility[x[0]])
#     failures = []
#     for not_elected in instance:
#         if not_elected in outcome:
#             continue
#         coalition_size = 0
#         for i, voter in sorted_voters:
#             if not_elected in voter:
#                 coalition_size += 1
#                 if up_to_one:
#                     ejr_satisfied = (
#                         utility[i]
#                         >= (coalition_size / len(profile)) * instance.budget_limit
#                         - not_elected.cost
#                     )
#                 else:
#                     ejr_satisfied = (
#                         utility[i]
#                         >= (coalition_size / len(profile)) * instance.budget_limit
#                     )
#                 if not ejr_satisfied:
#                     failures.append(not_elected.name)
#                     break
#     return failures
#
#
#
# def cost_sat_func(
#         instance: Instance,
#         profile: AbstractProfile,
#         ballot: AbstractBallot,
#         project: Project,
#         precomputed_values: dict,
# ) -> int:
#     if isinstance(ballot, AbstractCardinalBallot):
#         return ballot.get(project, 0) * project.cost
#     elif isinstance(ballot, AbstractOrdinalBallot):
#         if project in ballot:
#             return (len(ballot) - ballot.position(project)) * project.cost
#         else:
#             return 0
#     else:
#         return int(project in ballot) * project.cost


# def get_project_sat(self, project: Project) -> Numeric:
#     score = self.scores.get(project, None)
#     if score is None:
#         score = self.func(
#             self.instance,
#             self.profile,
#             self.ballot,
#             project,
#             self.precomputed_values,
#         )
#         self.scores[project] = score
#     return score
#
# def sat(self, proj: Collection[Project]) -> Numeric:
#     return sum(self.get_project_sat(p) for p in proj)
