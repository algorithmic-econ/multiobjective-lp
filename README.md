# Multi Objective Linear Programming

---
## Overview
This project provides tools to work with multi objective linear programs, i.e.,
* **muoblp** - package defining model and utils to create MOLPs ([core readme](core/README.md)).
* **muoblpsolvers** - package containing ready to use implementations of MOLP solvers ([solvers readme](solvers/README.md)).
* **experiments** - set of scripts and utils for showcasing usage of solvers on real data and comparing alternative algorithms ([experiments readme](experiments/README.md)).
* **muoblpbindings** - performance-critical solver algorithms implemented in C++20 (pybind11/scikit-build-core), consumed by `solvers` (path dependency in dev, version range when published) ([bindings readme](bindings/README.md)).

## Documentation

Documentation is available at [github.io/multiobjective-lp](https://jasieksz.github.io/multiobjective-lp/) .

For details and installation guide see the READMEs for each package linked above.

* Documentation is created using MkDocs
* To deploy new changes run
    ```shell
    cd documentation
    make deploy-doc
    ```

## Development

### Tools
* [Poetry](https://python-poetry.org/docs/) 2.x - dependency management, building, publishing
* [Ruff](https://docs.astral.sh/ruff/) - linter and formatter
* [Pyright](https://microsoft.github.io/pyright/) - type checking (basic mode)
* [pre-commit](https://pre-commit.com/#intro) - git hooks

### Prerequisites
* Python 3.13, Poetry 2.x
* C++20 toolchain for `bindings` (CMake/Ninja are fetched automatically by scikit-build-core), see [bindings readme](bindings/README.md)

```sh
pre-commit install
```

### Workflow
Each subproject has its own Poetry venv; run commands from its directory.
Dependency chain (path dependencies in dev): `core` ← `solvers` ← `experiments`, `bindings` ← `solvers`.

```sh
cd <core|solvers|experiments> && poetry install && poetry run pytest
poetry run pyright
```

* Ruff version matching CI (0.15.1) lives in the `solvers` dev group:
  `cd solvers && poetry run ruff check .. && poetry run ruff format --diff ..`
* e2e golden test: `cd experiments && poetry run pytest -m e2e`
* End-to-end example: [sample experiment](experiments/sample-experiment/README.md)

## GitHub Workflows

### Code quality checks
Every pushed commit triggers required code quality checks.
The workflow is configured in [ruff.yml](.github/workflows/ruff.yml).

### Tests
[test.yml](.github/workflows/test.yml) runs on pull requests and pushes to `main`:
builds a linux `bindings` wheel (import smoke test), runs `pytest` for
`core`, `solvers` (against the built wheel) and `experiments` (incl. e2e
golden), and `pyright` for each of them.

### Publishing packages
Publish workflow is triggered by creating a git tag.

1. Increment project version in `pyproject.toml` file by one to `x.y.z` .
2. To publish a package you need to tag the selected commit.
   * Publish to TestPyPI - use tag pattern: `packageName@x.y.z-rc`
   * Publish to PyPI - use tag pattern: `packageName@x.y.z`
   * Where `packageName` is `core` or `solvers`
3. Tag must match the `pyproject.toml` version (checked by the workflow);
   already-uploaded versions are skipped.
4. Publish order for dependent releases: `bindings` → `core` → `solvers`.
5. `bindings` publishes via a separate workflow
   ([wheels.yml](.github/workflows/wheels.yml)): tag `bindings@x.y.z`
   (must match `bindings/pyproject.toml` version) builds sdist + multi-OS
   wheels (cibuildwheel, cp313+cp314) and uploads to PyPI. No `-rc` route.
