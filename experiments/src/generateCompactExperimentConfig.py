from pathlib import Path
from typing import List

import questionary

from generateExperimentConfig import (
    discover_sources,
    filter_paths,
    prompt_allowed_solvers,
    prompt_solver_options,
)
from helpers.runners.model import (
    CompactExperimentConfig,
    RunnerConfigsGenerator,
    Solver,
    SolverSpec,
)
from helpers.utils.utils import write_to_json

if __name__ == "__main__":
    # PLACEHOLDER - define long city/year pattern groups here when filtering needed.
    # AND within group, OR across groups. Example:
    pattern_groups = [
        # ["krakow", "2020"],
        ["krakow", "2021"],
        ["warszawa", "2022"],
        # ["amsterdam", "2020"],
    ]

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

    solvers_with_options: List[tuple[Solver, dict]] = []
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

    paths = discover_sources(mode, root)
    if pattern_groups:
        paths = filter_paths(paths, pattern_groups)

    config = CompactExperimentConfig(
        compact_config=True,
        concurrency=concurrency,
        experiment_results_base_path=results_base_path,
        runner_configs_generator=RunnerConfigsGenerator(
            solvers=[
                SolverSpec(type=solver, options=options)
                for solver, options in solvers_with_options
            ],
            source_type=source_type,
            sources=[str(path) for path in paths],
            constraints_configs_path=constraints_cfg,
            deduplicate_objectives=deduplicate_objectives,
        ),
    )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_to_json(
        output_path, config.model_dump(mode="json", exclude_none=True)
    )
    print(f"Generated compact experiment configuration saved to {output_path}")


# Source data directory: /Users/jasiek/Documents/Projects/pabulib/
# Experiment config json output path: ./resources/input/experiment-config/krk-waw-grouped.jsonc
# Results base path: ./resources/experiment-results/krk-waw-grouped/
