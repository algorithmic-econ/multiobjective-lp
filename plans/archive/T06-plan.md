# T06 — Merge muoblpbindings into monorepo

## Context
GH #20. Bindings (pybind11/C++20/scikit-build-core, PyPI `muoblpbindings` 0.0.17) live in sibling repo `../muoblpbindings`. Merge as 4th subproject `bindings/`; solvers switches PyPI pin → path dep. History stays in old repo (user archives on GH after merge). Refactor-only; repo must stay GREEN. CI wiring for bindings = T07 (not here). Publish-time range pin = T18.

## Source state (verified)
- Sibling repo clean on `chore/publish-release` @89f6b23 (vs `main`: only 1-line wheels.yml diff, publish-on-release — newer, use it). 18 tracked files; `.venv/ wheelhouse/ .cache/ .idea/ .DS_Store` untracked/gitignored.
- pyproject: scikit-build-core backend, v0.0.17, py>=3.13, build reqs scikit-build-core>=0.12 + pybind11>=3, no runtime deps. CMake: C++20, static lib `methods` (6 cpp), `python_add_library(muoblpbindings MODULE ... WITH_SOABI)`.
- `poetry.lock` stale/empty (drop per ticket). No tests dir.
- `common.cpp:53-75` contract on core model: `prob.objectives` list, each elem `.name` + iterable as dict {LpVariable: utility→`long long`}; `prob.objectives_weights` dict[name→double]; also `prob.variables()`, `prob.constraints`, budget from constraint `.constant`.
- Monorepo on `feat/roadmap-base-branch`, clean. solvers/pyproject: `muoblpbindings = "0.0.17"`. experiments: bindings only transitive via solvers.

## Decisions
- **Import**: `git -C ../muoblpbindings archive chore/publish-release | tar -x -C bindings/` — tracked files only, junk auto-excluded. Then `rm bindings/poetry.lock`. Single commit `chore(bindings): squash-import muoblpbindings@89f6b23 (v0.0.17)`.
- **wheels.yml**: keep inert at `bindings/.github/workflows/wheels.yml` (GH ignores non-root .github) as T07 reference.
- **Path dep**: `muoblpbindings = {path = "../bindings"}` develop=false — editable useless for C++ ext (no auto-rebuild, redirect shim quirks). Nested resolution from experiments proven by existing `../core` pattern.
- **CI untouched**: ubuntu `poetry install` builds bindings via pip isolation (scikit-build-core auto-provisions cmake/ninja, gcc present). Cache key hashes 3 locks → this PR busts it. Future C++-only-change cache staleness → T07.
- **ruff.yml risk**: `ruff check --fix` + `ruff format --diff` steps run repo-wide → bindings' 2 shim .py files linted (default config, no [tool.ruff] in bindings). Lint/format-check locally pre-push; also pre-commit hooks (eof, trailing-ws) may touch imported files — let them, include in import commit if trivial.

## Files
- NEW `bindings/` (17 files post-lock-drop) + rewritten `bindings/README.md`
- `solvers/pyproject.toml` (pin→path dep), `solvers/poetry.lock`, `experiments/poetry.lock` (relock: PyPI wheel entry → directory source)
- root `README.md` + `CLAUDE.md` (3→4 subprojects)

## bindings/README.md outline
Build reqs (C++20 toolchain, cmake auto-provisioned, py>=3.13); macOS broken-CLT workaround `SDKROOT=$(xcrun --show-sdk-path) CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"`; core-model-shape contract (common.cpp reads `.objectives`/`.objectives_weights` as above); utilities must be int (`Utility` = long long, pybind rejects float — leftovers B6); exposed fns (equal_shares_add1/utils, expanding_approvals, single_transferable_vote, solid_coalition_refinement); keep existing "adding new algorithm" checklist; tag convention `bindings@x.y.z` (CI in T07).

## Verify
1. Fresh solvers venv: `cd solvers && poetry env remove --all; poetry env use python3.13 && poetry install` (with SDKROOT/CXXFLAGS workaround) → builds bindings from `../bindings`.
2. `poetry run python -c "import muoblpbindings"` + `poetry run pytest` (13 tests).
3. `cd experiments && poetry install && poetry run pytest` (75 incl e2e golden, NO regen) .
4. ruff check + format --diff repo-wide (0.15.1); pyright solvers+experiments (suppression inventory unchanged).
5. Push branch → PR to `feat/roadmap-base-branch`; watch Actions (test matrix builds bindings on ubuntu — Linux e2e tie-break risk from T02/T03 leftovers still applies).
6. Post-merge (user, manual): archive old GH repo.

## Leftovers to record (plans/leftovers.md)
- bindings `.pyi` imports pulp but no declared runtime dep — not fixed (refactor-only); T18 candidate.
- CI cache won't bust on bindings C++ changes (no lock) → T07.
- wheels.yml inert in bindings/.github → T07 ports to root.

## Unresolved questions
None blocking. Assumptions: import source = `chore/publish-release` (newest, matches published 0.0.17); path dep develop=false. Flag if you prefer `main` or editable.

## Steps
1. Branch `feat/t06-merge-bindings` off `feat/roadmap-base-branch`.
2. `git archive` import → `bindings/`, drop `poetry.lock`, commit squash-import.
3. Rewrite `bindings/README.md` (outline above).
4. solvers/pyproject.toml: pin → `{path = "../bindings"}`; `poetry lock`.
5. `poetry install` solvers (SDK workaround) + import check + pytest.
6. experiments: `poetry lock` + install + pytest incl e2e golden.
7. Update root README.md + CLAUDE.md → 4 subprojects.
8. ruff/pyright/format checks repo-wide.
9. Append leftovers.md; commit; PR → feat/roadmap-base-branch; verify Actions.
