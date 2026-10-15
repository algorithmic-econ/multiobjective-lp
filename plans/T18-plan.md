# T18 Solvers Pyproject Hygiene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** pytest out of runtime deps (→ dev group); confirm bindings/pulp dep policy; keep `poetry check` clean and wheel METADATA correct.

**Architecture:** Thin ticket — T08 already delivered most of the ROADMAP text: bindings published range + path enrichment, pulp `==3.3.2`, `poetry check` = "All set!". **ROADMAP-wording override (document in PR):** "single poetry style (drop mixed PEP-621/poetry)" is deliberately reinterpreted as KEEPING the hybrid — static `[project.dependencies]` version pins + `[tool.poetry.dependencies]` path enrichment IS the T08 fix (Poetry 2.x rule: a dep in both tables publishes the `[project]` pin in wheel METADATA and dev-installs from the `[tool.poetry]` path). Flipping to pure `[tool.poetry]` style would resurrect the `file://`-in-METADATA bug T08 killed. The one real defect left: `pytest==8.4.1` sits in `[project].dependencies` (lock `groups = ["main"]`) and ships as a runtime `Requires-Dist`.

**Tech Stack:** poetry 2.x, poetry-core masonry, twine (via pipx, optional).

## Global Constraints

- Branch `feat/t18-pyproject-hygiene` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- No dependency-version changes beyond the pytest move: `pulp==3.3.2` (T05), `muoblp>=1.0.4,<2.0`, `muoblpbindings` range stays as found — `>=0.0.17,<0.1`, or `>=0.0.18,<0.1` if T17 (which bumps it) merged first. Do NOT re-bump here.
- dev pytest constraint mirrors core's dev group: `pytest (>=8.4,<9.0)`.
- Repo GREEN after: solvers pytest (pytest itself now from dev group), experiments pytest incl. e2e (NO regen), ruff, pyright.

---

### Task 1: Move pytest to the dev group

**Files:**
- Modify: `solvers/pyproject.toml`, `solvers/poetry.lock` (regenerated)

- [ ] **Step 1: Edit `solvers/pyproject.toml`.** Remove `"pytest==8.4.1",` from `[project].dependencies` (leaving muoblp, pulp, muoblpbindings). Extend `[dependency-groups]`:

```toml
[dependency-groups]
dev = [
    "pytest (>=8.4,<9.0)",
    "ruff (>=0.15.1,<0.16.0)",
    "pyright (>=1.1,<2.0)"
]
```

- [ ] **Step 2: Relock + install**

```bash
cd solvers && poetry lock && poetry install
```

Expected: lock regenerates with pytest `groups = ["dev"]`; install is a no-op or moves pytest's group marker. Then check the sibling: `cd ../experiments && poetry check --lock` — if the solvers path-dep metadata change invalidated it, `poetry lock` there too (T08 precedent says it stays stable, but verify).

- [ ] **Step 3: Verify runtime graph has no pytest**

```bash
cd solvers && poetry show --only main | grep -i pytest || echo "CLEAN"
```

Expected: `CLEAN`. AC-literal check (in-place, reversible):

```bash
poetry sync --only main
poetry run python -c "import pytest" && echo "FAIL: pytest still importable" || echo "OK: pytest gone"
poetry sync   # restore dev group
poetry run pytest -q   # suite still green from dev-group pytest
```

- [ ] **Step 4: Commit** — `git add -A && git commit -m "T18: pytest -> dev group"`

---

### Task 2: Wheel METADATA verification

- [ ] **Step 1: Build + inspect**

```bash
cd solvers && rm -rf dist && poetry build
unzip -p dist/muoblpsolvers-*.whl '*/METADATA' | grep -E '^Requires-Dist'
```

Expected — exactly these (bindings floor per Global Constraints), NO pytest, NO `file://`:

```
Requires-Dist: muoblp (>=1.0.4,<2.0)
Requires-Dist: pulp (==3.3.2)
Requires-Dist: muoblpbindings (>=0.0.17,<0.1)
```

- [ ] **Step 2: `poetry check`** → `All set!`. Optional: `pipx run twine check dist/*` → PASSED (publish.yml runs it anyway, T08).

- [ ] **Step 3: Commit** (only if anything changed; dist/ is gitignored) — else proceed.

---

### Task 3: Document the style decision + PR

**Files:**
- Modify: `solvers/pyproject.toml` (comment only)

- [ ] **Step 1:** Extend the existing T08 comment above `[tool.poetry.dependencies]` so the hybrid reads as policy, not accident:

```toml
# Single-style policy (T18): static [project.dependencies] holds the
# published version pins; this table ONLY enriches them with local path
# sources for dev installs. Poetry 2.x uses [project] for wheel METADATA
# and this table for install/lock — do not move deps back here alone or
# wheels regain broken file:// refs (see T08).
```

- [ ] **Step 2: Full verify** — `cd solvers && poetry run pytest -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright && poetry check`; `cd ../experiments && poetry run pytest -q && poetry run pytest -m e2e -q`; `cd ../core && poetry run pytest -q`.

- [ ] **Step 3: Commit + PR** — `git commit -am "T18: document hybrid pyproject policy"`; push, PR → `feat/roadmap-base-branch`, title `T18: solvers pyproject hygiene`; body: pytest move, METADATA before/after, the ROADMAP-wording override rationale. Update ROADMAP checkbox + PR link; leftovers note: solvers `[project.urls]` still points at `jasieksz/multiobjective-lp` (cosmetic, stays for T28).

## Unresolved questions

None. (If T17 hasn't merged when this executes, the bindings floor is still `0.0.17` — expected values above adjust; nothing else changes.)
