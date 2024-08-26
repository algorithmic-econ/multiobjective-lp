# Introduction

About this project ...

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
