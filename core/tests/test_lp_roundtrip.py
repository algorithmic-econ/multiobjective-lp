from pulp import LpAffineExpression, LpVariable

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblp.utils.lp_reader_utils import read_lp_file


def test_write_lp_read_lp_roundtrip(tmp_path):
    """write_lp appends the OBJECTIVES/WEIGHTS sections read_lp_file needs
    (plain pulp writeLP omits them)."""
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    problem = MultiObjectiveLpProblem("roundtrip")
    problem += LpAffineExpression({p1: 100}, name="v1")
    problem += LpAffineExpression({p1: 100, p2: 200}, name="v2")
    problem.set_objectives_weights({"v1": 1, "v2": 2})
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"

    path = tmp_path / "problem.lp"
    problem.write_lp(str(path))
    restored = read_lp_file(str(path))

    assert [o.name for o in restored.objectives] == ["v1", "v2"]
    assert restored.objectives_weights == {"v1": 1.0, "v2": 2.0}
    assert list(restored.constraints) == ["pb_constraint"]
    assert sorted(v.name for v in restored.variables()) == ["p1", "p2"]
