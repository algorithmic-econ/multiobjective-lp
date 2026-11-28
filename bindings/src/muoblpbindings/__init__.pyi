from pulp import LpProblem

def equal_shares_utils(
    voters: dict[str, float],
    projects: list[str],
    cost: dict[str, float],
    approvals_utilities: dict[str, list[tuple[str, int]]],
    total_utility: dict[str, float],
    total_budget: float,
) -> list[str]:
    """
    Equal shares baseline
    """

def equal_shares_add1(
    voters: dict[str, float],
    projects: list[str],
    cost: dict[str, float],
    approvals_utilities: dict[str, list[tuple[str, int]]],
    total_utility: dict[str, float],
    total_budget: float,
) -> list[str]:
    """
    Equal shares Add1
    """

def expanding_approvals(prob: LpProblem):
    """
    Expanding approvals rule
    """

def single_transferable_vote(prob: LpProblem):
    """
    Single transferable vote
    """

def solid_coalition_refinement(prob: LpProblem):
    """
    Solid coalition refinement
    """

def phragmen(
    voters: list[tuple[str, float]],
    profile: list[tuple[str, list[tuple[str, float]]]],
    costs: dict[str, float],
    constraints: list[tuple[int, float, list[tuple[str, float]]]],
    *,
    increasing_scalings: bool = False,
    kappa: float = 1.0,
    bos_version: bool = False,
    eps: float = 1e-6,
    time_limit: float | None = None,
) -> tuple[list[str], bool]:
    """
    Phragmen (cardinal), port of muoblpsolvers phragmen_cardinal.
    Returns (rank, timed_out).
    """
