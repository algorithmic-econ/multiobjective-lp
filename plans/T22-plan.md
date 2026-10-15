# T22 Consolidate Config Generators Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One interactive generator (`generate_experiment_config.py`, keeps `discover_sources`/`filter_paths`/`prompt_*`) that emits full OR compact config; one sweep generator (`generate_sweep_config.py`) driven by a JSON `SweepSpec` (replaces hardcoded `generate_phragmen_greedy_district_experiment.py`); `generate_compact_experiment_config.py` + `generate_experiment.py` → archived_code. Output via `model_dump` of T19 models.

**Architecture:** Shared pure core in `generate_experiment_config.py`: existing `discover_sources`/`filter_paths` + NEW extracted `build_runner_configs(paths, solvers_with_options, utilities, ...)` (the cartesian product currently inlined in `generate_experiment_config()` — sweep uses the same fn → "zero dup helpers"). Interactive `__main__` gains 2 prompts: output format full|compact, optional pattern-groups (folds the hardcoded placeholder both interactive scripts carried). Sweep entrypoint = thin: read spec json → `SweepSpec.model_validate` → discover/filter/build → validate resulting `ExperimentConfig` → `model_dump(mode="json", exclude_none=True)` write. User decision: sweep params from JSON config file (not module constants). Kills T09 leftover (generators writing into deleted `resources/…` defaults — all paths now from spec/prompts).

**Tech Stack:** T19 pydantic models (`StrictModel`, `SolverSpec`, `CompactExperimentConfig`, `parse_experiment_config`), questionary (interactive only, untested), pytest for pure helpers.

## Global Constraints

- Branch `feat/t22-generators` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T19+T21 merge** (models exist; files already snake_case: `generate_experiment_config.py`, `generate_compact_experiment_config.py`, `generate_experiment.py`, `generate_phragmen_greedy_district_experiment.py`). Verify names/line refs against merged tree; T19 Task 5 already switched generators to model construction + `model_dump` writes — this ticket consolidates entrypoints, does not re-do that.
- e2e golden IDENTICAL, NO regen (generators are outside the runner/analyzer path).
- No new features beyond parameterization of existing hardcoded behavior: sweep spec fields mirror what the hardcoded script + interactive flow already express. No per-solver option schemas (T10 contract: options = free-form constructor kwargs).
- Interactive prompt flow NOT unit-tested (questionary); pure helpers are. Import of every generator module must succeed without prompting (all prompts under `__main__`/functions).
- Dead code → `archived_code/experiments/` via `git mv`.
- Repo GREEN after ticket: experiments pytest (units+e2e) + ruff + pyright; siblings untouched.

---

### Task 1: `SweepSpec` model + extracted `build_runner_configs`

**Files:**
- Modify: `experiments/src/helpers/runners/model.py` (append `SweepSpec`)
- Modify: `experiments/src/generate_experiment_config.py` (extract `build_runner_configs` from `generate_experiment_config()` body; keep old fn as thin wrapper)
- Test: `experiments/tests/test_generators.py` (new)

**Interfaces:**
- `SweepSpec(StrictModel)`: `mode: Literal["citywide","independent_districts"]`, `root_path: str`, `pattern_groups: list[list[str]] = []`, `solvers: list[SolverSpec]` (reuse T19), `utilities: list[Utility] | None = None`, `concurrency: int = 4`, `experiment_results_base_path: str`, `constraints_configs_path: str | None = None`, `deduplicate_objectives: bool = False`, `output_path: str`.
- `build_runner_configs(paths: list[Path], solvers_with_options: list[tuple[Solver, dict]], utilities: list[Utility] | None, source_type: Source, experiment_results_base_path: str, constraints_configs_path: str | None, deduplicate_objectives: bool) -> list[RunnerConfig]` — pure, cartesian paths × solvers × (utilities or [None]).

- [ ] **Step 1: Write the failing tests** — `SweepSpec` validation (unknown key → ValidationError with loc; minimal valid spec parses); `build_runner_configs` cartesian size (2 paths × 2 solver entries × 2 utilities = 8; utilities None → utility_type omitted → 4); options dict lands in `solver_options`.
- [ ] **Step 2: Run to verify failure** — ImportError on `SweepSpec`/`build_runner_configs`.
- [ ] **Step 3: Implement** — append model; extract helper (mechanical lift of the triple loop; `generate_experiment_config()` calls it).
- [ ] **Step 4: Run** — new tests + full `pytest -q` green (behavior of interactive fn unchanged).
- [ ] **Step 5: Commit** — `git commit -am "T22: SweepSpec model + extracted build_runner_configs"`

---

### Task 2: Sweep entrypoint `generate_sweep_config.py`

**Files:**
- Move: `git mv experiments/src/generate_phragmen_greedy_district_experiment.py experiments/src/generate_sweep_config.py` (then full rewrite — name no longer solver-specific; old content preserved via git history)
- Test: `experiments/tests/test_generators.py` (append)
- Fixture: `experiments/tests/fixtures/sweep-spec.json` (new; points `root_path` at `tests/fixtures/input`, GREEDY + PHRAGMEN×2-options entries — mirrors the old hardcoded sweep shape)

- [ ] **Step 1: Write the failing tests** — `generate_from_spec(spec) -> ExperimentConfig`: on fixture spec → expected runner_configs count; result passes `parse_experiment_config` (already an `ExperimentConfig`); written file re-reads + validates (`main(spec_path)` writes to tmp output_path override — pass spec dict with `output_path` under tmp_path).
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** rewrite:

```python
# generate_sweep_config.py (thin)
def generate_from_spec(spec: SweepSpec) -> ExperimentConfig:
    paths = discover_sources(spec.mode, spec.root_path)
    if spec.pattern_groups:
        paths = filter_paths(paths, spec.pattern_groups)
    return ExperimentConfig(
        concurrency=spec.concurrency,
        experiment_results_base_path=spec.experiment_results_base_path,
        runner_configs=build_runner_configs(
            paths,
            [(s.type, s.options) for s in spec.solvers],
            spec.utilities,
            Source.PABUTOOLS,
            spec.experiment_results_base_path,
            spec.constraints_configs_path,
            spec.deduplicate_objectives,
        ),
    )

def main(spec_path: Path) -> Path:
    spec = SweepSpec.model_validate(read_from_json(spec_path))
    config = generate_from_spec(spec)
    output_path = Path(spec.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_to_json(output_path, config.model_dump(mode="json", exclude_none=True))
    return output_path

if __name__ == "__main__":
    main(Path(sys.argv[1]))
```

(`find_source_paths`/dup `filter_paths` from the old script die — shared helpers imported from `generate_experiment_config`.)

- [ ] **Step 4: Run** — tests green; `grep -rn "resources/" experiments/src --include="*.py"` → empty (T09 leftover closed).
- [ ] **Step 5: Commit** — `git commit -am "T22: sweep generator from SweepSpec json"`

---

### Task 3: Fold compact flow into interactive; archive superseded scripts

**Files:**
- Modify: `experiments/src/generate_experiment_config.py` (`__main__` block)
- Move: `git mv experiments/src/generate_compact_experiment_config.py archived_code/experiments/generate_compact_experiment_config.py`
- Move: `git mv experiments/src/generate_experiment.py archived_code/experiments/generate_experiment.py`

- [ ] **Step 1: Extend interactive `__main__`:**
  - New prompt `questionary.select("Output format:", choices=["full", "compact"])`.
  - New prompt replacing the hardcoded `pattern_groups` placeholder: `questionary.text("Pattern groups (groups ';', patterns ',', blank = all):")` → parse `"krakow,2021;warszawa,2022"` → `[["krakow","2021"],["warszawa","2022"]]`; blank → None. Extract pure `parse_pattern_groups(raw: str) -> list[list[str]] | None`.
  - compact branch: build `CompactExperimentConfig(compact_config=True, concurrency=…, experiment_results_base_path=…, runner_configs_generator=RunnerConfigsGenerator(solvers=[SolverSpec(type=s, options=o) …], source_type=…, sources=[str(p) …], constraints_configs_path=…, deduplicate_objectives=…))` — the whole dup prompt loop in the compact script dies; both formats written via `model_dump(mode="json", exclude_none=True)`.
- [ ] **Step 2: Tests** (append): `parse_pattern_groups` (blank/one group/two groups/stray spaces); import smoke `import generate_experiment_config, generate_sweep_config` runs without prompting.
- [ ] **Step 3: Archive** the 2 superseded scripts (git mv above). Grep: `grep -rn "generate_compact_experiment_config\|generate_experiment\b" experiments/src experiments/tests` → only self/archived refs gone.
- [ ] **Step 4: Run** — full `pytest -q` + ruff + pyright green (archived_code excluded).
- [ ] **Step 5: Commit** — `git commit -am "T22: fold compact flow into interactive generator; archive superseded scripts"`

---

### Task 4: Generate → run verify + PR

- [ ] **Step 1: End-to-end generate→run test** (append to test_generators.py, may mark `@pytest.mark.e2e`-adjacent but keep in default run — GREEDY-only spec on `krakow_2024_mini` is fast): spec w/ solvers=[GREEDY], root=fixtures input dir, results+output under tmp_path → `main(spec_path)` → `experiment_runner.main(read_from_json(generated))` → ≥1 `meta_*.json` produced ("generated config validates + runs" AC, programmatic).
- [ ] **Step 2: Full matrix** — pytest (units+e2e) + ruff + ruff format + pyright green; siblings pytest green.
- [ ] **Step 3: Interactive manual smoke** (session-local, record in PR): run `python src/generate_experiment_config.py`, answer prompts against `sample-experiment/input`, confirm emitted config validates via `parse_experiment_config` for BOTH formats.
- [ ] **Step 4: PR** — push, PR → `feat/roadmap-base-branch`, title `T22: consolidate config generators`. Body: entrypoint map (1 interactive + 1 sweep), archived scripts, SweepSpec schema, pattern-groups prompt replacing placeholder, T09 leftover closed. Update ROADMAP + `plans/leftovers.md` (record sweep-spec fixture path; note old sweep shape recoverable from archived git history).

## Unresolved questions

1. Rename to `generate_sweep_config.py` (2nd rename after T21) — OK, or keep `generate_phragmen_greedy_district_experiment.py` name?
2. `SweepSpec` in `helpers/runners/model.py` next to other config models — OK, or own module (it's generator-only)?
3. Pattern-groups prompt parse format (`;`/`,` separators) — OK?
4. Sweep `source_type` hardcoded PABUTOOLS (only implemented source) — field omitted from SweepSpec deliberately. OK, or add field with single allowed value?

## Steps

1. Task 1: SweepSpec + build_runner_configs extraction (TDD) + commit
2. Task 2: sweep entrypoint rewrite + fixture + commit
3. Task 3: fold compact prompt flow, archive 2 scripts + commit
4. Task 4: generate→run verify, manual interactive smoke, PR, ROADMAP/leftovers update
