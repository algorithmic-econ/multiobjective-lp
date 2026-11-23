# fix-mes-weights: native MES ignores voter weights

> **FIRST ACTION when implementing:** call AskUserQuestion with every item
> under "Unresolved questions". Do not write code until answered. Record
> answers in a "Decisions (session)" section of this file.

## Context
Found while validating metric-00 (PR #76) on
`experiments/resources/experiment-results/independent-waw-krk{,-dedup}`
(162 runs each; dedup: 766,767 objectives, Σw = 1,089,120 = non-dedup
voter count). Dedup must not change any solver outcome (weight-w voter ==
w identical voters), but:
- MES_ADD1: 50/54 instances select differently; EJR+ (up to one) 0 → up to
  7 violations (impossible for real MES) → dedup MES results invalid
- PHRAGMEN: 1/54 differs (probably tie-break; check)
- GREEDY: 0 differ

Cause: native MES (`bindings/src/mes_utils.cpp`, `mes_add1.cpp`) gets
`list(voters.keys())` (ids only, see `# TODO: weight-aware via binding
update` in `solvers/src/muoblpsolvers/mes/{mes_add1,mes_utility,
mes_constrains}.py`). Only `total_utility` is weighted
(`mes/common.py:76`). Affected solvers: MES_UTILS, MES_ADD1,
MES_CONSTRAINTS. Not affected: MES_EXPONENTIAL (python, weighted), GREEDY,
PHRAGMEN, EA/STV/SCR (`common.cpp` `voter_weights`).

## Weighted MES semantics (= w copies, each own budget b_v)
Reference pattern: `mes/mes_exponential.py:55-150`. W = Σ w_v.
- init `b_v = B / W` (was `B / voters.size()`)
- affordability `money_behind = Σ w_v·b_v`
- payment loop: if `ρ·u_v > b_v`: `paid += w_v·b_v`, `denom -= w_v·u_v`
  (`denom` starts at weighted `total_utility`)
- deduction per copy unchanged: `b_v -= min(ρ·u_v, b_v)`
- ADD1: integral start `floor(B / W)·W`; step `+ W` (was `voters.size()`)
- w ≡ 1 → bit-identical to current (goldens unchanged)

## Changes
- `bindings/src/mes_utils.cpp`, `mes_add1.cpp`, `methods.hpp`,
  `binder.cpp`, `muoblpbindings/__init__.pyi`: `voters` becomes
  `dict[str, float]` (id → weight) instead of `list[str]`
- `solvers/.../mes/{mes_add1,mes_utility,mes_constrains}.py`: pass
  `voters` dict; drop TODOs
- bindings bump (next version), relock solvers + analyzers + experiments
- `bindings/README.md`: MES weight semantics

## Tests (`solvers/tests/`)
- invariance: weighted problem vs expanded (duplicated voters, no weights)
  → same selection, for MES_UTILS, MES_ADD1, MES_CONSTRAINTS; handcrafted
  + random seeds (random weights 1-3, ints; reuse analyzers
  `make_random_problem` idea)
- hand-computed weighted case where ignoring weights changes outcome
  (e.g. a w=3 bloc affords a project only when weighted)
- existing tests unchanged (w=1)
- optional oracle: pabutools MES on equivalent `MultiProfile`
  (experiments env has pabutools)

## Verification
- `cd solvers && poetry install && poetry run pytest && poetry run ruff
  check . && poetry run pyright`
- `cd experiments && poetry run pytest && poetry run pytest -m e2e`
  (goldens no dedup → unchanged)
- data: rerun `resources/independent-waw-krk-dedup.jsonc` experiment +
  analyzer (all metrics, script pattern: run_analysis.py w/ `__main__`
  guard; pool spawn re-imports script). Expect: MES_* selections == non-dedup
  run (modulo documented ties); MES EJR+ violations 0
- `cd analyzers && poetry run pytest` (relock sanity)

## Unresolved questions
- base branch: `main` (solver bug, independent) or
  `feat/pabulib-metrics-base`?
- `Utility = long long` in MES bindings: weighted `total_utility` is float
  when weights are non-int (or `3.0` after LP read) → pybind TypeError.
  Switch MES utilities to `double`, or require int weights for MES (raise
  clear error)?
- `remaining[candidate] = eff_vote_count` stores a double into
  `unordered_map<CandidateId, Utility>` (long long) → truncation; fix in
  same PR (may change w=1 outcomes/goldens) or separate ticket?
- tie-break `choices[0]` over `unordered_map` iteration order → can differ
  dedup vs expanded; make deterministic (e.g. by name) here, or accept
  ties as known divergence in invariance tests?
- PHRAGMEN 1 diff: investigate in this plan or separate?

## Steps
1. AskUserQuestion (unresolved questions); record decisions
2. Branch `fix/mes-weights` off chosen base
3. C++ weighted MES utils + add1, binding signature, pyi
4. Python callers pass weights; drop TODOs
5. Invariance + hand-computed tests; existing tests green
6. Bump bindings, relock 3 projects, rebuild
7. Verification block incl. waw-krk dedup rerun + comparison
8. Docs (bindings README, metrics-index warning → resolved); commit, PR →
   base; stop, wait for review

## Decisions (session)
- base: `feat/pabulib-metrics-base`; branch `fix/mes-weights`
- types: utilities stay `long long`; weights `double`; `total_utility` →
  `double` (weighted, computed in python)
- `remaining` long long truncation: separate ticket (leftovers)
- tie-break `choices[0]`: keep; invariance tests tie-free; ties documented
  as known divergence
- PHRAGMEN 1/54 dedup diff: separate ticket (leftovers)
