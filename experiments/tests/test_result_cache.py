import json
from pathlib import Path

import pytest

from helpers.runners.model import (
    CacheKey,
    ConstraintConfig,
    RunnerConfig,
    RunnerResult,
    Solver,
    Utility,
)
from helpers.utils.result_cache import (
    CACHE_SCHEMA_VERSION,
    KEY_HASH_LENGTH,
    build_cache_key,
    cache_key_hash,
    find_cached_run,
)
from helpers.utils.result_naming import META_FILENAME, PROBLEM_FILENAME

from .fixtures.runner_result_factories import make_cache_key

# RunnerConfig field -> how it enters CacheKey. A new RunnerConfig field
# fails test_every_runner_config_field_is_keyed_or_excluded until it is
# added to build_cache_key (+ here) or consciously excluded.
KEYED_CONFIG_FIELDS = {
    "solver_type",
    "solver_options",
    "source_type",
    "utility_type",  # resolved utility passed separately
    "source_directory_path",  # -> data_source
    "constraints_configs",  # resolved
    "constraints_configs_path",  # resolved into constraints_configs
    "deduplicate_objectives",
}
EXCLUDED_CONFIG_FIELDS = {"results_base_path"}


def _config(**overrides) -> RunnerConfig:
    fields = {
        "solver_type": "GREEDY",
        "source_type": "PABUTOOLS",
        "source_directory_path": "input/krakow_2024_mini",
    }
    fields.update(overrides)
    return RunnerConfig.model_validate(fields)


def _write_run(results_dir: Path, key: CacheKey, *, write_meta=True) -> Path:
    key_hash = cache_key_hash(key)
    run_dir = results_dir / f"RUNID_{key.data_source}_{key_hash}"
    run_dir.mkdir(parents=True)
    (run_dir / PROBLEM_FILENAME).write_text("")
    if write_meta:
        result = RunnerResult(
            cache_key=key,
            key_hash=key_hash,
            time=0.1,
            solver=key.solver,
            solver_options=key.solver_options,
            source_type=key.source_type,
            utility_type=key.utility_type,
            source_path=f"input/{key.data_source}",
            constraints_configs=key.constraints_configs,
            deduplicate_objectives=key.deduplicate_objectives,
            problem_path=str(run_dir / PROBLEM_FILENAME),
            instance_size=1,
            selected=[],
        )
        (run_dir / META_FILENAME).write_text(
            json.dumps(result.model_dump(mode="json", exclude_none=True))
        )
    return run_dir


def test_every_runner_config_field_is_keyed_or_excluded():
    assert set(RunnerConfig.model_fields) == (
        KEYED_CONFIG_FIELDS | EXCLUDED_CONFIG_FIELDS
    )


def test_build_cache_key_from_config():
    key = build_cache_key(
        _config(source_directory_path="input/x/krakow.pb"), Utility.COST
    )
    assert key == make_cache_key(data_source="krakow")


def test_hash_is_pinned():
    # changing this = every existing result becomes a cache miss
    assert cache_key_hash(make_cache_key()) == "747f8c9111d7"


def test_hash_length():
    assert len(cache_key_hash(make_cache_key())) == KEY_HASH_LENGTH


def test_hash_ignores_solver_options_order():
    a = make_cache_key(solver_options={"timeLimit": 10, "msg": False})
    b = make_cache_key(solver_options={"msg": False, "timeLimit": 10})
    assert cache_key_hash(a) == cache_key_hash(b)


def test_explicit_default_hashes_like_omitted():
    explicit = make_cache_key(
        solver_options={}, constraints_configs=[], deduplicate_objectives=False
    )
    assert cache_key_hash(explicit) == cache_key_hash(make_cache_key())


def test_new_defaulted_field_keeps_hash():
    class FutureCacheKey(CacheKey):
        new_flag: bool = False

    key = make_cache_key()
    future = FutureCacheKey.model_validate(key.model_dump())
    assert cache_key_hash(future) == cache_key_hash(key)


@pytest.mark.parametrize(
    "override",
    [
        {"schema_version": CACHE_SCHEMA_VERSION + 1},
        {"solver": Solver.MES_ADD1},
        {"solver_options": {"timeLimit": 10}},
        {"utility_type": Utility.APPROVAL},
        {"data_source": "warszawa_2024"},
        {
            "constraints_configs": [
                ConstraintConfig(
                    key="DISTRICT", value="*", bound="UPPER", budget_ratio=0.5
                )
            ]
        },
        {"deduplicate_objectives": True},
    ],
)
def test_hash_changes_with_each_key_field(override):
    assert cache_key_hash(make_cache_key(**override)) != cache_key_hash(
        make_cache_key()
    )


def test_find_cached_run_hit(tmp_path):
    run_dir = _write_run(tmp_path, make_cache_key())
    assert find_cached_run(tmp_path, make_cache_key()) == run_dir


def test_find_cached_run_misses_on_different_key(tmp_path):
    _write_run(tmp_path, make_cache_key())
    other = make_cache_key(solver_options={"timeLimit": 10})
    assert find_cached_run(tmp_path, other) is None


def test_find_cached_run_misses_without_meta(tmp_path):
    # lp written, run died before meta (commit marker)
    _write_run(tmp_path, make_cache_key(), write_meta=False)
    assert find_cached_run(tmp_path, make_cache_key()) is None


def test_find_cached_run_ignores_incompatible_meta(tmp_path):
    run_dir = _write_run(tmp_path, make_cache_key())
    (run_dir / META_FILENAME).write_text('{"solver": "GREEDY"}')
    assert find_cached_run(tmp_path, make_cache_key()) is None


def test_find_cached_run_ignores_corrupt_meta(tmp_path):
    run_dir = _write_run(tmp_path, make_cache_key())
    (run_dir / META_FILENAME).write_text("not json")
    assert find_cached_run(tmp_path, make_cache_key()) is None


def test_find_cached_run_rejects_key_mismatch(tmp_path):
    # simulated hash collision: dir carries the hash, stored key differs
    key = make_cache_key()
    other_dir = _write_run(tmp_path, make_cache_key(solver=Solver.STV))
    other_dir.rename(tmp_path / f"RUNID_x_{cache_key_hash(key)}")
    assert find_cached_run(tmp_path, key) is None


def test_find_cached_run_missing_results_dir(tmp_path):
    assert find_cached_run(tmp_path / "nope", make_cache_key()) is None
