import argparse
import json
from pathlib import Path
from typing import List, Literal

from helpers.runners.model import (
    ExperimentConfig,
    RunnerConfig,
    Solver,
    Utility,
)
from helpers.utils.utils import write_to_json

Mode = Literal["citywide", "independent_districts"]


def discover_sources(mode: Mode, root_path: str) -> List[Path]:
    root = Path(root_path)
    if not root.exists():
        raise FileNotFoundError(root_path)

    if mode == "citywide":
        return [p for p in root.iterdir() if p.is_dir()]
    if mode == "independent_districts":
        return list(root.rglob("*.pb"))
    raise ValueError(f"unknown mode: {mode}")


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


def generate_experiment_config(
    mode: Mode,
    root_path: str,
    experiment_results_base_path: str,
    solvers_with_options: List[tuple[Solver, dict]],
    utilities: List[Utility] | None = None,
    pattern_groups: List[List[str]] | None = None,
    concurrency: int = 4,
    constraints_configs_path: str | None = None,
    deduplicate_objectives: bool = False,
) -> ExperimentConfig:
    paths = discover_sources(mode, root_path)
    if pattern_groups:
        paths = filter_paths(paths, pattern_groups)

    utility_iter: List[Utility | None] = (
        list(utilities) if utilities else [None]
    )

    runner_configs: List[RunnerConfig] = []
    for path in paths:
        for solver, options in solvers_with_options:
            for utility in utility_iter:
                config: RunnerConfig = {
                    "solver_type": solver,
                    "solver_options": options,
                    "source_type": "PABUTOOLS",
                    "source_directory_path": str(path),
                    "results_base_path": experiment_results_base_path,
                }
                if utility is not None:
                    config["utility_type"] = utility
                if constraints_configs_path:
                    config["constraints_configs_path"] = (
                        constraints_configs_path
                    )
                if deduplicate_objectives:
                    config["deduplicate_objectives"] = True
                runner_configs.append(config)

    return {
        "concurrency": concurrency,
        "experiment_results_base_path": experiment_results_base_path,
        "runner_configs": runner_configs,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ExperimentConfig JSON for experimentRunner.py"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["citywide", "independent_districts"],
    )
    parser.add_argument("--root", required=True, help="source root directory")
    parser.add_argument(
        "--output", required=True, help="output JSON/JSONC path"
    )
    parser.add_argument(
        "--results-base-path",
        required=True,
        help="experiment_results_base_path written into config",
    )
    parser.add_argument(
        "--solvers",
        required=True,
        help='JSON list of [solver, options] pairs, e.g. \'[["PHRAGMEN",{"kappa":0.0}],["GREEDY",{}]]\'',
    )
    parser.add_argument(
        "--utilities",
        nargs="*",
        default=[],
        help="optional utilities to multiply over (COST APPROVAL ...)",
    )
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--constraints-config",
        default=None,
        help="optional constraints_configs_path",
    )
    parser.add_argument(
        "--deduplicate-objectives", action="store_true", default=False
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # PLACEHOLDER - define long city/year pattern groups here when filtering needed.
    # AND within group, OR across groups. Example:
    # pattern_groups = [
    #     ["krakow", "2020"],
    #     ["krakow", "2021"],
    #     ["warszawa", "2022"],
    #     ["amsterdam", "2020"],
    # ]
    pattern_groups: List[List[str]] | None = None

    solvers_with_options: List[tuple[Solver, dict]] = [
        (solver, options) for solver, options in json.loads(args.solvers)
    ]

    config = generate_experiment_config(
        mode=args.mode,
        root_path=args.root,
        experiment_results_base_path=args.results_base_path,
        solvers_with_options=solvers_with_options,
        utilities=args.utilities or None,
        pattern_groups=pattern_groups,
        concurrency=args.concurrency,
        constraints_configs_path=args.constraints_config,
        deduplicate_objectives=args.deduplicate_objectives,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_to_json(output_path, config)
    print(f"Generated experiment configuration saved to {output_path}")
