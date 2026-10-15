import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

# Single source of truth for the runner/analyzer result filename shape.
# result_filename_pattern() reuses this template with a wildcard problem_id
# so builder and cache matcher can never drift apart.
PROBLEM_ID_PATTERN = (
    r"[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2}_[a-z0-9]{4}"
)


def data_source_name(source_directory_path: str) -> str:
    return Path(source_directory_path).name.replace(".pb", "")


def new_problem_id() -> str:
    timestamp = (
        datetime.now().isoformat(timespec="seconds").replace(":", "-")[5:]
    )
    return f"{timestamp}_{str(uuid4())[:4]}"


def result_filename(
    file_type: Literal["problem", "meta"],
    ext: Literal["lp", "json"],
    problem_id: str,
    data_source: str,
    utility_type: str,
    solver_type: str,
) -> str:
    return (
        f"{file_type}_{problem_id}_{data_source}_{utility_type}_"
        f"{solver_type}.{ext}"
    )


def result_filename_pattern(
    file_type: Literal["problem", "meta"],
    ext: Literal["lp", "json"],
    data_source: str,
    utility_type: str,
    solver_type: str,
) -> re.Pattern[str]:
    return re.compile(
        result_filename(
            file_type,
            ext,
            PROBLEM_ID_PATTERN,
            data_source,
            utility_type,
            solver_type,
        )
    )
