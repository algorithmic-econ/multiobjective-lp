# Multi Objective Linear Programming

---
## Overview
This project provides tools to work with multi objective linear programs, i.e.,
* **muoblp** - package defining model and utils to create MOLPs ([core readme](core/README.md)).
* **muoblpsolvers** - package containing ready to use implementations of MOLP solvers ([solvers readme](solvers/README.md)).
* **experiments** - set of scripts and utils for showcasing usage of solvers on real data and comparing alternative algorithms ([experiments readme](experiments/README.md)).

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
* [Poetry](https://python-poetry.org/docs/) - dependency management, building, publishing
* [Ruff](https://docs.astral.sh/ruff/) - linter and formatter
* [pre-commit](https://pre-commit.com/#intro) - git hooks

## GitHub Workflows

### Code quality checks
Every pushed commit triggers required code quality checks.
The workflow is configured in [ruff.yml](.github/workflows/ruff.yml).

### Publishing packages
Publish workflow is triggered by creating a git tag.

1. Increment project version in `pyproject.toml` file by one to `x.y.z` .
2. To publish a package you need to tag the selected commit.
   * Publish to TestPyPI - use tag pattern: `packageName@x.y.z-rc`
   * Publish to PyPI - use tag pattern: `packageName@x.y.z`
   * Where `packageName` is `core` or `solvers`
