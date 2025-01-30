# Solvers
This package contains all solver implementations and required utility scripts.

---

## Solver
1. See example [SummedObjectivesLpSolver](summed/SummedObjectivesLpSolver.py)
2. Solver has to be a class that extends `LpSolver`
3. Solver needs to override method `actualSolve` to accept an instance of `MultiObjectiveLpProblem`


## Prepare C++ python bindings
```shell
$ cd multiobjective-lp # repository root
$ ./solvers/prepare_bindings.sh
```
