from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblp.utils.lp_reader_utils import read_lp_file
from pulp import LpAffineExpression, LpVariable


def test_write_lp_read_lp_roundtrip(tmp_path):
    """Analyzer depends on OBJECTIVES/WEIGHTS sections written by
    MultiObjectiveLpProblem.write_lp (plain pulp writeLP omits them)."""
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    v1 = LpAffineExpression({p1: 100}, name="T_v1")
    v2 = LpAffineExpression({p1: 100, p2: 200}, name="T_v2")
    problem = MultiObjectiveLpProblem(
        "tiny", objectives=[v1, v2], objectives_weights={"T_v1": 1, "T_v2": 1}
    )
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"

    path = tmp_path / "problem.lp"
    problem.write_lp(str(path))
    restored = read_lp_file(str(path))

    assert len(restored.objectives) == 2
    assert len(restored.constraints) == 1
    assert set(restored.objectives_weights) == {"T_v1", "T_v2"}
