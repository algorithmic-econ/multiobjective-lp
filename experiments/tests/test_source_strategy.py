import json
from pathlib import Path

import pytest

from helpers.runners.model import (
    ConstraintConfig,
    RunnerConfig,
    Solver,
    Source,
    Utility,
)
from helpers.runners.source_strategy import (
    load_and_transform_strategy,
    resolve_constraints_configs,
)

FIXTURE_INPUT = (
    Path(__file__).parent / "fixtures" / "input" / "krakow_2024_mini"
)


def _config(**overrides) -> RunnerConfig:
    fields = {
        "solver_type": Solver.GREEDY,
        "source_type": Source.PABUTOOLS,
        "source_directory_path": str(FIXTURE_INPUT),
    }
    fields.update(overrides)
    return RunnerConfig.model_validate(fields)


def test_resolve_constraints_configs_returns_empty_when_unset():
    assert resolve_constraints_configs(_config()) == []


def test_resolve_constraints_configs_reads_and_validates_path(tmp_path):
    path = tmp_path / "constraints.json"
    path.write_text(
        json.dumps(
            [
                {
                    "key": "DISTRICT",
                    "value": "*",
                    "bound": "UPPER",
                    "budget_ratio": 0.5,
                }
            ]
        )
    )

    resolved = resolve_constraints_configs(
        _config(constraints_configs_path=str(path))
    )

    assert resolved == [
        ConstraintConfig(
            key="DISTRICT", value="*", bound="UPPER", budget_ratio=0.5
        )
    ]


def test_resolve_constraints_configs_inline_wins_over_path(tmp_path):
    path = tmp_path / "constraints.json"
    path.write_text(
        json.dumps([{"key": "CATEGORY", "value": "green", "bound": "LOWER"}])
    )
    inline = [ConstraintConfig(key="DISTRICT", value="*", bound="UPPER")]

    resolved = resolve_constraints_configs(
        _config(constraints_configs=inline, constraints_configs_path=str(path))
    )

    assert resolved == inline


def test_load_and_transform_strategy_detects_utility():
    problem, constraints, utility = load_and_transform_strategy(
        Source.PABUTOOLS, None, str(FIXTURE_INPUT), [], False
    )

    # krakow_2024_mini ballots are ordinal -> COST_ORDINAL per
    # pabutools_utils._VOTE_TYPE_TO_UTILITY.
    assert utility == Utility.COST_ORDINAL
    assert constraints == []
    assert len(problem.variables()) == 10  # 10 projects, 2 districts


def test_load_and_transform_strategy_honours_explicit_utility():
    _, _, utility = load_and_transform_strategy(
        Source.PABUTOOLS, Utility.APPROVAL, str(FIXTURE_INPUT), [], False
    )

    assert utility == Utility.APPROVAL


def test_load_and_transform_strategy_passes_constraints_through():
    # bound=LOWER on purpose: an UPPER district constraint collides by name
    # with the baseline per-district cap (pabutools_to_molp.py:509 TODO).
    constraints = [
        ConstraintConfig(
            key="DISTRICT", value="*", bound="LOWER", budget_ratio=0.1
        )
    ]

    problem, returned, _ = load_and_transform_strategy(
        Source.PABUTOOLS, Utility.COST, str(FIXTURE_INPUT), constraints, False
    )

    assert returned == constraints
    # total budget constraint + one per district
    assert len(problem.constraints) > 1


def test_load_and_transform_strategy_rejects_unknown_source():
    with pytest.raises(Exception, match="Strategy not implemented"):
        load_and_transform_strategy(
            "PREFLIB",  # type: ignore[arg-type]
            Utility.COST,
            str(FIXTURE_INPUT),
            [],
            False,
        )
