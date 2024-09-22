# Notes

### 11/09/2024
- [ ] Transform (if possible) election metrics / statistics to general constraint
  - EJR unclear
- [ ] Analyzer module
  - Part of repo not package 
  - Generate MOLP from pabutools format
  - Run solver and save to file
  - Analyze results
    - start with tables / raw numbers
    - graphs later
- [ ] Market based explanations of collectiove decisions, D. Peters


### 11/07/2024
- [x] Implement solver and use actualSolve
    - Allow to inject Gurobi under etc.
- [x] Example dummy solver
    - sum multiobjectives into one objective and run default PULP
- [x] Documentation
- [x] package publishing
- [ ] Implement constrained mes as solver
- [ ] Compare solvers by fairness
- [ ] Criteria module to get metrics about provided solution, e.g:
    - [ ] sum of objectives
    - [ ] count of non zero objective
    - [ ] other examples, proportionality...

### MkDocs Examples

#### Admonitions
???+ info annotate "About (1)"

    Collapsible panel
1.  🚀 I'm an annotation!

!!! warning "Be careful"

#### Graphs
``` mermaid
graph LR
  A[Start] --> B{Error?};
  B -->|Yes| C[Hmm...];
  C --> D[Debug];
  D --> B;
  B ---->|No| E[Yay!];
```

#### LaTeX
The homomorphism $f$ is injective if and only if its kernel is only the
singleton set $e_G$, because otherwise $\exists a,b\in G$ with $a\neq b$ such
that $f(a)=f(b)$.
