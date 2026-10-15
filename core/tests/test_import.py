from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


def test_construct_problem():
    problem = MultiObjectiveLpProblem(name="smoke")
    assert problem.name == "smoke"
    assert problem.objectives == []
    assert problem.objectives_weights == {}
