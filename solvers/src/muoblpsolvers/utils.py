from muoblp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal


def set_solved(lp: MultiObjectiveLpProblem, selected: list[str]) -> None:
    vals = {x.name: int(x.name in selected) for x in lp.variables()}
    lp.assignStatus(LpStatusOptimal)
    lp.assignVarsVals(vals)
