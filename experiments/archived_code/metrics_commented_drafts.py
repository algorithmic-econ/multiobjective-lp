# Archived in T25 (dead code sweep).
# Origin: experiments/src/helpers/analyzers/metrics.py, lines 111-174
# (trailing commented-out drafts, verbatim). Never executed, never
# imported; the live `ejr_plus` metric in the origin module is a
# different implementation and stays there.

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
