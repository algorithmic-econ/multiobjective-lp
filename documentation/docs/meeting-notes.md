# Notes

### 24/10/2024
- [ ] Don't divide voters by district (one voter in citywide + district)
- [ ] Future Solvers
  - based on simple mes
    - PB one constraint, i.e., with only positive weights, total budget 
    - binary variables
    - C++ implementation of solver itself 
    - investigate how python and gurobi communicates
  - extend simple mes with constraints 

### 10/10/2024
- [x] Config to problemRunner as json with 
- [x] Loop runner over directories

### 11/09/2024
- [ ] Transform (if possible) election metrics / statistics to general constraint
  - [x] dummy example
  - EJR unclear
- [x] Analyzer module
  - [x] Part of repo not package 
  - [x] Generate MOLP from pabutools format
  - [x] Run solver and save to file
  - Analyze results
    - [x] start with tables / raw numbers
    - [ ] graphs later
- [x] Read "Market based explanations of collective decisions, D. Peters"


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
    - [x] sum of objectives
    - [x] count of non zero objective
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
