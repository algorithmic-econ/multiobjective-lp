from pathlib import Path

import pytest
from pydantic import ValidationError

from generate_experiment_config import build_runner_configs
from helpers.runners.model import (
    Solver,
    SolverSpec,
    Source,
    SweepSpec,
    Utility,
)
from helpers.transformers.expand_experiment_config import (
    parse_experiment_config,
)
from helpers.utils.utils import read_from_json, write_to_json

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SWEEP_SPEC_FIXTURE = FIXTURES_DIR / "sweep-spec.json"
SWEEP_INPUT_DIR = FIXTURES_DIR / "input"


def test_sweep_spec_rejects_unknown_key():
    with pytest.raises(ValidationError) as exc_info:
        SweepSpec.model_validate(
            {
                "mode": "citywide",
                "root_path": "x",
                "solvers": [{"type": "GREEDY"}],
                "experiment_results_base_path": "results/",
                "output_path": "out.json",
                "bogus_key": 1,
            }
        )
    assert exc_info.value.errors()[0]["loc"] == ("bogus_key",)


def test_sweep_spec_minimal_valid():
    spec = SweepSpec.model_validate(
        {
            "mode": "citywide",
            "root_path": "x",
            "solvers": [{"type": "GREEDY"}],
            "experiment_results_base_path": "results/",
            "output_path": "out.json",
        }
    )
    assert spec.solvers == [SolverSpec(type=Solver.GREEDY)]
    assert spec.utilities is None
    assert spec.pattern_groups == []


def test_build_runner_configs_cartesian_size_with_utilities():
    paths = [Path("a"), Path("b")]
    solvers_with_options = [
        (Solver.GREEDY, {}),
        (Solver.PHRAGMEN, {"kappa": 1.0}),
    ]
    utilities = [Utility.COST, Utility.APPROVAL]

    configs = build_runner_configs(
        paths,
        solvers_with_options,
        utilities,
        Source.PABUTOOLS,
        "results/",
        None,
        False,
    )

    assert len(configs) == 8


def test_build_runner_configs_no_utilities_omits_utility_type():
    paths = [Path("a"), Path("b")]
    solvers_with_options = [(Solver.GREEDY, {}), (Solver.PHRAGMEN, {})]

    configs = build_runner_configs(
        paths,
        solvers_with_options,
        None,
        Source.PABUTOOLS,
        "results/",
        None,
        False,
    )

    assert len(configs) == 4
    assert all(c.utility_type is None for c in configs)


def test_build_runner_configs_options_land_in_solver_options():
    configs = build_runner_configs(
        [Path("a")],
        [(Solver.PHRAGMEN, {"kappa": 0.5})],
        None,
        Source.PABUTOOLS,
        "results/",
        None,
        False,
    )
    assert configs[0].solver_options == {"kappa": 0.5}


def _load_sweep_spec_dict(**overrides) -> dict:
    spec_dict = read_from_json(SWEEP_SPEC_FIXTURE)
    spec_dict["root_path"] = str(SWEEP_INPUT_DIR)
    spec_dict.update(overrides)
    return spec_dict


def test_generate_from_spec_builds_expected_runner_configs():
    import generate_sweep_config as gsc

    spec = SweepSpec.model_validate(_load_sweep_spec_dict())

    config = gsc.generate_from_spec(spec)

    # 1 discovered source dir (krakow_2024_mini) x 3 solver entries
    assert len(config.runner_configs) == 3
    parse_experiment_config(config)


def test_main_writes_and_reads_back_valid_config(tmp_path):
    import generate_sweep_config as gsc

    spec_dict = _load_sweep_spec_dict(
        output_path=str(tmp_path / "generated" / "sweep.json"),
        experiment_results_base_path=str(tmp_path / "results"),
    )
    spec_path = tmp_path / "spec.json"
    write_to_json(spec_path, spec_dict)

    output_path = gsc.main(spec_path)

    assert output_path == Path(spec_dict["output_path"])
    written = read_from_json(output_path)
    parse_experiment_config(written)
