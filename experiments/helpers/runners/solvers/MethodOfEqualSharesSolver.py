from pulp import LpSolver, lpSum, PULP_CBC_CMD

from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem


class MethodOfEqualSharesSolver(LpSolver):
    """

    Info:
        Solver that executes Methods of Equal Shares to find solution

    """

    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        """
        Parameters:
            lp: Instance of MultiObjectiveLpProblem
        """
        pass
        # TODO: Transform problem into parameters for C++ program
        # TODO: Run C++ MES implementation and return selected candidates
