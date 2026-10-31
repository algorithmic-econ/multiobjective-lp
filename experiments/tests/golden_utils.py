"""Golden-file helpers for the e2e test.

Normalization strips nondeterminism:
1. drop `time` (wall-clock)
2. `<uuid7>_` run dir prefix -> `ID_` (key_hash suffix kept)
3. paths -> run dir + basename only (kills tmp_path / absolute paths)
4. floats rounded to 6 dp (exclusion_ratio)
5. metrics rows: no None rows allowed, sorted by solver

Regen: UPDATE_GOLDEN=1 pytest -m e2e writes goldens, then the test FAILS on
purpose (leaked env var must not green CI). Inspect + commit separately.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

RUN_ID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}_"
)


def _round_floats(value: Any, ndigits: int = 6) -> Any:
    if isinstance(value, float):
        return round(value, ndigits)
    if isinstance(value, dict):
        return {k: _round_floats(v, ndigits) for k, v in value.items()}
    if isinstance(value, list):
        return [_round_floats(v, ndigits) for v in value]
    return value


def _normalize_path(path: str) -> str:
    # <tmp>/<uuid7>_..._<key_hash>/meta.json -> ID_..._<key_hash>/meta.json
    # key_hash kept on purpose: golden pins it (hash drift = cache miss)
    run_dir = RUN_ID_PATTERN.sub("ID_", Path(path).parent.name)
    return f"{run_dir}/{Path(path).name}"


def normalize_meta(meta: dict) -> dict:
    meta = _round_floats(meta)
    del meta["time"]
    meta["problem_path"] = _normalize_path(meta["problem_path"])
    meta["source_path"] = Path(meta["source_path"]).name
    return meta


def normalize_metrics_rows(rows: list) -> list:
    assert None not in rows, "analyzer produced None row (analysis failed)"
    rows = _round_floats(rows)
    for row in rows:
        del row["time"]
        row["problem_path"] = _normalize_path(row["problem_path"])
    return sorted(rows, key=lambda row: row["solver"])


def verify_golden(actual, golden_path: Path) -> Path | None:
    """Assert `actual` == parsed golden. UPDATE_GOLDEN=1: (re)write golden
    instead and return its path (caller must fail the test)."""
    if os.environ.get("UPDATE_GOLDEN"):
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n"
        )
        return golden_path
    golden = json.loads(golden_path.read_text())
    assert actual == golden
    return None
