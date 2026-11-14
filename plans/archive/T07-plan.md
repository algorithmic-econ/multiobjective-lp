# T07 — Bindings CI in monorepo

## Context
GH #20, #25 (partial). T06 merged bindings as 4th subproject; its `bindings/.github/workflows/wheels.yml` is inert (GH runs only root `.github`). Goal: (1) root wheels workflow (cibuildwheel 3.4.1, ubuntu/macos-15/windows, cp313+cp314, OIDC PyPI) triggered by `bindings@x.y.z` tag; (2) PR-time job building bindings wheel on linux + import smoke; solvers tests run against that artifact. Also fixes T06 leftover: venv cache key ignores bindings C++ edits. No C++/py source changes — CI + docs only.

## Current state (verified)
- `bindings/.github/workflows/wheels.yml`: triggers PR/push-main/release; sdist+3-OS cibuildwheel; upload on `release published`, env `pypi`, OIDC, `attestations: false`. Uses `submodules: true` (none exist — drop).
- Root `.github/workflows/test.yml`: matrix {core,solvers,experiments} × {test,pyright}, py3.13, venv cache key = hash of 3 poetry.locks only. solvers `poetry install` builds bindings from path-dep source.
- `publish.yml`: tags `core@…`/`solvers@…` only; bindings routing stays out (T08 owns publish.yml).
- `bindings/pyproject.toml` v0.0.17, scikit-build-core, `[tool.cibuildwheel] build-frontend = "build[uv]"`.
- `bindings/README.md` Publishing section says "inert, CI wiring in T07".

## Decisions (user-confirmed)
- **Dry run**: temp `push: branches: ['feat/t07-*']` trigger in wheels.yml → verify full matrix on branch → strip trigger in final commit pre-merge.
- **No rc tags** for bindings: upload to PyPI on exact `bindings@X.Y.Z` only; T08 may add rc routing.

## Design

### NEW root `.github/workflows/wheels.yml` (git mv from bindings/.github + adapt)
- Triggers: `workflow_dispatch` + `push: tags: ['bindings@[0-9].[0-9]+.[0-9]+']` (+ temp branch trigger during ticket). Drop PR/push-main/release triggers.
- `validate-tag` job (tag pushes only): regex check + tag version == `bindings/pyproject.toml` version (grep), fail w/ message.
- `build_sdist`: `pipx run build --sdist bindings` + twine check `bindings/dist/*`.
- `build_wheels`: matrix [ubuntu-latest, macos-15, windows-latest], `pypa/cibuildwheel@v3.4.1` with `package-dir: bindings`; keep env block (cp313+cp314, ARM64 windows, MACOSX_DEPLOYMENT_TARGET=14.0, auditwheel), setup-uv, `git diff --exit-code`, upload `wheelhouse/*.whl`. Drop `submodules: true`. Keep concurrency group.
- `upload_all`: `if: startsWith(github.ref, 'refs/tags/bindings@')`, needs build+sdist+validate, environment `pypi`, OIDC → PyPI. workflow_dispatch = build-only dry run (upload skipped).
- Delete now-redundant `bindings/.github/` (content lives at root; git history preserves).

### test.yml changes
- NEW job `build-bindings` (ubuntu, py3.13): `pipx run build --wheel bindings` → `pip install bindings/dist/*.whl` → `python -c "import muoblpbindings; print(muoblpbindings.__doc__)"` smoke → upload artifact `bindings-wheel`.
- `test` + `pyright` jobs: `needs: build-bindings` (small latency for core/experiments, acceptable — keeps single matrix). solvers-only conditional step (`if: matrix.project == 'solvers'`, after poetry install): download `bindings-wheel`, `pip install --force-reinstall` into venv → pytest runs against built artifact instead of path-dep build. experiments stays on path-dep source build (exercises the other install mode).
  - NOTE: pyright matrix does NOT need bindings artifact → `needs` only on `test` job.
- Cache-key fix (T06 leftover): append `hashFiles('bindings/pyproject.toml', 'bindings/CMakeLists.txt', 'bindings/src/**')` to venv cache keys (both jobs) so C++ edits bust solvers/experiments caches.

### Docs
- `bindings/README.md`: Publishing section → workflow now live at root, tag `bindings@x.y.z` → wheels build + PyPI (no rc); drop "inert" note.
- Root `README.md`: publish section adds bindings package + tag convention.

## Out of scope
- publish.yml tag routing / consistency checks for core+solvers → T08. Bindings range pin in solvers metadata → T18. No golden regen; no py source changes.

## Verify
1. Branch `feat/t07-bindings-ci` off `feat/roadmap-base-branch`.
2. Local: `pipx run build --wheel bindings` (needs SDKROOT/CXXFLAGS broken-CLT workaround on this machine) + import smoke — sanity before CI.
3. Push → PR: `build-bindings` job green (wheel + smoke), solvers test green against artifact, core/experiments unchanged, pyright green, cache keys resolve.
4. Full-matrix dry run via temp `feat/t07-*` push trigger: 6 wheels (3 OS × cp313/cp314) + sdist artifacts uploaded, `upload_all` skipped.
5. Strip temp trigger (final commit); actions lint (`gh workflow view` / actionlint if avail).
6. NO tag pushed this ticket — real `bindings@0.0.18` publish happens when bindings next change (or T08 rc rehearsal).

## Leftovers to record
- wheels workflow untested end-to-end for tag-triggered PyPI upload (no tag pushed); first real bindings release verifies. workflow_dispatch from main only available post-roadmap-merge.
- Windows/macos wheel results (any matrix quirks) → note for D14 (cp314 already built).

## Unresolved questions
None — dry-run approach + no-rc confirmed by user.

## Steps
1. Save this plan as `multiobjective-lp/plans/T07-plan.md`.
2. Branch `feat/t07-bindings-ci` off `feat/roadmap-base-branch`.
3. `git mv bindings/.github/workflows/wheels.yml .github/workflows/wheels.yml`; adapt: triggers (dispatch + bindings tag + temp branch), validate-tag job, sdist/cibuildwheel `package-dir: bindings`, upload gate on tag ref; drop submodules; remove empty `bindings/.github`.
4. test.yml: add `build-bindings` job (build wheel, smoke, artifact); `test` job `needs` + solvers wheel-install step; extend cache keys w/ bindings hashes (test+pyright).
5. Update `bindings/README.md` + root `README.md` publish sections.
6. Local sanity: build wheel + import (CLT workaround).
7. Push, open PR → feat/roadmap-base-branch; verify PR jobs green.
8. Trigger full wheels matrix via temp branch trigger; verify 6 wheels + sdist artifacts.
9. Strip temp trigger; final CI green.
10. Append `plans/leftovers.md`; update ROADMAP checkbox on merge.
