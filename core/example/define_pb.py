"""Minimal participatory budgeting election as a multi objective LP.

Three projects, two voters (one objective per voter), one budget
constraint. Run it directly: `python core/example/define_pb.py`.
"""

import tempfile
from pathlib import Path

from pulp import LpAffineExpression, LpConstraint, LpConstraintLE, LpVariable

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblp.utils.lp_reader_utils import read_lp_file


def define_pb() -> MultiObjectiveLpProblem:
    """Build the election: maximise every voter's utility under a budget."""
    projects = {
        name: LpVariable(name, cat="Binary")
        for name in ("park", "library", "bikelane")
    }
    costs = {"park": 100, "library": 200, "bikelane": 50}

    problem = MultiObjectiveLpProblem("pb-election")
    # one objective per voter, approval utility (1 per approved project)
    problem += LpAffineExpression(
        {projects["park"]: 1, projects["library"]: 1}, name="voter_1"
    )
    problem += LpAffineExpression(
        {projects["park"]: 1, projects["bikelane"]: 1}, name="voter_2"
    )
    problem.set_objectives_weights({"voter_1": 1, "voter_2": 1})

    problem += LpConstraint(
        LpAffineExpression(
            [(projects[name], cost) for name, cost in costs.items()]
        ),
        sense=LpConstraintLE,
        name="pb_constraint",
        rhs=250,
    )
    return problem


def main() -> None:
    problem = define_pb()
    print(f"{problem.name}: {len(problem.objectives)} objectives")
    print(f"weights: {problem.objectives_weights}")
    print(f"constraints: {list(problem.constraints)}")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "pb-election.lp"
        problem.write_lp(str(path))
        restored = read_lp_file(str(path))

    print(f"read back: {[o.name for o in restored.objectives]}")


if __name__ == "__main__":
    main()
