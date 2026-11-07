# muoblpbindings

Performance-critical MOLP solver algorithms implemented in C++20, exposed to
Python via pybind11. Built with scikit-build-core + CMake. 4th subproject of the
multiobjective-lp monorepo; consumed by `solvers` as a path dependency, and
by `experiments` for native analysis metrics.

## Build requirements
- C++20 toolchain (gcc/clang/MSVC).
- Python `>=3.13` (CI: 3.13, 3.14; wheels: cp313, cp314).
- CMake + Ninja: auto-provisioned by scikit-build-core during `pip`/`poetry`
  install (build isolation) — no manual install needed.
- pybind11 `>=3`, scikit-build-core `>=0.12` (build-system deps, auto-fetched).

Build happens transparently on `poetry install` in `solvers`/`experiments`
(path dep). No auto-rebuild on C++ edits — re-run install to rebuild.

### macOS broken-CommandLineTools workaround
If bare `clang++` can't find `c++/v1` headers (broken CommandLineTools install):
```sh
export SDKROOT=$(xcrun --show-sdk-path)
export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"
```
Proper fix: reinstall CLT (`xcode-select --install`).

## Core-model-shape contract
`common.cpp` reads the `muoblp` `LpProblem` (core) directly — bindings depend on
this shape implicitly (no compile-time link to core):
- `prob.objectives`: list; each element has `.name` and is iterable as a dict
  `{LpVariable: utility}`. `Utility` is `double` in `common.cpp` (int or float
  accepted); `equal_shares_*` take flattened `long long` utilities — pybind
  rejects float there (non-dedup objective weights must be `1`, not `1.0`).
- `prob.objectives_weights`: `dict[name -> double]`.
- `prob.variables()`, `prob.constraints` (first constraint = budget; budget =
  `-constraint.constant`, per-var cost from constraint dict). Solvers require
  exactly 1 constraint.

`metrics` (`src/metrics/solved_instance.cpp`) reads less, differently:
- `var.varValue` for every variable (`prob.variables()` + objective-only
  variables); `None` → `ValueError`.
- `objective.constant` + objective dict items (pulp order preserved).
- `prob.constraints`: any number tolerated. Per-var cost = constraint coef,
  last write wins over all constraints. PB budget = `abs(constant)` of the
  unique `<=` constraint over all `prob.variables()` (mirrors
  `validate_pb_constraint`); none/many → `ValueError` only from metrics that
  need it (`ejr_plus`). Weights not read.

## Exposed functions
- `equal_shares_utils(...)`, `equal_shares_add1(...)` — Method of Equal Shares.
- `expanding_approvals(prob)`, `single_transferable_vote(prob)`,
  `solid_coalition_refinement(prob)`.
- `metrics.SolvedInstance(prob)` — opaque snapshot of solved problem;
  ro props `num_voters`, `num_candidates`.
- `metrics.exclusion_ratio(instance)` — fraction of voters with objective
  value exactly 0 (bit-identical to python `obj.value() == 0`).
- `metrics.ejr_plus(instance, up_to_one=True)` — number of unelected
  candidates violating EJR+ (up to one); parity with python `ejr_plus`.

See `src/muoblpbindings/__init__.pyi` and `metrics.pyi` for signatures.

## Adding new algorithm
1. Assuming algorithm is named `x`
2. Create `x.cpp` and `x.hpp` files with implementation
3. Bind method in `binder.cpp`
4. Define import and method signature in `__init__.py` and `__init__.pyi`
5. Add and link x.cpp as library in `CMakeLists.txt`
6. Bump project version in `pyproject.toml`

## Adding new metric
1. Assuming metric is named `x`
2. Pure core fn `double metrics::x(const SolvedInstance&)` in
   `src/metrics/x.cpp`, declared in `src/metrics/metrics.hpp` (no pybind/Python
   API inside: runs with GIL released)
3. Need more data? Extend `SolvedInstance` + extraction in
   `src/metrics/solved_instance.cpp`
4. Bind in `binder.cpp` (`metrics_module.def`) with `py::gil_scoped_release`
5. Re-export in `src/muoblpbindings/metrics.py`, add stub in `metrics.pyi`
6. Add `x.cpp` to `metrics` library in `CMakeLists.txt`
7. Bump project version in `pyproject.toml`; relock `solvers` + `experiments`
8. In `experiments`: python oracle + parity pairing in
   `helpers/analyzers/native_metrics.py`

## Publishing
Independent semver from the rest of the monorepo. Tag `bindings@x.y.z`
(must match `pyproject.toml` version) triggers root
`.github/workflows/wheels.yml`: sdist + cibuildwheel (ubuntu/macos-15/windows,
cp313+cp314) → PyPI via OIDC. No rc/test.pypi route. `workflow_dispatch`
runs a build-only dry run (upload skipped). Every PR additionally builds a
linux wheel + import smoke test; solvers CI tests run against that artifact.
