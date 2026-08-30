"""Runner-level cache behaviour (ROADMAP T26 AC: cache-hit-skips-solve).

Uses a real GREEDY solve on the mini fixture (sub-second) so the assertion
covers the actual round trip: what problem_runner writes must be what
result_cache recognises on the next run.
"""

from pathlib import Path

import pytest

import problem_runner as problem_runner_module
from helpers.runners.model import RunnerConfig, Solver, Source

FIXTURE_INPUT = (
    Path(__file__).parent / "fixtures" / "input" / "krakow_2024_mini"
)


def _config(results_dir: Path) -> RunnerConfig:
    return RunnerConfig(
        solver_type=Solver.GREEDY,
        source_type=Source.PABUTOOLS,
        source_directory_path=str(FIXTURE_INPUT),
        results_base_path=str(results_dir),
    )


def _metas(results_dir: Path) -> list[Path]:
    return sorted(results_dir.glob("meta_*.json"))


def test_first_run_persists_meta_and_lp(tmp_path):
    problem_runner_module.problem_runner(_config(tmp_path))

    assert len(_metas(tmp_path)) == 1
    assert len(list(tmp_path.glob("problem_*.lp"))) == 1


def test_cache_hit_skips_solve(tmp_path, monkeypatch):
    config = _config(tmp_path)
    problem_runner_module.problem_runner(config)
    meta_before = _metas(tmp_path)
    assert len(meta_before) == 1

    def boom(*args, **kwargs):
        raise AssertionError("solver constructed on cache hit")

    monkeypatch.setattr(problem_runner_module, "get_solver", boom)

    # Must return via the cache short-circuit without touching get_solver.
    problem_runner_module.problem_runner(config)

    assert _metas(tmp_path) == meta_before


def test_cache_miss_calls_solver(tmp_path):
    calls = []
    real_get_solver = problem_runner_module.get_solver

    def counting_get_solver(*args, **kwargs):
        calls.append(args)
        return real_get_solver(*args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(problem_runner_module, "get_solver", counting_get_solver)
        problem_runner_module.problem_runner(_config(tmp_path))

    assert len(calls) == 1
    assert len(_metas(tmp_path)) == 1


def test_missing_results_base_path_raises(tmp_path):
    config = _config(tmp_path)
    config.results_base_path = None

    with pytest.raises(ValueError, match="results_base_path"):
        problem_runner_module.problem_runner(config)
