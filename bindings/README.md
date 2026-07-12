# muoblpbindings

Performance-critical MOLP solver algorithms implemented in C++20, exposed to
Python via pybind11. Built with scikit-build-core + CMake. 4th subproject of the
multiobjective-lp monorepo; consumed by `solvers` as a path dependency.

## Build requirements
- C++20 toolchain (gcc/clang/MSVC).
- Python `>=3.13`.
- CMake + Ninja: auto-provisioned by scikit-build-core during `pip`/`poetry`
  install (build isolation) — no manual install needed.
- pybind11 `>=3`, scikit-build-core `>=0.12` (build-system deps, auto-fetched).

Build happens transparently on `poetry install` in `solvers` (path dep). No
auto-rebuild on C++ edits — re-run install to rebuild.

### macOS broken-CommandLineTools workaround
If bare `clang++` can't find `c++/v1` headers (broken CLT on this machine):
```sh
export SDKROOT=$(xcrun --show-sdk-path)
export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"
```
Proper fix: reinstall CLT (`xcode-select --install`).

## Core-model-shape contract
`common.cpp` reads the `muoblp` `LpProblem` (core) directly — bindings depend on
this shape implicitly (no compile-time link to core):
- `prob.objectives`: list; each element has `.name` and is iterable as a dict
  `{LpVariable: utility}`. **Utilities must be int** — `Utility` is `long long`;
  pybind rejects float (non-dedup objective weights must be `1`, not `1.0`).
- `prob.objectives_weights`: `dict[name -> double]`.
- `prob.variables()`, `prob.constraints` (first constraint = budget; budget =
  `-constraint.constant`, per-var cost from constraint dict).

## Exposed functions
- `equal_shares_utils(...)`, `equal_shares_add1(...)` — Method of Equal Shares.
- `expanding_approvals(prob)`, `single_transferable_vote(prob)`,
  `solid_coalition_refinement(prob)`.

See `src/muoblpbindings/__init__.pyi` for signatures.

## Adding new algorithm
1. Assuming algorithm is named `x`
2. Create `x.cpp` and `x.hpp` files with implementation
3. Bind method in `binder.cpp`
4. Define import and method signature in `__init__.py` and `__init__.pyi`
5. Add and link x.cpp as library in `CMakeLists.txt`
6. Bump project version in `pyproject.toml`

## Publishing
Independent semver from the rest of the monorepo. Tag `bindings@x.y.z`
(must match `pyproject.toml` version) triggers root
`.github/workflows/wheels.yml`: sdist + cibuildwheel (ubuntu/macos-15/windows,
cp313+cp314) → PyPI via OIDC. No rc/test.pypi route. `workflow_dispatch`
runs a build-only dry run (upload skipped). Every PR additionally builds a
linux wheel + import smoke test; solvers CI tests run against that artifact.
