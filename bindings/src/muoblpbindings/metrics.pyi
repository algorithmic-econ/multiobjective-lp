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

def exclusion_ratio(instance: SolvedInstance) -> float:
    """
    Fraction of voters with zero objective value
    """
