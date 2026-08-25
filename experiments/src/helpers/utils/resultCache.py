import logging
from pathlib import Path

from pydantic import ValidationError

from helpers.runners.model import RunnerConfig, RunnerResult, Utility
from helpers.runners.sourceStrategy import resolve_constraints_configs
from helpers.utils.result_naming import (
    data_source_name,
    result_filename_pattern,
)
from helpers.utils.utils import read_from_json

logger = logging.getLogger(__name__)


def is_metadata_content_matching(
    meta_path: Path, problem_config: RunnerConfig
) -> bool:
    try:
        existing_result = RunnerResult.model_validate(
            read_from_json(meta_path)
        )
    except ValidationError:
        logger.warning(f"Ignoring incompatible meta file {meta_path}")
        return False

    if existing_result.solver_options != problem_config.solver_options:
        return False

    if existing_result.constraints_configs != resolve_constraints_configs(
        problem_config
    ):
        return False

    if (
        existing_result.deduplicate_objectives
        != problem_config.deduplicate_objectives
    ):
        return False

    # Check if the corresponding LP file exists
    lp_filename = meta_path.name.replace("meta_", "problem_").replace(
        ".json", ".lp"
    )
    lp_path = meta_path.parent / lp_filename
    return lp_path.exists()


def is_result_present(
    problem_config: RunnerConfig, utility_type: Utility
) -> bool:
    base_path = problem_config.results_base_path
    if base_path is None:
        raise ValueError("results_base_path not set on RunnerConfig")
    solver_type = problem_config.solver_type
    data_source = data_source_name(problem_config.source_directory_path)

    pattern = result_filename_pattern(
        "meta", "json", data_source, str(utility_type), str(solver_type)
    )
    for meta_path in Path(base_path).iterdir():
        if pattern.match(meta_path.name):
            if is_metadata_content_matching(meta_path, problem_config):
                logger.info(f"Found result {meta_path.name}")
                return True

    return False
