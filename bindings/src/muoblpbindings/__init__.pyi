from pulp import LpProblem

def equal_shares_utils(
    voters: list[str],
    projects: list[str],
    cost: dict[str, float],
    approvals_utilities: dict[str, list[tuple[str, int]]],
    total_utility: dict[str, int],
    total_budget: float,
) -> list[str]:
    """
    Equal shares baseline
    """

def equal_shares_add1(
    voters: list[str],
    projects: list[str],
    cost: dict[str, float],
    approvals_utilities: dict[str, list[tuple[str, int]]],
    total_utility: dict[str, int],
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
