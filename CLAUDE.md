- In all interactions and commit messages, be extemely concise and sacrifice grammar for the sake of concision.

## Plans
- When writing plans, be extremely concise. Sacrifice grammar for the sake of concision.
- At the end of each plan, give me a list unresolved questions to answer if any. Ask about edge cases, error handling, and unclear requirements before proceeding.
- End every plan with a numbered list of concrete steps. This should be the last thing visible in the terminal.

## Repository structure
- multiobjective-lp is python monorepo, with three projects
  - core - defines model of multiobjective linear program
  - solvers - independent set of algorithms that can be applied to solve an instance of multiobjective LP, sometimes with C++ bindings
  - experiments - scripts and utilities to generate, solve and analyse instances of multiobjective LPs
