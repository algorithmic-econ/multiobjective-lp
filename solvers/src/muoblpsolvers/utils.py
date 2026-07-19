from importlib.util import find_spec

from muoblp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal


def bindings_available() -> bool:
    """True if the muoblpbindings C++ package is importable (no side effects)."""
    return find_spec("muoblpbindings") is not None


def set_solved(
    lp: MultiObjectiveLpProblem,
    selected: list[str],
    status: int = LpStatusOptimal,
) -> None:
    vals = {x.name: int(x.name in selected) for x in lp.variables()}
    lp.assignStatus(status)
    lp.assignVarsVals(vals)
