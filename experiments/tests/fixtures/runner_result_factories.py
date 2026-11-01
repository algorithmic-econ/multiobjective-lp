from typing import Any

from helpers.runners.model import CacheKey, Solver, Source, Utility
from helpers.utils.result_cache import CACHE_SCHEMA_VERSION, cache_key_hash


def make_cache_key(**overrides: Any) -> CacheKey:
    fields: dict[str, Any] = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "solver": Solver.GREEDY,
        "source_type": Source.PABUTOOLS,
        "utility_type": Utility.COST,
        "data_source": "krakow_2024_mini",
    }
    fields.update(overrides)
    return CacheKey.model_validate(fields)


def cache_key_fields(**overrides: Any) -> dict[str, Any]:
    """`cache_key` + `key_hash` kwargs for RunnerResult."""
    key = make_cache_key(**overrides)
    return {"cache_key": key, "key_hash": cache_key_hash(key)}
