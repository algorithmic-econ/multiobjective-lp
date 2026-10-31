import hashlib
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from helpers.runners.model import CacheKey, RunnerConfig, RunnerResult, Utility
from helpers.runners.source_strategy import resolve_constraints_configs
from helpers.utils.result_naming import META_FILENAME, data_source_name
from helpers.utils.utils import read_from_json

logger = logging.getLogger(__name__)

# Bump to invalidate every cached result (semantic change not visible in
# CacheKey fields, e.g. solver behaviour or LP format change).
CACHE_SCHEMA_VERSION = 1
KEY_HASH_LENGTH = 12


def build_cache_key(config: RunnerConfig, utility_type: Utility) -> CacheKey:
    return CacheKey(
        schema_version=CACHE_SCHEMA_VERSION,
        solver=config.solver_type,
        solver_options=config.solver_options,
        source_type=config.source_type,
        utility_type=utility_type,
        data_source=data_source_name(config.source_directory_path),
        constraints_configs=resolve_constraints_configs(config),
        deduplicate_objectives=config.deduplicate_objectives,
    )


def cache_key_hash(key: CacheKey) -> str:
    # exclude_defaults: adding a defaulted field keeps existing hashes
    payload = json.dumps(
        key.model_dump(mode="json", exclude_defaults=True),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:KEY_HASH_LENGTH]


def find_cached_run(results_base_path: Path, key: CacheKey) -> Path | None:
    key_hash = cache_key_hash(key)
    for run_dir in sorted(results_base_path.glob(f"*_{key_hash}")):
        meta_path = run_dir / META_FILENAME
        # meta.json is written last: its presence marks a completed run
        if not meta_path.is_file():
            continue
        try:
            existing = RunnerResult.model_validate(read_from_json(meta_path))
        except (ValidationError, ValueError):
            logger.warning(f"Ignoring incompatible meta file {meta_path}")
            continue
        if existing.cache_key != key:
            logger.warning(f"Hash collision, key mismatch in {meta_path}")
            continue
        return run_dir
    return None
