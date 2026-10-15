# Archived T31: duplicate of `muoblpsolvers.election_solver.validate_pb_constraint`
# (was `muoblpsolvers/mes/common.py::get_total_budget_constraint`). MES
# solvers now receive the PB constraint from `validate_election_program`.
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpConstraint, LpConstraintLE, PulpSolverError

from muoblpsolvers.types import CandidateId


def get_total_budget_constraint(lp: MultiObjectiveLpProblem) -> LpConstraint:
    all_candidates: set[CandidateId] = {
        variable.name
        for variable in lp.variables()
        if variable.name != "__dummy"
    }

    pb_constraints = []
    for constraint in lp.constraints.values():
        candidates = {variable.name for variable in constraint}
        if candidates == all_candidates and constraint.sense == LpConstraintLE:
            pb_constraints.append(constraint)

    if len(pb_constraints) == 0:
        raise PulpSolverError("Problem does not have PB constraint")
    if len(pb_constraints) > 1:
        raise PulpSolverError("Problem has too many PB constraint")
    return pb_constraints[0]
