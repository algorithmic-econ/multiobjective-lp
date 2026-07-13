from pathlib import Path
from typing import List, Literal

import questionary

from helpers.runners.model import (
    ExperimentConfig,
    RunnerConfig,
    Solver,
    Source,
    Utility,
)
from helpers.utils.utils import write_to_json

Mode = Literal["citywide", "independent_districts"]

SOLVER_CHOICES: List[str] = [
    "SUMMING",
    "MES_ADD1",
    "MES_CONSTRAINT",
    "MES_UTILS",
    "MES_EXPONENTIAL",
    "GREEDY",
    "PHRAGMEN",
]

UTILITY_CHOICES: List[str] = [
    "COST",
    "APPROVAL",
    "ORDINAL",
    "CUMULATIVE",
    "COST_ORDINAL",
    "COST_CUMULATIVE",
]

# (option_name, kind, default_or_None) -- kind in {"float","int","bool"}.
# Numeric blank input -> key omitted (solver falls back to in-code default).
# Bool keys are always included with the chosen value.
SOLVER_OPTION_SPECS: dict[str, list[tuple[str, str, object | None]]] = {
    "GREEDY": [],
    "MES_ADD1": [],
    "MES_UTILS": [],
    "PHRAGMEN": [
        ("kappa", "float", 1.0),
        ("increasing_scalings", "bool", False),
        ("bos_version", "bool", False),
        ("eps", "float", 1e-6),
    ],
    "MES_CONSTRAINT": [
        ("cost_modification_base", "float", 1.007),
        ("max_iterations", "int", 200),
    ],
    "MES_EXPONENTIAL": [
        ("budget_init", "int", None),
    ],
    "SUMMING": [
        ("use_gurobi", "bool", False),
    ],
}


def prompt_allowed_solvers() -> List[str]:
    while True:
        allowed = questionary.checkbox(
            "Allowed solvers (you'll add one or more entries below):",
            choices=SOLVER_CHOICES,
        ).ask()
        if allowed:
            return allowed
        print("Select at least one solver.")


def prompt_solver_options(solver: str) -> dict:
    options: dict = {}
    for name, kind, default in SOLVER_OPTION_SPECS[solver]:
        if kind == "bool":
            options[name] = questionary.confirm(
                f"  {solver}.{name}?", default=bool(default)
            ).ask()
            continue
        hint = "none" if default is None else str(default)
        raw = questionary.text(
            f"  {solver}.{name} ({kind}, blank = omit/default {hint}):",
            default="",
        ).ask()
        raw = (raw or "").strip()
        if raw == "":
            continue
        options[name] = float(raw) if kind == "float" else int(raw)
    return options


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
    source_type: Source,
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
                    "source_type": source_type,
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


if __name__ == "__main__":
    # PLACEHOLDER - define long city/year pattern groups here when filtering needed.
    # AND within group, OR across groups. Example:
    pattern_groups = [
        # ["krakow", "2020"],
        ["krakow", "2021"],
        ["warszawa", "2022"],
        # ["amsterdam", "2020"],
    ]
    # pattern_groups: List[List[str]] | None = None

    source_type = questionary.select(
        "Source type:",
        choices=["PABUTOOLS"],
    ).ask()

    mode = questionary.select(
        "Source mode:",
        choices=["citywide", "independent_districts"],
    ).ask()

    root = questionary.text("Source data directory:").ask()
    output = questionary.text("Experiment config json output path:").ask()
    results_base_path = questionary.text("Results base path:").ask()

    allowed_solvers = prompt_allowed_solvers()

    solvers_with_options: list[tuple[Solver, dict]] = []
    seen: set[tuple[Solver, frozenset]] = set()
    while True:
        if solvers_with_options:
            action = questionary.select(
                f"Current entries: {len(solvers_with_options)}. Add another?",
                choices=["Add entry", "Done"],
            ).ask()
            if action == "Done":
                break
        solver = questionary.select(
            "Solver for this entry:", choices=allowed_solvers
        ).ask()
        options = prompt_solver_options(solver)
        signature = (solver, frozenset(options.items()))
        if signature in seen:
            print(
                f"Entry {solver} with these options already added, skipping."
            )
            continue
        seen.add(signature)
        solvers_with_options.append((solver, options))

    if not solvers_with_options:
        raise SystemExit("No solver entries configured")

    # utilities = (
    #     questionary.checkbox(
    #         "Utilities (optional, leave empty to omit utility_type):",
    #         choices=UTILITY_CHOICES,
    #     ).ask()
    #     or None
    # )

    concurrency = int(questionary.text("Concurrency:", default="4").ask())

    constraints_cfg = (
        questionary.text(
            "Constraints config path (empty for none):", default=""
        ).ask()
        or None
    )

    deduplicate_objectives = questionary.confirm(
        "Deduplicate objectives?", default=False
    ).ask()

    config = generate_experiment_config(
        mode=mode,
        source_type=source_type,
        root_path=root,
        experiment_results_base_path=results_base_path,
        solvers_with_options=solvers_with_options,
        # utilities=utilities,
        pattern_groups=pattern_groups,
        concurrency=concurrency,
        constraints_configs_path=constraints_cfg,
        deduplicate_objectives=deduplicate_objectives,
    )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_to_json(output_path, config)
    print(f"Generated experiment configuration saved to {output_path}")
