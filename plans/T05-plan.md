# T05 — Bump pulp → 3.3.2

## Context
Roadmap P1, deps T04 done. Current: pulp 2.9.0 exact-pinned in core (`pyproject.toml:15`, PEP-621) + solvers (`pyproject.toml:27`, poetry); experiments has NO direct pulp dep (transitive via core/solvers path deps, locked 2.9.0). pabutools pins `pulp = "*"` — no conflict. Latest stable = **3.3.2** (2026-05-25, py>=3.10); 4.0.0 alphas on PyPI — exact pin excludes them. Verified against pulp 3.3.2 source (GH tag 3.3.2).

Decisions (confirmed w/ user 2026-07-12): exact pin 3.3.2; silence v4-migration warnings centrally; keep PULP_CBC_CMD (COIN_CMD switch = future pulp-4 ticket).

### pulp 2.9 → 3.3.2 audit (verified in source)
**Breaks:**
- `LpConstraint.from_dict` REMOVED (only `fromDataclass` now) → `core/src/muoblp/utils/lp_reader_utils.py:68` crashes. LpConstraint also no longer subclasses LpAffineExpression (has `.expr`), but ctor `LpConstraint(e, sense, name, rhs)` + `.items()/.sense/.constant/.value()/.pi` all intact.

**Still works (no change needed):**
- `pulp.const.LpCplexLPLineSize` monkeypatch (`multi_objective_lp.py:9`): const exists (constants.py:88, default 78), read at call time by `asCplexVariablesOnly`/`asCplexLpConstraint`; `pulp.const` still star-exported.
- `LpProblem.writeLP(filename, writeSOS=1, mip=1, max_length=100)` signature + LP file sections (`Subject To`/`Bounds`/`Binaries`/`End`) unchanged → `write_lp` + `read_lp_file` format contract holds.
- `LpSolver.__init__(mip, msg, options, timeLimit, *args, **kwargs)` unchanged → all 10 solver subclasses fine as-is.
- `LpAffineExpression([(var,coef),...])`, `sorted_keys()`, `setInitialValue`, `variablesDict`, `valid()`, `LpVariable.dicts`, `GUROBI_CMD` — all present.
- Repo does no constraint arithmetic / isinstance-on-LpConstraint (grepped).

**Deprecation noise (3.3.1+ "v4 migration" DeprecationWarnings, module `pulp/v4_migration.py`):** direct `LpVariable(...)` ctor, `LpVariable.dicts`, `addVariable(s)`, dict-like `prob.constraints` (returns `_DeprecatedConstraintsMapping`), `PULP_CBC_CMD` instantiation (coin_api.py:429). All heavily used (election_solver, pabutoolsToMoLp, lp_reader_utils, mes/common, phragmen). Kill switch: `pulp.set_v4_migration_warnings(False)`.

## Changes
1. Pins: core `"pulp == 2.9.0"` → `"pulp == 3.3.2"`; solvers `pulp = "2.9.0"` → `"3.3.2"`. Experiments: no pin to bump — relock only (transitive resolves 3.3.2). `poetry lock && poetry install` ×3 (order: core → solvers → experiments).
2. `core/src/muoblp/utils/lp_reader_utils.py:68-77`: replace `LpConstraint.from_dict({coefficients, constant, name, sense, pi})` with `LpConstraint(LpAffineExpression(c_lhs), sense=c_sense, name=c_name, rhs=c_rhs)` (old `constant: -c_rhs` ≡ `rhs=c_rhs`; drop `pi: -0.0` TODO — defaults None).
3. `core/src/muoblp/model/multi_objective_lp.py`: next to existing `LpCplexLPLineSize` monkeypatch add `pulp.set_v4_migration_warnings(False)` + 1-line comment (4.0 migration out of roadmap scope). Keep monkeypatch as-is.
4. Verify PULP_CBC_CMD warning (coin_api.py:429) is gated by same switch; if it's a plain `warnings.warn`, add targeted `filterwarnings` in the 3 test configs instead — do NOT switch to COIN_CMD.
5. Sweep for surprises: full pytest ×3 with `-W error::DeprecationWarning` once (informational) to inventory any remaining pulp deprecations; fix only breakage, log rest to leftovers.
6. Timebox fallback (per roadmap): newest 2.x IS 2.9.0 — so fallback = revert bump + GH issue with findings. Only if 3.3.2 breaks fundamentally (not expected per audit).

Do NOT touch: solver ctor signatures (T10), available() (T11), status (T12), bindings (T06), publish (T08).

## Verify
- `cd core && poetry run pytest`; solvers; experiments (75 incl. e2e golden — expect IDENTICAL, no regen; pulp bump must not change solve results: golden solvers GREEDY/MES_UTILS/MES_ADD1 use bindings + is_feasible boolean).
- `experiments/sample-experiment/run.sh` + `analyze.sh` smoke.
- Roundtrip contract: `experiments/tests/test_lp_roundtrip.py` (write_lp/read_lp_file vs 3.3.2 writer).
- ruff + pyright ×3 (watch: pyright may flag LpConstraint API drift; suppression inventory in leftovers T03).
- Confirm zero DeprecationWarnings in normal pytest output after silencing.
- PR → `feat/roadmap-base-branch`; Actions green.
- Append findings to `plans/leftovers.md` (incl. pulp-4.0 migration debt note: PULP_CBC_CMD removal, LpVariable/add_variable API, constraints() list API).

## Unresolved questions
- None — pin style (exact 3.3.2), warning handling (central silence), CBC (keep PULP_CBC_CMD) confirmed with user pre-plan.

## Steps
1. Branch `feat/t05-pulp-332` off `feat/roadmap-base-branch`.
2. Bump pins (core, solvers); `poetry lock && poetry install` core → solvers → experiments.
3. Fix `lp_reader_utils.py` LpConstraint construction.
4. Add `set_v4_migration_warnings(False)` to `multi_objective_lp.py`; check PULP_CBC_CMD warning gated, else filterwarnings.
5. pytest ×3 + e2e golden (no regen) + roundtrip + sample run.sh/analyze.sh + ruff/pyright.
6. Deprecation inventory sweep (`-W error::DeprecationWarning`, informational) → leftovers.
7. Update ROADMAP checkbox, append leftovers (+pulp-4.0 debt note), commit, PR → `feat/roadmap-base-branch`, Actions green.
