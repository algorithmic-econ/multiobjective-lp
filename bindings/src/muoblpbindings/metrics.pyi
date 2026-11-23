from pulp import LpProblem

class SolvedInstance:
    """
    Opaque snapshot of a solved MuoblpProblem (variable values + objectives)
    """

    def __init__(self, prob: LpProblem) -> None: ...
    @property
    def num_voters(self) -> int: ...
    @property
    def num_candidates(self) -> int: ...
    @property
    def total_weight(self) -> float:
        """Sum of voter weights (objectives_weights, default 1)"""

def exclusion_ratio(instance: SolvedInstance) -> float:
    """
    Weighted fraction of voters with zero objective value
    """

def ejr_plus(instance: SolvedInstance, up_to_one: bool = True) -> int:
    """
    Number of unelected candidates violating EJR+ (up to one if
    `up_to_one`), voters weighted. Raises ValueError without a unique PB
    constraint
    """
