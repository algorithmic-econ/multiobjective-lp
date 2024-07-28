from logging import Logger
from typing import List, Optional

from pulp import LpProblem, LpAffineExpression, PulpError


class MultiObjectiveLpProblem(LpProblem):

    def __init__(self, name: str, objectives: List[LpAffineExpression] = None, logger: Optional[Logger] = None) -> None:
        super().__init__(name)
        self._objectives = objectives
        self._logger = logger

    @property
    def objectives(self) -> List[LpAffineExpression]:
        return self._objectives

    def setObjectives(self, objectives: List[LpAffineExpression]) -> None:
        self._objectives = objectives

    @property
    def logger(self) -> Logger:
        return self._logger

    def fixObjective(self):
        if self.logger is not None:
            self.logger.warning("fixObjective is incompatible with MultiObjectiveLp, returning mock values")
        print("fixObjective is incompatible with MultiObjectiveLp, returning mock values")
        return 1, None

    def restoreObjective(self, wasNone, dummyVar):
        if self.logger is not None:
            self.logger.warning("SKIPPED, restoreObjective is incompatible with MultiObjectiveLp")
            pass

    def toDict(self) -> dict:
        try:
            self.checkDuplicateVars()
        except PulpError:
            raise PulpError(
                "Duplicated names found in variables:\nto export the model, variable names need to be unique"
            )
        # TODO: Skip calling fixObjective()
        variables = self.variables()
        return dict(
            # TODO: List of objectives
            objectives=[dict(name=objective.name, coefficients=objective.toDict()) for objective in self.objectives],
            constraints=[v.toDict() for v in self.constraints.values()],
            variables=[v.toDict() for v in variables],
            parameters=dict(
                name=self.name,
                sense=self.sense,
                status=self.status,
                sol_status=self.sol_status,
            ),
            sos1=list(self.sos1.values()),
            sos2=list(self.sos2.values()),
        )

    to_dict = toDict

    # TODO: override __iadd__ to append objective to the list of objectives
