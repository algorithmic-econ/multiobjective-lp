import pytest
from pydantic import ValidationError

from helpers.runners.model import (
    RunnerConfig,
    RunnerResult,
    Solver,
    Utility,
)
from helpers.transformers.expand_experiment_config import (
    parse_experiment_config,
)


def test_malformed_config_validation_error_has_field_path():
    config = {
        "concurrency": 1,
        "experiment_results_base_path": "results/",
        "runner_configs": [
            {
                "solver_type": "NOT_A_SOLVER",
                "source_type": "PABUTOOLS",
                "source_directory_path": "input/x",
            }
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        parse_experiment_config(config)
    [error] = exc_info.value.errors()
    assert error["loc"] == ("runner_configs", 0, "solver_type")


def test_unknown_config_key_rejected():
    with pytest.raises(ValidationError) as exc_info:
        RunnerConfig.model_validate(
            {
                "solver_type": "GREEDY",
                "source_type": "PABUTOOLS",
                "source_directory_path": "input/x",
                "solver_optionz": {},
            }
        )
    assert exc_info.value.errors()[0]["loc"] == ("solver_optionz",)


def test_compact_config_expands():
    compact = {
        "compact_config": True,
        "concurrency": 2,
        "experiment_results_base_path": "results/",
        "runner_configs_generator": {
            "solvers": [{"type": "GREEDY"}, {"type": "STV"}],
            "source_type": "PABUTOOLS",
            "sources": ["input/a", "input/b"],
        },
    }
    experiment = parse_experiment_config(compact)
    assert len(experiment.runner_configs) == 4
    first = experiment.runner_configs[0]
    assert first.results_base_path == "results/"
    assert first.solver_options == {}
    assert first.constraints_configs is None


def test_solver_enum_has_all_ten():
    assert len(Solver) == 10
    assert {"STV", "SOLID_COALITION_REFINEMENT", "EXPANDING_APPROVALS"} <= {
        s.value for s in Solver
    }


def test_strenum_formats_to_value_in_filenames():
    # problemRunner/resultCache build filenames via f-strings — contract
    assert f"x_{Utility.COST_ORDINAL}_{Solver.GREEDY}.lp" == (
        "x_COST_ORDINAL_GREEDY.lp"
    )


def test_runner_result_roundtrips_meta_json():
    meta = {
        "constraints_configs": [],
        "deduplicate_objectives": False,
        "instance_size": 10,
        "problem_path": "results/problem_x.lp",
        "selected": ["V_1"],
        "solver": "GREEDY",
        "solver_options": {},
        "source_path": "input/krakow_2024_mini",
        "source_type": "PABUTOOLS",
        "time": 0.5,
        "utility_type": "COST_ORDINAL",
    }
    result = RunnerResult.model_validate(meta)
    assert result.model_dump(mode="json", exclude_none=True) == meta
