import sys
from pathlib import Path

if sys.version_info >= (3, 14):
    from uuid import uuid7
else:
    from uuid6 import uuid7

# Run dir: <run_id>_<data_source>_<utility>_<solver>_<key_hash>/
# Everything before key_hash is display/sort only and never parsed;
# identity lives in the key_hash suffix (see result_cache).
PROBLEM_FILENAME = "problem.lp"
META_FILENAME = "meta.json"


def data_source_name(source_directory_path: str) -> str:
    return Path(source_directory_path).name.replace(".pb", "")


def new_run_id() -> str:
    # uuid7: time-ordered, so run dirs sort by execution datetime
    return str(uuid7())


def run_dir_name(
    run_id: str,
    data_source: str,
    utility_type: str,
    solver_type: str,
    key_hash: str,
) -> str:
    return f"{run_id}_{data_source}_{utility_type}_{solver_type}_{key_hash}"
