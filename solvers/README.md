# Solvers
This package contains all solver implementations and required utility scripts.

---

## Installation
```shell
pip install muoblpsolvers
```
Or use any other package manager.

Alternatively you can install locally (see [Development](#development)).

### C++ python bindings
C++ bindings live in the monorepo subproject [`bindings/`](../bindings/README.md)
(`muoblpbindings`).

## Solvers
PuLP name / class module / experiments `solver_type` / bindings-backed / constructor options:

| PuLP name | Module | `solver_type` | Bindings | Options (defaults) |
|---|---|---|---|---|
| `Greedy` | `greedy_solver.py` | `GREEDY` | no | — |
| `Phragmen` | `phragmen.py` | `PHRAGMEN` | no | `increasing_scalings=False`, `kappa=1.0`, `bos_version=False`, `eps=1e-6` |
| `SummedObjectives` | `summed_objectives_lp_solver.py` | `SUMMING` | no | `use_gurobi=False` |
| `MethodOfEqualSharesExponential` | `mes/mes_exponential.py` | `MES_EXPONENTIAL` | no | `budget_init` (required) |
| `MethodOfEqualSharesConstrains` | `mes/mes_constrains.py` | `MES_CONSTRAINT` | yes | `cost_modification_base=1.007`, `max_iterations=200` |
| `MethodOfEqualSharesAdd1` | `mes/mes_add1.py` | `MES_ADD1` | yes | — |
| `MethodOfEqualSharesUtility` | `mes/mes_utility.py` | `MES_UTILS` | yes | — |
| `SingleTransferableVote` | `single_transferable_vote.py` | `STV` | yes | — |
| `ExpandingApprovals` | `expanding_approvals.py` | `EXPANDING_APPROVALS` | yes | — |
| `SolidCoalitionRefinement` | `solid_coalition_refinement.py` | `SOLID_COALITION_REFINEMENT` | yes | — |

Modules are under `src/muoblpsolvers/`.

## Solver contract
All solvers follow PuLP's `LpSolver` contract:
* **Constructor**: `Solver(msg=True, timeLimit=None, options=None, **solver_options)`;
  solver options are keyword arguments, stored in `optionsDict` and serialized
  by `toDict()`/`toJson()` (`None` kwargs are dropped by PuLP).
* **`available()`**: `True` for pure-python solvers; bindings-backed solvers
  return whether `muoblpbindings` imports (imports are lazy, so
  `import muoblpsolvers` works without bindings).
* **Status**: `actualSolve(lp)` sets `lp.status` and returns it.
* **`msg=False`**: no output during solve.
* **`timeLimit`**: Greedy, Phragmen, MES-Exponential and MES-Constrains
  (coarsely, per iteration) stop early with `LpStatusNotSolved`;
  SummedObjectives passes it to CBC/Gurobi; other bindings-backed solvers
  emit a warning and ignore it.
* **Validation**: all PB solvers (all except SummedObjectives) reject programs
  outside the binary PB shape — no objectives, non 0/1 variables, negative
  utilities or costs — with `PulpSolverError`.
* **Known limitation**: MES-family, STV, ExpandingApprovals and
  SolidCoalitionRefinement ignore lower-bound (`>=`) constraints.

## Example Solver
1. See example [SummedObjectivesLpSolver](src/muoblpsolvers/summed_objectives_lp_solver.py)
2. Solver has to be a class that extends `LpSolver`
3. Solver needs to override method `actualSolve` to accept an instance of `MultiObjectiveLpProblem`, set `lp.status` and return it

## PuLP registration
`import muoblpsolvers` registers all 10 solvers into PuLP's registry, so they
resolve through the standard PuLP API:
```python
import muoblpsolvers  # side effect: registers solvers
import pulp

solver = pulp.getSolver("Phragmen", kappa=2.0)  # any of the 10 names
"Phragmen" in pulp.listSolvers()                 # True
```
Registered names: `ExpandingApprovals`, `Greedy`, `MethodOfEqualSharesAdd1`,
`MethodOfEqualSharesConstrains`, `MethodOfEqualSharesExponential`,
`MethodOfEqualSharesUtility`, `Phragmen`, `SingleTransferableVote`,
`SolidCoalitionRefinement`, `SummedObjectives`.

**Mechanism.** PuLP 3.3.2 drives `getSolver`/`listSolvers` off the module-level
list `pulp.apis._all_solvers` (`getSolver` builds `{cls.name: cls}` from it).
Registration appends our solver classes to that list in place. It runs
automatically on import via `register_solvers()` (also exported for explicit
use); the function is idempotent and only appends classes, so it never
instantiates a solver and stays bindings-free (C++ binding imports are lazy,
inside each solver's `actualSolve`).

## Development
`core` and `bindings` are path dependencies; `poetry install` compiles
bindings from `../bindings` (C++20 toolchain, see
[bindings README](../bindings/README.md)).
```shell
$ cd multiobjective-lp/solvers # package root
$ poetry install
$ poetry run pytest
$ poetry run pyright
$ poetry run ruff check .. && poetry run ruff format --diff ..  # CI ruff version
```
