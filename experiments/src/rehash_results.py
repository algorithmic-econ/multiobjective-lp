"""Migrate results to content-addressed run dirs (no re-solving).

Two layouts handled inside <results_dir>:
1. legacy flat `meta_<id>_....json` + `problem_<id>_....lp` -> run dir;
   run id = uuid7 at meta mtime, so execution order is preserved
2. run dirs: recompute key_hash from stored cache_key (after a CacheKey or
   hashing change) and rename the dir when the hash differs

Usage (from experiments/):
    python src/rehash_results.py <results_dir> [--dry-run]
"""

import argparse
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from helpers.runners.model import CacheKey, RunnerResult
from helpers.utils.logger import setup_logging
from helpers.utils.result_cache import CACHE_SCHEMA_VERSION, cache_key_hash
from helpers.utils.result_naming import (
    META_FILENAME,
    PROBLEM_FILENAME,
    data_source_name,
    run_dir_name,
)
from helpers.utils.utils import read_from_json, write_to_json

logger = logging.getLogger(__name__)


def uuid7_at(unix_ms: int) -> str:
    # RFC 9562: 48-bit ms timestamp | version 7 | random | variant 0b10
    value = (unix_ms & ((1 << 48) - 1)) << 80
    value |= int.from_bytes(os.urandom(10)) & ((1 << 80) - 1)
    value = (value & ~(0xF << 76)) | (0x7 << 76)
    value = (value & ~(0x3 << 62)) | (0x2 << 62)
    return str(uuid.UUID(int=value))


def legacy_cache_key(meta: dict[str, Any]) -> CacheKey:
    return CacheKey(
        schema_version=CACHE_SCHEMA_VERSION,
        solver=meta["solver"],
        solver_options=meta.get("solver_options", {}),
        source_type=meta["source_type"],
        utility_type=meta["utility_type"],
        data_source=data_source_name(meta["source_path"]),
        constraints_configs=meta.get("constraints_configs", []),
        deduplicate_objectives=meta.get("deduplicate_objectives", False),
    )


def migrate_legacy(meta_path: Path, dry_run: bool) -> bool:
    lp_path = meta_path.with_name(
        meta_path.name.replace("meta_", "problem_", 1)
    ).with_suffix(".lp")
    if not lp_path.is_file():
        logger.warning(f"Skip {meta_path.name}: missing {lp_path.name}")
        return False
    meta = read_from_json(meta_path)
    key = legacy_cache_key(meta)
    key_hash = cache_key_hash(key)
    run_id = uuid7_at(int(meta_path.stat().st_mtime * 1000))
    run_dir = meta_path.parent / run_dir_name(
        run_id, key.data_source, key.utility_type, key.solver, key_hash
    )
    result = RunnerResult.model_validate(
        {
            **meta,
            "cache_key": key,
            "key_hash": key_hash,
            # keep stored relative/absolute form, move into run dir
            "problem_path": str(
                Path(meta["problem_path"]).parent
                / run_dir.name
                / PROBLEM_FILENAME
            ),
        }
    )
    logger.info(f"{meta_path.name} -> {run_dir.name}/")
    if dry_run:
        return True
    run_dir.mkdir()
    os.replace(lp_path, run_dir / PROBLEM_FILENAME)
    write_to_json(
        run_dir / META_FILENAME,
        result.model_dump(mode="json", exclude_none=True),
    )
    meta_path.unlink()
    return True


def rehash_run_dir(run_dir: Path, dry_run: bool) -> bool:
    result = RunnerResult.model_validate(
        read_from_json(run_dir / META_FILENAME)
    )
    new_hash = cache_key_hash(result.cache_key)
    if new_hash == result.key_hash:
        return False
    new_dir = run_dir.with_name(
        run_dir.name.removesuffix(result.key_hash) + new_hash
    )
    logger.info(f"{run_dir.name}/ -> {new_dir.name}/")
    if dry_run:
        return True
    result.key_hash = new_hash
    result.problem_path = str(
        Path(result.problem_path).parent.with_name(new_dir.name)
        / PROBLEM_FILENAME
    )
    os.replace(run_dir, new_dir)
    write_to_json(
        new_dir / META_FILENAME,
        result.model_dump(mode="json", exclude_none=True),
    )
    return True


def main(results_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    migrated = sum(
        migrate_legacy(meta_path, dry_run)
        for meta_path in sorted(results_dir.glob("meta_*.json"))
    )
    rehashed = sum(
        rehash_run_dir(meta_path.parent, dry_run)
        for meta_path in sorted(results_dir.glob(f"*/{META_FILENAME}"))
    )
    logger.info(f"migrated {migrated}, rehashed {rehashed}")
    return migrated, rehashed


if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Migrate results to content-addressed run dirs"
    )
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(args.results_dir, args.dry_run)
