from pulp import LpSolver

from model.multi_objective_lp import MultiObjectiveLpProblem


class MesLPSolver(LpSolver):
    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        print('Run MES')
