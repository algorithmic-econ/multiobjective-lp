import json
from pathlib import Path as _Path

import pytest
from pydantic import ValidationError

from helpers.analyzers.model import AnalyzerConfig
from helpers.runners.model import (
    ExperimentConfig,
    RunnerConfig,
    RunnerResult,
    Solver,
    Utility,
)
from helpers.transformers.expand_experiment_config import (
    parse_experiment_config,
    resolve_runner_configs,
)
from helpers.utils.utils import read_from_json


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
    # problem_runner/result_cache build filenames via f-strings — contract
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


def test_metadata_metric_dropped():
    with pytest.raises(ValidationError) as exc_info:
        AnalyzerConfig.model_validate(
            {
                "analyzer_result_path": "analysis/",
                "experiment_results_base_path": "results/",
                "metrics": ["METADATA"],
            }
        )
    assert exc_info.value.errors()[0]["loc"] == ("metrics", 0)


def test_incompatible_meta_is_cache_miss(tmp_path):
    from helpers.utils.result_cache import is_metadata_content_matching

    meta_path = tmp_path / "meta_bad.json"
    meta_path.write_text('{"solver": "GREEDY"}')
    config = RunnerConfig.model_validate(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": "input/x",
        }
    )
    assert is_metadata_content_matching(meta_path, config) is False


def test_is_result_present_matches_existing_cache_entry(tmp_path):
    from helpers.utils.result_cache import is_result_present

    config = RunnerConfig.model_validate(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": "input/krakow_2024_mini",
            "results_base_path": str(tmp_path) + "/",
        }
    )
    (
        tmp_path
        / "problem_07-20T10-00-00_ab12_krakow_2024_mini_COST_GREEDY.lp"
    ).write_text("")
    meta = RunnerResult(
        time=0.1,
        solver="GREEDY",
        solver_options={},
        source_type="PABUTOOLS",
        utility_type="COST",
        source_path="input/krakow_2024_mini",
        constraints_configs=[],
        deduplicate_objectives=False,
        problem_path="ignored",
        instance_size=1,
        selected=[],
    )
    (
        tmp_path / "meta_07-20T10-00-00_ab12_krakow_2024_mini_COST_GREEDY.json"
    ).write_text(json.dumps(meta.model_dump(mode="json", exclude_none=True)))

    assert is_result_present(config, Utility.COST) is True


def test_is_result_present_misses_on_different_solver(tmp_path):
    from helpers.utils.result_cache import is_result_present

    config = RunnerConfig.model_validate(
        {
            "solver_type": "MES_ADD1",
            "source_type": "PABUTOOLS",
            "source_directory_path": "input/krakow_2024_mini",
            "results_base_path": str(tmp_path) + "/",
        }
    )
    (
        tmp_path
        / "problem_07-20T10-00-00_ab12_krakow_2024_mini_COST_GREEDY.lp"
    ).write_text("")
    (
        tmp_path / "meta_07-20T10-00-00_ab12_krakow_2024_mini_COST_GREEDY.json"
    ).write_text("{}")

    assert is_result_present(config, Utility.COST) is False


def test_resolve_runner_configs_fills_missing_default():
    experiment = ExperimentConfig.model_validate(
        {
            "concurrency": 1,
            "experiment_results_base_path": "results/",
            "runner_configs": [
                {
                    "solver_type": "GREEDY",
                    "source_type": "PABUTOOLS",
                    "source_directory_path": "input/a",
                },
                {
                    "solver_type": "STV",
                    "source_type": "PABUTOOLS",
                    "source_directory_path": "input/b",
                    "results_base_path": "explicit/",
                },
            ],
        }
    )
    resolved = resolve_runner_configs(experiment)
    assert resolved[0].results_base_path == "results/"
    assert resolved[1].results_base_path == "explicit/"
    # no mutation of the original configs
    assert experiment.runner_configs[0].results_base_path is None
    assert experiment.runner_configs[1].results_base_path == "explicit/"


def test_analyzer_config_concurrency_defaults_to_three():
    config = AnalyzerConfig.model_validate(
        {
            "analyzer_result_path": "analysis/",
            "experiment_results_base_path": "results/",
            "metrics": [],
        }
    )
    assert config.concurrency == 3


def test_analyzer_config_concurrency_override():
    config = AnalyzerConfig.model_validate(
        {
            "analyzer_result_path": "analysis/",
            "experiment_results_base_path": "results/",
            "metrics": [],
            "concurrency": 8,
        }
    )
    assert config.concurrency == 8


SAMPLE_DIR = _Path(__file__).parents[1] / "sample-experiment"


def test_sample_experiment_config_validates():
    experiment = parse_experiment_config(
        read_from_json(SAMPLE_DIR / "experiment-config.jsonc")
    )
    assert len(experiment.runner_configs) == 4
    assert experiment.runner_configs[0].solver_type == Solver.MES_ADD1


def test_sample_analyzer_config_validates():
    config = AnalyzerConfig.model_validate(
        read_from_json(SAMPLE_DIR / "sample-analysis-config.jsonc")
    )
    assert len(config.metrics) == 3
