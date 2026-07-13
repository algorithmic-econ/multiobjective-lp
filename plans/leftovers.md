## Leftovers

Use this file as a memory between sessions that implement independent tasks
---

### From T01 (PR #37, 2026-07-12)

Env / machine state (NOT in repo):
- experiments venv = py3.12 (`poetry env use /opt/homebrew/bin/python3.12`). T04 bumps to 3.13.
- PyPI `muoblpbindings` stale (0.0.16, lacks `expanding_approvals`/`stv`/`scr`) → `import muoblpsolvers` fails from clean install. Workaround baked into current venv: local build of sibling repo `../muoblpbindings` (0.0.17) via `pip install --ignore-requires-python` (repo requires py>=3.13). Any fresh venv before T04/T06 needs same step.
- THIS MACHINE: CommandLineTools broken — toolchain missing `c++/v1` headers, bare `clang++` can't compile hello-world. Bindings build needs `SDKROOT=$(xcrun --show-sdk-path) CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"`. Proper fix: reinstall CLT (`xcode-select --install`, needs user). Affects T06/T07 local verify.

Discovered bugs fixed in T01 beyond plan (context for T02 golden):
- B6: non-dedup objective weights must be int (`1` not `1.0`) — MES bindings take `long long` utilities, pybind rejects float. Dedup path uses `len()` (int) already. If anyone reintroduces float weights/utilities, every MES solve dies with pybind TypeError.
- B7: runner must call `problem.write_lp` (custom, appends OBJECTIVES/WEIGHTS) not pulp `writeLP` — analyzer `read_lp_file` requires those sections. Contract covered by `tests/test_lp_roundtrip.py`.

Deferred (has ticket):
- Analyzer `except → None` swallows real errors (made B7 diagnosis painful) → T24.
- `config/logging_config.yaml` FileNotFoundError noise when scripts run from `sample-experiment/` (relative path from cwd); non-fatal → T20/T09.
- `analysis_table` KeyError `Location-Year` when ALL rows fail regex (empty df) — only partial fix done (ValueError w/ pattern) → T24.
- Stale tracked generated file `sample-experiment/results/sample-analysis/metrics-sample-experiment.jsonc` (old ext; new pipeline writes `.json`, which is untracked) → prune in T09.
- MES_CONSTRAINT/MES_EXPONENTIAL/PHRAGMEN with empty `solver_options` still crash inside `actualSolve` (missing `max_iterations` etc.) → T10/T13.

Facts useful for T02 (golden e2e):
- Sample run: 4 configs (all MES_ADD1), full krakow_2024 = 19 districts, ~2 min wall on this machine; analyze ~1 min.
- Reference metrics from T01 verify run (exclusion_ratio / sum_obj / ejr+): APPROVAL 0.0033/219239/167; COST 0.0035/134763199377/0; COST_ORDINAL 0.0032/279444152847/0; bronowice COST_ORDINAL 0.0666/4351588280/0.
- Meta json `time` field + filename timestamp+uuid are nondeterministic → normalization list (D11).
- pulp preserves int coefficients in `LpAffineExpression` (verified) — int utilities survive to bindings.

Repo conventions observed:
- pre-commit hooks active (ruff, ruff-format, eof, trailing-ws) — commits auto-checked.
- `poetry -C <dir> run` changes cwd → breaks relative-path scripts; `cd` first instead.
- Branch naming used: `feat/t01-fix-pipeline` (existed already; plan's `fix/...` name skipped).

### From T02 (PR #38, 2026-07-12)

- e2e golden: `cd experiments && poetry run pytest -m e2e`; regen `UPDATE_GOLDEN=1 ...` (writes goldens then FAILS by design — inspect + commit separately). Normalization list (D11) in `tests/golden_utils.py`, awaiting confirm in PR #38 review.
- Goldens macOS-generated; C++ MES tie-breaks may differ on Linux CI → surfaces in T03; `sorted(os.listdir)` fix removed main known cause.
- DISCOVERED: GreedySolver `total_utility[candidate]` KeyError on zero-vote candidates (`greedy_solver.py:43`; full krakow never hits it). Fixture avoids via coverage-first ballot pick. Fix in T13 (validation) or T17 (tests).
- DISCOVERED: meta `instance_size`=11 not 10 — pulp `__dummy` passes `problemRunner.py` filter `name != "dummy"` (actual name `__dummy`). Metric INSTANCE_SIZE correct (10). Golden captures 11; fix in T19 (meta remodel) → goldens regen there.
- MES_ADD1 golden has `invalid_count: 1` — Add1 exceeds district cap by design, not a bug.
- `pytest.register_assert_rewrite("tests.golden_utils")` needed in conftest for readable golden diffs (+ E402 per-file-ignore); pattern applies to any future assert-helper module.
- tests/ is a package (relative imports, `tests.golden_utils` module path).

### From T03 (PR #39, 2026-07-12)

Env / machine state (NOT in repo):
- experiments now py3.13; venv `muoblpexp-*-py3.13` (poetry cache, not in-project locally). Lock regenerated → `muoblpbindings` 0.0.17 resolved from **PyPI** (macos-arm64 wheel). T01 local-build-of-sibling-repo hack now OBSOLETE for experiments. Transitive bumps accepted silently (notebook 7.6.0, coverage 7.15.0, etc.).
- core + solvers venvs also recreated on 3.13 (`poetry env use /opt/homebrew/bin/python3.13`). core pyproject still `requires-python >=3.11` (T04 bumps to >=3.13); CI runs 3.13 which satisfies it.
- core got a **dev group** (pytest, pyright) — previously none; core had no tests dir (pytest exit-5). Added `core/tests/test_import.py` smoke test.

pyright suppression inventory (D12 ratchet backlog — all basic mode):
- **core**: 1 inline `# pyright: ignore[reportInvalidTypeForm]` in `multi_objective_lp.py:16` (`sense: LpMaximize|LpMinimize` — pulp consts are ints not types; real fix T27).
- **solvers**: config `reportArgumentType: none` (15 systemic errors — `Utility`/int + float/int + dict-value invariance across mes_add1, mes_constrains, mes_exponential, mes_utility, phragmen). Plus 2 inline: `mes_constrains.py:21` reportOptionalOperand (Optional `constraint.value()`; None-guard T13), `phragmen.py:398` reportReturnType (returns list, annotated set[str]; T16/T27).
- **experiments**: config disables 10 rules (reportArgumentType 31, reportCallIssue 7, reportAttributeAccessIssue 7, reportAssignmentType 7, reportOperatorIssue 6, reportOptionalSubscript 5, reportReturnType 4, reportGeneralTypeIssues 3, reportTypedDictNotRequiredAccess 3, reportInvalidTypeForm 3 = 76 total). Loose pabutools/pandas interop + tests; most files rewritten in Phase 3 (T19 Pydantic, T21 rename, T22/T23 consolidate, T25 dead-code) which should eliminate most — re-enable rules incrementally as Phase 3 lands.

CI (test.yml) notes for T07/future:
- Rewrote: 3-project matrix (core/solvers/experiments) × {test, pyright} jobs, py3.13, `fail-fast: false`. Cache path per-project `${{ matrix.project }}/.venv`, key hashes all 3 locks (path-dep interdependence). No path filters; push trigger limited to `main` + `feat/roadmap-base-branch`; PRs always run.
- **UNVERIFIED locally: Linux CI e2e golden** — goldens macOS-generated; MES C++ tie-break divergence risk (leftovers T02). If ubuntu e2e diffs: normalization fix (`experiments/tests/golden_utils.py`) or switch experiments matrix to `macos-15` + GH issue. NO golden regen.
- `poetry install` runs unconditionally (no cache-hit guard) so editable path-deps (core←solvers←experiments) re-link against checkout.

### From T04 (PR #40, 2026-07-12)

- Trivial ticket — T03 had done most. Only 3 source edits: `core/pyproject.toml` requires-python `>=3.11`→`>=3.13`, `publish.yml:29` setup-python `3.12`→`3.13`, relock ×3.
- Relock diffs MINIMAL, zero transitive bumps: core lock `[metadata] python-versions`→`>=3.13` + content-hash; solvers/experiments only the `muoblp` path-dep `python-versions`→`>=3.13`. (No `poetry install` changes — all venvs already 3.13 from T03.)
- All green locally: pytest core 1 / solvers 13 / experiments 75 (incl e2e golden, no regen), ruff clean, pyright 0 errors ×3. pyright suppression inventory (T03 D12 backlog) unchanged.
- publish.yml change NOT CI-verifiable (tag-triggered) — review-only, rc-tag dry run deferred to T08.

### From T05 (PR feat/t05-pulp-332, 2026-07-12)

- pulp 2.9.0 → 3.3.2 across core+solvers pins; experiments relock-only (transitive). Relock ×3 minimal: only pulp 2.9.0→3.3.2, zero transitive bumps. All green: pytest core 1 / solvers 13 / experiments 75 (incl e2e golden + roundtrip, NO regen), ruff clean, pyright 0×3.
- 2 source fixes: `lp_reader_utils.py` `LpConstraint.from_dict({...constant:-c_rhs, pi})` → `LpConstraint(LpAffineExpression(c_lhs), sense=, name=, rhs=c_rhs)` (from_dict REMOVED in 3.x); `multi_objective_lp.py` +`pulp.set_v4_migration_warnings(False)` after LpCplexLPLineSize monkeypatch (silences all 3.3.x v4 DeprecationWarnings centrally; -W error::DeprecationWarning clean ×3).
- Solve results IDENTICAL post-bump: sample metrics match T01 refs exactly (APPROVAL 0.0033/219239/167; COST 0.0035/1.34763e11; COST_ORDINAL 0.0032/2.79444e11; bronowice 0.0666/4.35159e9). e2e golden unchanged.
- NEW pyright suppression debt (pulp 3.3.2 stubs typed `LpElement.name` + `LpConstraint.value()` as Optional; was green after T04, so all bump-induced) — 6 inline `# pyright: ignore`, all tagged w/ pulp-3.3.2 reason:
  - solvers `mes_constrains.py:34,35` reportOptionalOperand (value()<0/>0; None-guard T13); `election_solver.py:113` reportCallIssue (.get(name)); `common.py:58,59` reportAssignmentType+reportCallIssue (dict[name] comp).
  - experiments `tests/test_constraint_creation.py:276,277` reportOptionalMemberAccess (.name.startswith).
  - Root cause uniform: `name` Optional str → fixable en masse when name-typing addressed (T27-ish). No config-rule changes.
- **pulp-4.0 migration debt** (out of roadmap scope; kill switch masks now): `PULP_CBC_CMD` removal (COIN_CMD switch), direct `LpVariable(...)` ctor + `LpVariable.dicts` + `addVariable(s)`, dict-like `prob.constraints` (→ list API). All heavily used (election_solver, pabutoolsToMoLp, lp_reader_utils, mes/common, phragmen). File GH issue when pulp 4.x targeted.
- Known non-fatal noise unchanged: `config/logging_config.yaml` FileNotFoundError when run from sample-experiment/ cwd (T20/T09); pulp `UserWarning: Spaces not permitted in name` during sample solve (pre-existing, not a Deprecation).
- CI: pushed branch → PR to feat/roadmap-base-branch; Actions unverified locally (Linux e2e tie-break risk per T02/T03 leftovers still applies).

### From T06 (PR feat/t06-merge-bindings, 2026-07-12)

- Squash-imported `../muoblpbindings@89f6b23` (chore/publish-release, v0.0.17) → `bindings/` (4th subproject) via `git archive | tar -x`; dropped stale `poetry.lock`. 17 files. History stays in old repo (user archives GH manually post-merge — NOT done).
- solvers/experiments pin `muoblpbindings="0.0.17"` (PyPI) → path dep `{path="../bindings", develop=false}`; relock ×2 (wheel-files entry → `[package.source] type=directory url=../bindings`, zero transitive change). experiments resolves `../bindings` nested via solvers path dep (like `../core`).
- Fresh solvers venv (`env remove --all; env use python3.13; install`) builds bindings from source via scikit-build-core pip isolation. **macOS broken-CLT workaround REQUIRED** (broken-clt-cpp-headers memory): `export SDKROOT=$(xcrun --show-sdk-path); export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"`. No SDKROOT → build fails (missing c++/v1). Applies to any bindings-building install (solvers, experiments) on this machine + T07 local verify.
- Pre-commit hooks touched imported files (repo-wide, plan-anticipated): eof-fixer trimmed `.clang-format` double-newline; ruff F401 on shim `__init__.py` (re-export names) → added `__all__`; ruff-format reformatted `__init__.pyi` (wrapped multiline sigs). Used solvers-venv ruff 0.15.1 (pins match pre-commit; global ruff is 0.14.0 — mismatch, avoid).
- All green: pytest solvers 13 / experiments 75 (incl e2e golden + roundtrip, NO regen), ruff check+format repo-wide clean (80 files), pyright solvers 0 / experiments 0 (suppression inventory unchanged). `import muoblpbindings` OK, 5 fns exposed.
- **T08 data — path deps NOT vendored, emitted as broken `file://` URLs** (verified `poetry build` solvers on this branch): wheel bundles ONLY `muoblpsolvers/` (no bindings/core code inside). METADATA `Requires-Dist` = `muoblp @ file:///Users/jasiek/.../core` + `muoblpbindings @ file:///Users/jasiek/.../bindings` (both path deps → local file: direct refs, NOT version pins). Wheel UNPUBLISHABLE as-is (PyPI rejects file: direct refs; path absent on user machine). Poetry 2.x does NOT auto-rewrite path dep → version pin (roadmap T08 assumes it should — it currently does not). Fix in T08: force version-pin rewrite for muoblp + muoblpbindings; T18 sets bindings published range `>=0.0.17,<0.1`. Publish order: bindings (PyPI, via T07 wheels) FIRST, then core, then solvers depends by version. Confirms 3 independent PyPI packages — bindings is standalone, path dep is dev-only wiring.
  - Also in that METADATA: `pytest (==8.4.1)` as runtime `Requires-Dist` (should be dev group) → T18.
- Deferred (record for later tickets):
  - bindings `.pyi` imports `pulp` (`from pulp import LpProblem`) but bindings has no declared runtime dep → T18 candidate (add pulp range to bindings metadata, or drop import).
  - CI cache key hashes 3 locks; bindings C++-only edits don't bust it (no lock in bindings) → T07.
  - `bindings/.github/workflows/wheels.yml` inert (GH runs only root `.github`) → T07 ports to root w/ bindings paths + `bindings@x.y.z` tag trigger.
  - root README publish section still lists only core/solvers packageNames; bindings publish deferred to T07 (documented tag convention in bindings/README only).

### From T07 (PR feat/t07-bindings-ci, 2026-07-12)

- `git mv bindings/.github/workflows/wheels.yml .github/workflows/wheels.yml` + adapt; `bindings/.github/` removed. New root `wheels.yml`: triggers `workflow_dispatch` + `push tags bindings@X.Y.Z` + TEMP `push branches feat/t07-*` (dry-run) — **STRIP temp branch trigger (wheels.yml:5-7) before merge**. Jobs: `validate_tag` (regex + tag==pyproject version, tag-ref only), `build_sdist` (pipx build --sdist + twine check), `build_wheels` (ubuntu/macos-15/windows × cp313+cp314, cibuildwheel 3.4.1 `package-dir: bindings`, setup-uv, `git diff --exit-code`, auditwheel linux, ARM64 windows, MACOSX_DEPLOYMENT_TARGET=14.0), `upload_all` (gate `refs/tags/bindings@`, env pypi, OIDC). Dropped `submodules:true` (none). workflow_dispatch = build-only (upload skipped).
- test.yml: NEW `build-bindings` job (ubuntu py3.13, `python -m build --wheel bindings` → install → `import muoblpbindings` smoke → upload artifact `bindings-wheel`). `test` job `needs: build-bindings`; solvers-only steps download artifact + `poetry run pip install --force-reinstall --no-deps ../bindings-wheel/*.whl` (tests run vs built wheel). experiments/core stay path-dep source build. `pyright` job NOT gated on artifact. Cache keys (both jobs) extended: `hashFiles(...,'bindings/pyproject.toml','bindings/CMakeLists.txt','bindings/src/**')` — fixes T06 leftover (C++ edits now bust solvers/experiments caches).
- Local sanity (CLT workaround): `pipx run build --wheel bindings` OK (cp313 macos arm64); fresh py3.13 venv install + `import muoblpbindings` OK. NOTE `muoblpbindings.__doc__` is `None` → CI smoke prints "None" (non-failing, import success is the check). `bindings/dist/*.whl` gitignored (T06).
- System `python3` on this machine = **3.14** — cp313 wheel won't install under it; must use `/opt/homebrew/bin/python3.13` for local wheel smoke.
- READMEs updated (root + bindings/README) publish sections; dropped "inert" note.
- **UNVERIFIED**: no tag pushed → tag-triggered PyPI upload path (validate_tag + upload_all) never exercised; first real `bindings@0.0.18` (or T08 rehearsal) verifies. Full 6-wheel matrix dry-run via temp branch trigger requires push→Actions (not run locally). Windows/macos wheel quirks + cp314 → D14 note.
- Publish order reminder (from T06): bindings PyPI FIRST (this workflow), then core, then solvers by version — relevant to T08.

### From T08 (PR feat/t08-fix-publish, 2026-07-12)

- **Root fix — solvers wheel path-dep → version-pin via Poetry 2.0 dependency enrichment** (T06 `file://` bug): moved version pins into static `[project.dependencies]` (`muoblp>=1.0.4,<2.0`, `pulp==3.3.2`, `muoblpbindings>=0.0.17,<0.1`, `pytest==8.4.1`), dropped `dynamic=["dependencies"]`; `[tool.poetry.dependencies]` reduced to path-only enrich (`muoblp`→`../core` develop, `muoblpbindings`→`../bindings`). Poetry 2.x rule: a dep in BOTH tables uses `[project]` version for wheel METADATA + `[tool.poetry]` path for dev install/lock. Verified METADATA now `muoblp (>=1.0.4,<2.0)` / `muoblpbindings (>=0.0.17,<0.1)`, ZERO `file://`. `poetry lock` REQUIRED after (check fails otherwise); solvers lock changed, experiments lock UNAFFECTED (path-dep hash stable).
- pytest==8.4.1 STILL a runtime `Requires-Dist` (in-scope-boundary: T18 moves to dev group). Version-pinned so satisfies T08 AC; just misplaced.
- Bindings range `>=0.0.17,<0.1` set here (T18 was nominal owner per T06 leftover — now DONE); confirm/adjust in T18 if range policy changes. core range `>=1.0.4,<2.0`.
- **publish.yml changes**: (1) `validate-tag` now checks out + verifies tag version == `<pkg>/pyproject.toml` version (strips `-rc`; mirrors wheels.yml T07). (2) Dropped `poetry install` before `poetry build` (build reads pyproject only — no bindings C++ compile, no core install needed; verified solvers wheel builds w/o SDKROOT). (3) Added `twine check <pkg>/dist/*` metadata gate post-build. (4) `skip-existing: true` on pypa/gh-action-pypi-publish (idempotent re-push, avoids the version-already-exists 400 — chosen over hard-fail). (5) Header comment: `bindings@` tags route to wheels.yml (publish.yml tag filter already core/solvers-only, no code change needed).
- **wheels.yml**: STRIPPED stale `feat/t07-*` temp branch trigger (T07 pre-merge cleanup that was missed — it shipped live on base via PR #43). Now `workflow_dispatch` + `bindings@X.Y.Z` tags only.
- **ROADMAP reconcile**: T07 was merged (PR #43, commit ae5a2a9) but checkbox never flipped — set `[x]` + PR link this session.
- **UNVERIFIED locally** (per T04/T07 pattern — tag-triggered, needs OIDC/test.pypi): actual `solvers@X.Y.Z-rc` / `core@X.Y.Z-rc` push → test.pypi upload + `pip download` METADATA resolution. Review-only. First real rc tag (T08 rehearsal) exercises validate-tag + publish + skip-existing. NOTE: `pip download` of solvers wheel will only resolve if `muoblp`/`muoblpbindings` already on the target index (publish order bindings→core→solvers still holds).
- Local verify GREEN: core 1 / solvers 13 / experiments 75 (incl e2e golden, NO regen), ruff clean ×3, pyright 0 ×3. Wheel metadata: core (pulp==3.3.2, no file://) + solvers (all version-pinned, no file://) `twine check` PASSED. All 3 workflows `yaml.safe_load` OK. validate-tag bash sim: correct MATCH/MISMATCH. System python3 lacks pyyaml — used experiments venv for YAML parse; system python3 = 3.14 (T07 note) so wheel smoke needs 3.13 venv.

### From T09 (PR #45, 2026-07-12)

- Deleted (git rm, NOT archived — user decision, all unreferenced by src/tests): whole `experiments/resources/` (7 abs-path experiment configs incl. invalid `"MES"` solver_type + `no-constraints.json` ext bug — deletion moots both "fix stale configs" bullets; 6 analyzer configs; 2 constraint configs incl. only LB-strategy example `sample-constraints.jsonc` — schema recoverable from `model.py` ConstraintConfig + git history; `warszawa_2023_test/` 5.9MB .pb ×2; 6 tracked generated `analyzer-results/*.json`; 3 .gitkeep) + stale `sample-experiment/results/sample-analysis/metrics-sample-experiment.jsonc` (T01 leftover). ~27 files / ~7MB.
- ROADMAP "~25k file drop" was STALE: root `resources/` (26k files, 4.5G) untracked+ignored since pre-roadmap (last tracked b7ac995). Still on disk locally — user data, NOT touched.
- `.gitignore` consolidated: `/experiments/resources/` (whole dir) replaces 3 piecemeal rules (`**/*.png`, `experiment-results`, stale `/experiments/resources/results/`). Dir stays runtime-writable target for legacy scripts.
- T22/T23 heads-up: generator/aggregator scripts still default-output into deleted `resources/…` paths (`generatePhargmenGreedyDistrictExperiment.py:95` writes `../resources/input/experiment-config/…` — parent dir gone → runtime error until rewrite; `aggregateResults.py:238` `../resources/*.png`). Dir is gitignored so runtime writes harmless.
- logger fix done HERE not T20: `helpers/utils/logger.py` default config path now file-relative (`parents[3]/config/logging_config.yaml`) — kills FileNotFoundError noise when run from `sample-experiment/` (T01 leftover). All callers used default.
- Verify GREEN: experiments 75 pytest (incl e2e golden 1, NO regen), ruff+format clean, pyright 0. AC grep `/Users/jasiek` in *.json* empty. Sample run.sh+analyze.sh pass. core/solvers/bindings untouched (deletion-only ticket) — not re-verified.

### P1 judge verdict (2026-07-12, session post-T09)

- **P1 VERIFIED COMPLETE @047fadb — GO for P2.** Independent green-check: pytest core 1 / solvers 13 / experiments 75 (incl e2e golden), ruff repo-wide clean, pyright 0 ×3, `import muoblpbindings` OK, CI green on base.
- ROADMAP T05/T08 PR links fixed this session (#41, #44).
- Outstanding (non-blocking):
  - **T08/T07 publish paths never exercised end-to-end**: no rc tag pushed (test.pypi via publish.yml) nor `bindings@` tag (wheels.yml upload). Rehearse before first real release; order bindings→core→solvers.
  - Old `algorithmic-econ/muoblpbindings` repo NOT archived on GH (T06 manual follow-up; `isArchived:false`).
  - wheels.yml `workflow_dispatch` dry run triggered this session (closes T07 AC letter) — check outcome if not observed.
  - Cosmetic: solvers `[project.urls]` → `jasieksz/multiobjective-lp`, repo lives at `algorithmic-econ/` → T28.
- D8 (timeLimit on binding-backed solvers) still undecided — must be resolved before T14; T10–T13 unblocked.

### From T10 (PR feat/t10-native-options, 2026-07-13)

- Contract now: options = constructor kwargs → pulp `optionsDict` → serialized via `toDict()`. Solvers read `self.optionsDict[...]`, `self.solver_options`/`self.use_gurobi` GONE. No-option solvers (Greedy, Add1, Utility, STV, SCR, ExpandingApprovals) + ElectionSolver have NO `__init__` — inherit pulp base `(mip=True, msg=True, options=None, timeLimit=None, *args, **kwargs)`.
- Option defaults now in constructors (from generator spec): MES_CONSTRAINT cost_modification_base=1.007/max_iterations=200, PHRAGMEN increasing_scalings=False/kappa=1.0/bos_version=False/eps=1e-6, SUMMING use_gurobi=False. T01 leftover "empty solver_options crash" FIXED for these.
- MES_EXPONENTIAL `budget_init` REQUIRED at solve: None default dropped from optionsDict (pulp filters None kwargs) → `PulpSolverError` in actualSolve (was raw KeyError). T13 folds into shared validation. No numeric default invented (B_init tuning excluded §5).
- SolverOptions TypedDicts (mes_constrains, mes_exponential, phragmen) plain-deleted with migration (user-approved; superseded type decls, not archived).
- `get_solver` = dict dispatch + `**(solver_options or {})` unpack; config `solver_options` dict keys MUST be valid constructor kwargs. Config key `"use-gurobi"` renamed `"use_gurobi"` (generateExperimentConfig.py). T19 Pydantic SolverSpec must keep kwargs-compatible keys; config field name `solver_options` (RunnerConfig/meta/goldens) intentionally UNCHANGED until T19 — AC grep interpreted as solvers/-side clean (verified empty).
- pulp `optionsDict` gotcha: None-valued kwargs silently dropped; False kept. Anyone adding Optional options must read via `.get`.
- Sample smoke needs venv python on PATH: `run.sh`/`analyze.sh` call bare `python` → `PATH="$(poetry -C .. env info --path)/bin:$PATH" ./run.sh`. Also resultCache short-circuits solve — `rm -rf results/*` first for a real smoke (dirs gitignored). Metrics matched T01/T05 refs exactly.
- Verify GREEN: solvers 30 pytest (13→30, +17 contract tests), experiments 80 (75→80, incl e2e golden 1, NO regen), ruff+format clean ×2, pyright 0 ×2, sample e2e values identical. core/bindings untouched.

### From T11 (PR #47, 2026-07-13)

- `available()` on all 10 solvers now truthful (base `LpSolver.available()` raises NotImplementedError — 7 solvers previously inherited it, would've crashed if called). Binding-backed (STV, ExpandingApprovals, SCR, MES-Add1/Utility/Constrains) → `bindings_available()`; pure-python (Greedy, Phragmen via `ElectionSolver` base, Summed, MES-Exponential) → `True`. Removed 3 hardcoded `return True` stubs (STV/EA/SCR).
- NEW helper `muoblpsolvers/utils.py::bindings_available()` = `importlib.util.find_spec("muoblpbindings") is not None`. find_spec locates WITHOUT executing → no C++ init, no SDKROOT/CLT needed for the probe. Checks whole package (per ticket), not per-symbol.
- Lazy imports: 6 top-level `from muoblpbindings import X` moved to first line of each `actualSolve`. `import muoblpsolvers` now succeeds bindings-free (was hard-fail via `__init__` fan-out). Missing bindings now surfaces as ImportError at SOLVE time for binding-backed solvers (not import time) — T13 shared validation may wrap/pre-check via `available()`.
- Missing-bindings unit sim = `monkeypatch.setitem(sys.modules, "muoblpbindings", None)` (idiomatic): makes both `import muoblpbindings` raise AND `find_spec` return None. New `tests/test_available.py` (3 tests): import-without-bindings, available truthful without, available truthful with (skip-if-absent). solvers 30→33.
- Verify GREEN: solvers 33 pytest, experiments 80 (incl e2e golden 1, NO regen), ruff+format clean ×2, pyright 0 ×2 (no new suppressions). Bindings-free subprocess: `sys.modules['muoblpbindings']=None; import muoblpsolvers` → GreedySolver.available() True / STV.available() False. core/bindings untouched.
