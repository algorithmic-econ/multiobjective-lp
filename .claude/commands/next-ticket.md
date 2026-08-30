---
description: Execute the next unsolved ROADMAP ticket end-to-end (branch → plan → implement → verify → PR to base)
---

Execute the next ROADMAP ticket as one session. Base branch = `feat/roadmap-base-branch`. PRs target base, NEVER main. Follow `CLAUDE.md` (concision, poetry venv per project).

## 1. Sync base

- `git -C multiobjective-lp checkout feat/roadmap-base-branch && git -C multiobjective-lp pull`
- If working tree dirty or mid-ticket branch checked out: STOP, report — don't clobber.

## 2. Select ticket

- Read `multiobjective-lp/ROADMAP.md`. Ticket headers: `#### [ ] TXX ...` (open) / `#### [x] ...` (done).
- Pick FIRST open ticket (top-down) whose every `Deps:` ticket is `[x]`.
- **D-gate**: if ticket body says a §6 TODO-decide item blocks it (e.g. T14 "per D8 (blocked until decided)"), and that decision is still open in §6, SKIP to next eligible ticket. If none eligible, STOP and report why.
- Read `multiobjective-lp/plans/TXX-plan.md` — implementiation plan created by high level model, use it as base, some points might become stale since the planning
- Read `multiobjective-lp/plans/leftovers.md` — surface entries relevant to this ticket (env state, deferred bugs pointing here, machine workarounds).

## 3. Branch

- `git -C multiobjective-lp checkout -b feat/tXX-<short-slug>` off base. Slug = 2–3 words from title (see prior names: `feat/t06-merge-bindings`).

## 4. Plan (enter plan mode)

- Enter plan mode. Produce detailed action points from the ticket's bullet list, AC, and Verify recipe. Include: files to touch, verify commands, leftovers to append, any edge cases / D-decisions to confirm.
- End plan with numbered concrete steps + unresolved questions (per CLAUDE.md plan rules).
- ExitPlanMode → wait for user approval before implementing. Do not implement in plan mode.

## 5. Implement

- Work the approved steps. No new features (ROADMAP §5). Dead code → `archived_code/`, never plain-deleted.
- Regenerate golden files ONLY if ticket explicitly allows; if so, separate commit + justification.

## 6. Verify (repo must be GREEN)

Per touched subproject (`core`/`solvers`/`experiments`/`bindings`):

- `cd multiobjective-lp/<proj> && poetry install && poetry run pytest`
- ruff + pyright (basic) per project
- e2e golden: `cd multiobjective-lp/experiments && poetry run pytest -m e2e` (no regen)
- Sample smoke if ticket touches pipeline: `experiments/sample-experiment/run.sh` + `analyze.sh`
- Machine notes: broken CLT → bindings builds need `SDKROOT`/`CXXFLAGS` (see leftovers T06 / broken-clt-cpp-headers memory). Use the project's py3.13 venv.
- If not all green: fix or STOP and report. Do not open PR on red.

## 7. Record leftovers

- Append `### From TXX (PR <branch>, <today>)` section to `multiobjective-lp/plans/leftovers.md`: env/machine state, bugs found beyond plan, deferred items + which ticket owns them, facts useful downstream, new pyright suppressions.
- Update ROADMAP ticket: `[ ]`→`[x]`, fill PR link. Commit.

## 8. PR + stop

- Push branch. `gh pr create --base feat/roadmap-base-branch --head feat/tXX-<slug>` with concise title + body (what/AC status/verify results/leftovers highlights). End body with:
  🤖 Generated with [Claude Code](https://claude.com/claude-code)
- Print PR URL. STOP. Tell user: review & merge, then start a fresh session and run `/next-ticket` again.

Do NOT auto-merge. Do NOT start the next ticket in this session.
