from pathlib import Path
from typing import List

from helpers.runners.model import RunnerConfig, Solver
from helpers.utils.utils import write_to_json


def find_source_paths(root_path: str, use_directories: bool) -> List[Path]:
    root = Path(root_path)

    if not root.exists():
        raise FileNotFoundError

    if use_directories:
        return [p for p in root.iterdir() if p.is_dir()]
    else:
        return list(root.rglob("*.pb"))


def filter_paths(
    paths: List[Path], pattern_groups: List[List[str]]
) -> List[Path]:
    return [
        path
        for path in paths
        if any(
            all(pattern in str(path) for pattern in group)
            for group in pattern_groups
        )
    ]


if __name__ == "__main__":
    root_dir = "/Users/jasiek/Documents/Projects/pabulib-all"
    result_dir = "resources/experiment-results/greedy-phragmen-single-auto/"
    USE_DIRECTORIES = False

    raw_paths = find_source_paths(root_dir, USE_DIRECTORIES)

    selected_paths = raw_paths

    # selected_paths = filter_paths(
    #     raw_paths,
    #     [
    #         ["krakow", "2020"],
    #         ["krakow", "2021"],
    #         ["krakow", "2022"],
    #         ["krakow", "2023"],
    #         ["krakow", "2024"],
    #         ["warszawa", "2020"],
    #         ["warszawa", "2021"],
    #         ["warszawa", "2022"],
    #         ["warszawa", "2023"],
    #         ["warszawa", "2024"],
    #         ["amsterdam", "2020"],
    #         ["amsterdam", "2021"],
    #         ["amsterdam", "2022"],
    #         ["lodz", "2022"],
    #         ["lodz", "2023"],
    #         ["lodz", "2024"],
    #         ["czestochowa", "2020"],
    #         ["czestochowa", "2024"],
    #         ["czestochowa", "2025"],
    #         ["zabrze", "2020"],
    #         ["zabrze", "2021"],
    #     ],
    # )

    solvers_options: List[tuple[Solver, dict]] = [
        ("PHRAGMEN", {"kappa": 0.0, "increasing_scalings": True}),
        ("PHRAGMEN", {"kappa": 0.0, "increasing_scalings": False}),
        ("PHRAGMEN", {"kappa": 1.0, "increasing_scalings": True}),
        ("PHRAGMEN", {"kappa": 1.0, "increasing_scalings": False}),
        ("GREEDY", {}),
    ]

    configs: List[RunnerConfig] = []
    for path in selected_paths:
        for solver, options in solvers_options:
            config: RunnerConfig = {
                "solver_type": solver,
                "solver_options": options,
                "source_type": "PABUTOOLS",
                "source_directory_path": str(path),
            }
            configs.append(config)

    experiment = {
        "concurrency": 6,
        "experiment_results_base_path": result_dir,
        "runner_configs": configs,
    }

    output_path = Path(
        "../resources/input/experiment-config/greedy-phragmen-single-auto.jsonc"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_to_json(output_path, experiment)
