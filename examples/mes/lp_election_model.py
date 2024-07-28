from typing import TypeVar, Dict, TypeAlias, List, Tuple

from pulp import LpConstraint, LpVariable, LpProblem, LpMaximize, LpAffineExpression, lpSum, LpConstraintLE, \
    LpConstraintGE

TParameter = TypeVar('TParameter')
TConstraint = TypeVar('TConstraint')
Weight: TypeAlias = float
AgentId: TypeAlias = str
ConstraintId: TypeAlias = str
VariableId: TypeAlias = str


class LpElection:
    def __init__(self,
                 candidates: List[AgentId],
                 voters_preferences: Dict[AgentId, List[AgentId]]) -> None:
        self.lp_problem, self.selected_candidates, self.voters_objectives = \
            LpElection.define_lp_problem('mes', candidates, voters_preferences)

    def set_selected_candidates_values(self, selected: List[AgentId]):
        for candidate_id, variable in self.selected_candidates.items():
            variable.setInitialValue(1 if candidate_id in selected else 0)

    def get_infeasible_constraints(self) -> List[LpConstraint]:
        #
        # TODO: Generalise for lower and upper bound, should be LE or GE than 0 based on the LpSense
        #
        return [
            constraint for constraint in self.lp_problem.constraints.values()
            if (constraint.sense == LpConstraintGE and constraint.value() < 0) or
               (constraint.sense == LpConstraintLE and constraint.value() > 0)
        ]

    def define_constraint_ub(self, name: str, project_costs: Dict[AgentId, int], budget: int):
        # Σ (selected[i] * cost[i]) <= budget
        constraint = LpConstraint(
            e=lpSum(self.selected_candidates[c_id] * c_cost for c_id, c_cost in project_costs.items()),
            sense=LpConstraintLE,
            rhs=budget)
        self.lp_problem.addConstraint(constraint, f"ub_{name}")

    def define_constraint_lb(self, name: str, project_costs: Dict[AgentId, int], budget: int):
        # Σ (selected[i] * cost[i]) >= budget
        constraint = LpConstraint(
            e=lpSum(self.selected_candidates[c_id] * c_cost for c_id, c_cost in project_costs.items()),
            sense=LpConstraintGE,
            rhs=budget)
        self.lp_problem.addConstraint(constraint, f"lb_{name}")

    @staticmethod
    def define_lp_problem(name: str,
                          candidates: List[AgentId],
                          voters_preferences: Dict[AgentId, List[AgentId]]) -> Tuple[
        LpProblem, Dict[VariableId, LpVariable], Dict[AgentId, LpAffineExpression]]:
        lp_problem = LpProblem(name, LpMaximize)
        selected_candidates = LpVariable.dicts("selected_candidate", candidates, cat="Binary")
        for variable in selected_candidates.values():
            variable.setInitialValue(0)
        lp_problem.addVariables(selected_candidates.values())

        multi_objectives = {
            voter: LpElection.define_voter_objective(f"target_{voter}", approved_candidates, selected_candidates)
            for voter, approved_candidates in voters_preferences.items()
        }

        return lp_problem, selected_candidates, multi_objectives

    @staticmethod
    def define_voter_objective(name: str,
                               voter_preferences: List[AgentId],
                               candidate_variables: Dict[AgentId, LpVariable]) -> LpAffineExpression:
        approved_candidates_variables = [candidate_variables[candidate_id] for candidate_id in voter_preferences]
        return LpAffineExpression([[variable, 1] for variable in approved_candidates_variables], name=name)
