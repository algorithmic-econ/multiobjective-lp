from logging import Logger
from typing import List, Optional

from pulp import LpProblem, LpAffineExpression, PulpError, LpMaximize, LpMinimize, LpConstraint, LpVariable


class MultiObjectiveLpProblem(LpProblem):

    def __init__(self, name: str, sense: LpMaximize | LpMinimize = LpMaximize, objectives: List[LpAffineExpression] = None, logger: Optional[Logger] = None) -> None:
        super().__init__(name, sense=sense)
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

    # TODO: Decide how to handle fixObjective and restoreObjective

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

    @classmethod
    def fromDict(cls, _dict):

        # we instantiate the problem
        params = _dict["parameters"]
        pb_params = {"name", "sense"}
        args = {k: params[k] for k in pb_params}
        pb = cls(**args)
        pb.status = params["status"]
        pb.sol_status = params["sol_status"]

        # recreate the variables.
        var = {v["name"]: LpVariable.fromDict(**v) for v in _dict["variables"]}

        # objective function.
        # we change the names for the objects:
        recreated_objectives = []
        for objective in _dict["objectives"]:
            coefficients = {var[v["name"]]: v["value"] for v in objective["coefficients"]}
            recreated_objectives.append(LpAffineExpression(e=coefficients, name=objective["name"]))
        pb.setObjectives(recreated_objectives)

        # constraints
        # we change the names for the objects:
        def edit_const(const):
            const = dict(const)
            const["coefficients"] = {
                var[v["name"]]: v["value"] for v in const["coefficients"]
            }
            return const

        constraints = [edit_const(v) for v in _dict["constraints"]]
        for c in constraints:
            pb += LpConstraint.fromDict(c)

        # last, parameters, other options
        list_to_dict = lambda v: {k: v for k, v in enumerate(v)}
        pb.sos1 = list_to_dict(_dict["sos1"])
        pb.sos2 = list_to_dict(_dict["sos2"])

        return pb

    from_dict = fromDict

    # TODO: override __iadd__ to append objective to the list of objectives
