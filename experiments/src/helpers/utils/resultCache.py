import logging
import os
import re
from pathlib import Path

from helpers.runners.model import RunnerConfig, Utility
from helpers.runners.sourceStrategy import resolve_constraints_configs
from helpers.utils.utils import read_from_json

logger = logging.getLogger(__name__)


def is_metadata_content_matching(
    meta_path: Path, problem_config: RunnerConfig
) -> bool:
    existing_result = read_from_json(meta_path)

    # Check if solver options match
    if existing_result["solver_options"] != problem_config.get(
        "solver_options", {}
    ):
        return False

    # Check if constraints match
    current_constraints = resolve_constraints_configs(problem_config)

    if existing_result["constraints_configs"] != current_constraints:
        return False

    # Check if the corresponding LP file exists
    lp_filename = (
        os.path.basename(meta_path)
        .replace("meta_", "problem_")
        .replace(".json", ".lp")
    )
    lp_path = os.path.join(os.path.dirname(meta_path), lp_filename)
    return os.path.exists(lp_path)


def is_result_present(
    problem_config: RunnerConfig, utility_type: Utility
) -> bool:
    base_path = problem_config["results_base_path"]
    solver_type = problem_config["solver_type"]
    data_source = (
        problem_config["source_directory_path"]
        .split("/")[-1]
        .replace(".pb", "")
    )

    for filename in os.listdir(base_path):
        pattern = f"meta_[0-9]{{2}}-[0-9]{{2}}T[0-9]{{2}}-[0-9]{{2}}-[0-9]{{2}}_[a-z0-9]{{4}}_{data_source}_{utility_type}_{solver_type}.json"
        if re.match(pattern, filename):
            metadata_file_path = Path(os.path.join(base_path, filename))
            if is_metadata_content_matching(
                metadata_file_path, problem_config
            ):
                logger.info(f"Found result {filename}")
                return True

    return False
