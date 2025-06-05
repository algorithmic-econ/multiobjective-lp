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
