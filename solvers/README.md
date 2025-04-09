# Solvers
This package contains all solver implementations and required utility scripts.

---

## Installation

### Temporary Disclaimer
This package has to be used locally until C++ bindings can be compiled for most common architectures (in progress).

Preferably install locally using Poetry, see example in `experiments` package.
```yaml
[tool.poetry.dependencies]
muoblpsolvers = {path = "${relativePathToSolversDirectory}", develop = true}
```
Alternatively using pip
```shell
$ cd multiobjective-lp/solvers # package root
$ pip install -e .
```

## Solver
1. See example [SummedObjectivesLpSolver](src/muoblpsolvers/summed/SummedObjectivesLpSolver.py)
2. Solver has to be a class that extends `LpSolver`
3. Solver needs to override method `actualSolve` to accept an instance of `MultiObjectiveLpProblem`

## Prepare C++ python bindings
To use solvers that rely on C++ bindings you need to build them first on your machine.

```shell
$ cd multiobjective-lp/solvers # package root
$ ./prepare_bindings.sh
```
