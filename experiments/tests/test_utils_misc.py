"""Coverage for the small utility modules that had no direct test import:
enhance_from_solver_result, logger, preflib_to_muoblp.
"""

import logging

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable

from helpers.runners.model import RunnerResult, Solver, Source, Utility
from helpers.transformers.preflib_to_muoblp import parse_line
from helpers.utils.enhance_from_solver_result import (
    enhance_problem_from_solver_result,
)
from helpers.utils.logger import setup_logging


@pytest.fixture
def restore_root_logging():
    """setup_logging reconfigures the root logger process-wide."""
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers = handlers
    root.setLevel(level)


def _problem_with_two_projects() -> MultiObjectiveLpProblem:
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    problem = MultiObjectiveLpProblem(
        "tiny",
        objectives=[LpAffineExpression({p1: 1, p2: 1})],
        objectives_weights={},
    )
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"
    return problem


def _runner_result(selected: list[str]) -> RunnerResult:
    return RunnerResult(
        time=0.1,
        solver=Solver.GREEDY,
        solver_options={},
        source_type=Source.PABUTOOLS,
        utility_type=Utility.COST,
        source_path="input/x",
        constraints_configs=[],
        deduplicate_objectives=False,
        problem_path="ignored",
        instance_size=2,
        selected=selected,
    )


def test_enhance_sets_selected_to_one_and_rest_to_zero():
    problem = _problem_with_two_projects()

    enhanced = enhance_problem_from_solver_result(
        _runner_result(["p1"]), problem
    )

    values = {var.name: var.value() for var in enhanced.variables()}
    assert values == {"p1": 1, "p2": 0}


def test_enhance_with_empty_selection_zeroes_everything():
    problem = _problem_with_two_projects()

    enhanced = enhance_problem_from_solver_result(_runner_result([]), problem)

    assert all(var.value() == 0 for var in enhanced.variables())


def test_setup_logging_applies_config(tmp_path, restore_root_logging):
    config = tmp_path / "logging.yaml"
    config.write_text(
        "version: 1\ndisable_existing_loggers: false\nroot:\n  level: WARNING\n"
    )

    setup_logging(config)

    assert logging.getLogger().level == logging.WARNING


def test_setup_logging_missing_file_falls_back(
    tmp_path, caplog, restore_root_logging
):
    with caplog.at_level(logging.ERROR):
        setup_logging(tmp_path / "does-not-exist.yaml")

    assert "Error loading logging configuration" in caplog.text


def test_setup_logging_malformed_yaml_falls_back(
    tmp_path, caplog, restore_root_logging
):
    config = tmp_path / "logging.yaml"
    config.write_text("version: 1\n  bad: [unclosed\n")

    with caplog.at_level(logging.ERROR):
        setup_logging(config)

    assert "Error loading logging configuration" in caplog.text


def test_parse_line_flat_ranking():
    assert parse_line("3: 1,2,3") == (3, [[1], [2], [3]])


def test_parse_line_tied_group():
    assert parse_line("5: 1,{2,3}") == (5, [[1], [2, 3]])


def test_parse_line_rejects_nested_brace():
    with pytest.raises(RuntimeError, match="Cannot parse"):
        parse_line("1: {1,{2}")


def test_parse_line_rejects_unopened_brace():
    with pytest.raises(RuntimeError, match="Cannot parse"):
        parse_line("1: 1}")
