import importlib.util
from pathlib import Path

EXAMPLE_PATH = Path(__file__).parents[1] / "example" / "define_pb.py"


def _load_example():
    spec = importlib.util.spec_from_file_location("define_pb", EXAMPLE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readme_example_exists():
    assert EXAMPLE_PATH.is_file()


def test_example_runs(capsys):
    """Keeps the README example from rotting."""
    _load_example().main()

    assert "2 objectives" in capsys.readouterr().out


def test_example_defines_a_pb_election():
    problem = _load_example().define_pb()

    assert [o.name for o in problem.objectives] == ["voter_1", "voter_2"]
    assert problem.objectives_weights == {"voter_1": 1, "voter_2": 1}
    assert list(problem.constraints) == ["pb_constraint"]
