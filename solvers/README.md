# Solvers
This package contains all solver implementations and required utility scripts.

---

## Installation
```shell
pip install muoblpsolvers
```
Or use any other package manager.

Alternatively you can install locally.
```shell
$ cd multiobjective-lp/solvers # package root
$ pip install -e .
```

### Implement C++ python bindings
C++ bindings are implemented in standalone project [muoblpbindings](https://github.com/jasieksz/muoblpbindings)

## Example Solver
1. See example [SummedObjectivesLpSolver](src/muoblpsolvers/summed/SummedObjectivesLpSolver.py)
2. Solver has to be a class that extends `LpSolver`
3. Solver needs to override method `actualSolve` to accept an instance of `MultiObjectiveLpProblem`

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
