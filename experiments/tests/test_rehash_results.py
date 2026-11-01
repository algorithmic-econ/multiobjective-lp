import json
import os
import uuid
from pathlib import Path

from helpers.runners.model import RunnerConfig, RunnerResult, Utility
from helpers.utils.result_cache import (
    build_cache_key,
    cache_key_hash,
    find_cached_run,
)
from helpers.utils.result_naming import META_FILENAME, PROBLEM_FILENAME
from helpers.utils.utils import read_from_json
from rehash_results import main, uuid7_at

LEGACY_STEM = "07-20T10-00-00_ab12_krakow_2024_mini_COST_GREEDY"
MTIME = 1_750_000_000  # 2025-06-15


def _legacy_meta(results_dir: Path, **overrides) -> dict:
    return {
        "time": 0.1,
        "solver": "GREEDY",
        "solver_options": {},
        "source_type": "PABUTOOLS",
        "utility_type": "COST",
        "source_path": "input/krakow_2024_mini",
        "constraints_configs": [],
        "deduplicate_objectives": False,
        "problem_path": str(results_dir / f"problem_{LEGACY_STEM}.lp"),
        "instance_size": 1,
        "selected": ["p1"],
        **overrides,
    }


def _write_legacy(results_dir: Path, *, write_lp=True) -> Path:
    meta_path = results_dir / f"meta_{LEGACY_STEM}.json"
    meta_path.write_text(json.dumps(_legacy_meta(results_dir)))
    os.utime(meta_path, (MTIME, MTIME))
    if write_lp:
        (results_dir / f"problem_{LEGACY_STEM}.lp").write_text("LP")
    return meta_path


def _config(results_dir: Path) -> RunnerConfig:
    return RunnerConfig.model_validate(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": "other/root/krakow_2024_mini",
            "results_base_path": str(results_dir),
        }
    )


def test_uuid7_at_encodes_timestamp():
    value = uuid.UUID(uuid7_at(MTIME * 1000))
    assert value.version == 7
    assert value.variant == uuid.RFC_4122
    assert value.int >> 80 == MTIME * 1000


def test_legacy_result_migrated_into_run_dir(tmp_path):
    meta_path = _write_legacy(tmp_path)

    assert main(tmp_path) == (1, 0)

    assert not meta_path.exists()
    key = build_cache_key(_config(tmp_path), Utility.COST)
    run_dir = find_cached_run(tmp_path, key)
    assert run_dir is not None
    assert (run_dir / PROBLEM_FILENAME).read_text() == "LP"
    result = RunnerResult.model_validate(
        read_from_json(run_dir / META_FILENAME)
    )
    assert result.key_hash == cache_key_hash(key)
    assert result.problem_path == str(run_dir / PROBLEM_FILENAME)
    # run id keeps original execution time (meta mtime)
    run_id = uuid.UUID(run_dir.name[:36])
    assert run_id.int >> 80 == MTIME * 1000


def test_dry_run_changes_nothing(tmp_path):
    _write_legacy(tmp_path)
    before = sorted(tmp_path.iterdir())

    assert main(tmp_path, dry_run=True) == (1, 0)

    assert sorted(tmp_path.iterdir()) == before


def test_legacy_without_lp_skipped(tmp_path):
    meta_path = _write_legacy(tmp_path, write_lp=False)

    assert main(tmp_path) == (0, 0)

    assert meta_path.exists()


def test_stale_hash_run_dir_renamed(tmp_path):
    _write_legacy(tmp_path)
    main(tmp_path)
    [run_dir] = [path for path in tmp_path.iterdir() if path.is_dir()]
    good_hash = run_dir.name.rsplit("_", 1)[1]
    stale_dir = run_dir.rename(
        run_dir.with_name(run_dir.name.removesuffix(good_hash) + "stale")
    )
    meta = read_from_json(stale_dir / META_FILENAME)
    meta["key_hash"] = "stale"
    (stale_dir / META_FILENAME).write_text(json.dumps(meta))

    assert main(tmp_path) == (0, 1)

    assert not stale_dir.exists()
    assert run_dir.is_dir()
    assert read_from_json(run_dir / META_FILENAME)["key_hash"] == good_hash
    assert main(tmp_path) == (0, 0)
