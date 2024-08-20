from src.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpConstraint, LpConstraintGE, LpConstraintLE
from typing import List, Optional
from logging import Logger


class MultiObjectiveLpElection(MultiObjectiveLpProblem):

    def __init__(self, name: str = "mes",
                 objectives: List[LpAffineExpression] = None,
                 logger: Optional[Logger] = None) -> None:
        if objectives is None:
            objectives = []
        super().__init__(name, objectives, logger)

    def solve(self, solver=None, **kwargs) -> None:
        if self.logger is not None:
            self.logger.info("Run MES")
        else:
            print("Run MES")

    def get_infeasible_constraints(self) -> List[LpConstraint]:
        return [
            constraint for constraint in self.constraints.values()
            if (constraint.sense == LpConstraintGE and constraint.value() < 0) or
               (constraint.sense == LpConstraintLE and constraint.value() > 0)
        ]
