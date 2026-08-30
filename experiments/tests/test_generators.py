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
