# T32 py3.14 in CI matrix — Implementation Plan

> Implementer input. Planned 2026-09-27 against `968db3a`.

**Goal:** CI test + pyright run on py3.13 AND 3.14; D14 closed as adopted. Refactor-only: no src changes expected.

**Context:** Last open roadmap ticket (P5). D14 carried since T07 (wheels.yml already builds cp313+cp314; PyPI bindings 0.0.18 ships cp314 wheels). `test.yml` hardcodes 3.13 at `:22,:55,:104` + cache keys `py3.13` at `:68,:117`.

## User decisions (binding)

1. **D14 = adopt.** 3.14 added to CI.
2. **Scope = test + pyright** (both matrices), plus `build-bindings` per python version (solvers tests run vs matching-ABI wheel).

## Global constraints

- Branch `feat/t32-py314-matrix` off `feat/roadmap-base-branch`; PR → base. Never main.
- No golden regen. If 3.14 e2e diffs vs golden → STOP + report (no normalization hacks without user OK).
- Exact-pin style in experiments kept (`pandas = "2.3.3"`, not ranges).
- ruff: solvers venv ruff 0.15.1 (global 0.14 mismatch).
- Machine: bindings source build needs `export SDKROOT=$(xcrun --show-sdk-path); export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"`. Interpreters: `/opt/homebrew/bin/python3.13`, `/opt/homebrew/bin/python3.14` (system `python3` = 3.14.6 via pyenv).
- Do NOT switch the repo's own 3.13 poetry venvs to 3.14 — do 3.14 verify in scratch clone.

## Verified live facts (2026-09-27)

- `requires-python = ">=3.13"` in all 4 pyprojects (no upper cap) → locks already resolve for 3.14; no pyproject python change needed.
- Compiled deps in locks w/o cp314 wheel (would source-build on 3.14 → pandas meson/cython build, slow/fragile):
  - experiments `pandas 2.3.1` (exact pin `experiments/pyproject.toml:33`) → **2.3.3** (first w/ cp314 wheels).
  - experiments `pyyaml 6.0.2` (exact pin `:35`) → **6.0.3**.
- All other compiled deps already have cp314 wheels: numpy 2.5.1, pydantic-core 2.46.4, matplotlib 3.10.8, contourpy, kiwisolver, fonttools, pillow, gmpy2, coverage. solvers `ruff` = platform `py3-none` wheel (fine). core: pure only. pulp 3.3.2 pure + bundled CBC.
- bindings: `pybind11>=3`, scikit-build-core — cp314 already built by wheels.yml.
- pyrightconfigs ×3: no `pythonVersion` → pyright uses venv interpreter version → 3.14 run genuinely checks vs 3.14 stubs.
- `publish.yml:41` setup-python 3.13 builds pure wheels only → leave. `ruff.yml` no python → leave. `wheels.yml` unchanged.
- Lock-scan script (reuse): parse `poetry.lock` via `tomllib`, per package list `.whl` files, flag any non-`none-any` pkg lacking `cp314` / `abi3` / `py3-none-<plat>` wheel.

---

### Task 1: Branch

- [ ] `git checkout feat/roadmap-base-branch && git pull && git checkout -b feat/t32-py314-matrix`. Stop if dirty.
- [ ] Check required status checks on base (matrix renames job checks, e.g. `test (core)` → `test (core, 3.13)`): `gh api repos/algorithmic-econ/multiobjective-lp/branches/feat%2Froadmap-base-branch/protection` + same for `main`. If required checks listed → report names to user in PR body (user updates settings; agent does NOT edit protection).

### Task 2: Dep bumps for cp314 wheels

**Files:** `experiments/pyproject.toml`, `experiments/poetry.lock`

- [ ] `pandas = "2.3.3"`, `pyyaml = "6.0.3"`. `cd experiments && poetry lock`.
- [ ] Diff old/new lock as name→version maps (T28 method, not `git diff`): expect ONLY pandas + pyyaml changed (+ at most pandas-exclusive transitives, e.g. tzdata). Anything else bumped → revert, retry `poetry lock` (poetry 2.2.1 keeps locked); if unavoidable STOP + report.
- [ ] Re-run lock-scan on core/solvers/experiments locks → zero cp314 gaps.
- [ ] `poetry sync` → `poetry check --lock` → `poetry run pytest` (incl e2e, NO regen, `git status tests/` clean) + `poetry run pyright` on 3.13.
- [ ] Sample smoke on 3.13 (`cd sample-experiment && rm -rf results/* && poetry run sh run.sh && poetry run sh analyze.sh`) → metrics EXACT frozen refs: APPROVAL 0.0033/219239/167; COST 0.0035/1.34763e11/0; COST_ORDINAL 0.0032/2.79444e11/0; bronowice 0.0666/4.35159e9/0 (pandas bump touches analysis path).
- [ ] Commit `T32: pandas 2.3.3, pyyaml 6.0.3 (cp314 wheels)`.

### Task 3: test.yml matrix

**Files:** `.github/workflows/test.yml`

- [ ] `build-bindings`: `strategy.matrix.python: ["3.13", "3.14"]`; setup-python `${{ matrix.python }}`; artifact name `bindings-wheel-py${{ matrix.python }}`.
- [ ] `test`: matrix `project: [core, solvers, experiments]` × `python: ["3.13", "3.14"]`; setup-python `${{ matrix.python }}`; cache key `venv-${{ runner.os }}-py${{ matrix.python }}-${{ matrix.project }}-…` (rest unchanged); download artifact `bindings-wheel-py${{ matrix.python }}`. `needs: build-bindings` unchanged (waits all legs).
- [ ] `pyright`: same 2-axis matrix + cache key.
- [ ] Keep `fail-fast: false`. No other workflow edits.
- [ ] `yaml.safe_load` sanity (experiments venv has pyyaml).
- [ ] Commit `T32: CI matrix py3.13 + py3.14`.

### Task 4: Local 3.14 verify (scratch clone)

- [ ] `git clone <repo> $SCRATCH/t32-clone && git checkout feat/t32-py314-matrix`; CLT env vars exported.
- [ ] Per project core → solvers → experiments: `poetry env use /opt/homebrew/bin/python3.14 && poetry install && poetry run pytest && poetry run pyright`. Experiments incl `-m e2e` golden (NO regen). Expect counts core 16 / solvers 127 / experiments 194, 0 skipped bindings tests, pyright 0 ×3.
- [ ] Note any new 3.14-only DeprecationWarnings (record, don't fix unless test-failing).
- [ ] Any failure → fix only if trivially version-compat (no behavior change); else STOP + report.
- [ ] Cleanup: `poetry env remove --all` in each clone project, delete clone.

### Task 5: Docs

- [ ] `git grep -n "3\.13" -- '*.md'` (skip `plans/`, `ROADMAP.md`, `documentation/`, `papers/`) → where READMEs state python requirement, say "3.13+ (CI: 3.13, 3.14)". Root README "GitHub Workflows" test.yml bullet: mention py matrix. Minimal edits.
- [ ] Commit `T32: docs py3.14`.

### Task 6: ROADMAP + leftovers

- [ ] ROADMAP T32 `[x]` + PR link + short "From T32 session" note (decisions, bumps, job-name change). §6 D14 → `DECIDED (T32): adopt — test + pyright matrix 3.13+3.14; pandas 2.3.3 / pyyaml 6.0.3 for cp314 wheels`. §3 P5 line fine as-is.
- [ ] Append `### From T32 (PR #…, feat/t32-py314-matrix, <date>)` to `plans/leftovers.md`: lock diff summary, 3.14 local results + warnings, CI job count (build 2 / test 6 / pyright 6), required-checks finding, "roadmap complete → base→main PR next (paste §7 Closes block)".
- [ ] Commit.

### Task 7: PR + CI

- [ ] Push, `gh pr create --base feat/roadmap-base-branch --head feat/t32-py314-matrix`, title `T32: py3.14 in CI matrix (D14)`; body what/AC/verify + required-checks note; end with Claude Code attribution.
- [ ] Watch Actions (PR trigger): all 14 jobs green. Record run id in leftovers (amend via follow-up commit). STOP.

## AC

- CI green on 3.13 + 3.14 for test (core/solvers/experiments incl e2e golden) + pyright ×3.
- Only pandas/pyyaml (+ exclusive transitives) changed in locks; golden identical; sample smoke exact refs.
- D14 closed in §6; T32 `[x]`.

## Unresolved questions

1. Branch protection required checks (if any) change names with matrix — OK for you to update settings manually? (Plan: agent reports, doesn't touch.)
2. 3.14 golden diff (unlikely, same pkg versions): STOP vs regen per-version goldens? (Plan: STOP.)
3. Add `Programming Language :: Python :: 3.13/3.14` classifiers to core/solvers/bindings? (Plan: no — metadata change → release churn; out of scope.)
4. CI time ~2× (14 vs 7 jobs). Acceptable, or 3.14 on push-to-base only? (Plan: every PR.)

## Steps

1. Branch; check required status checks.
2. Bump pandas 2.3.3 / pyyaml 6.0.3, relock, verify lock diff + 3.13 green + sample refs.
3. test.yml: python matrix on build-bindings/test/pyright, per-version artifact + cache key.
4. Scratch-clone 3.14 verify: pytest + e2e + pyright ×3.
5. README python-version touch-ups.
6. ROADMAP T32 `[x]`, D14 decided; leftovers entry.
7. PR → base, watch 14 jobs green, stop.
