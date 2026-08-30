from typing import List

import pulp
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintVar,
    LpMaximize,
    LpMinimize,
    LpProblem,
    LpVariable,
)

from muoblp.utils.lp_writer_utils import expression_to_lp_format

# Override line limit for writeLP to output single line values
pulp.const.LpCplexLPLineSize = 100000

# Silence pulp 3.3.x v4-migration DeprecationWarnings (4.0 migration out of roadmap scope)
pulp.set_v4_migration_warnings(False)


class MultiObjectiveLpProblem(LpProblem):
    def __init__(
        self,
        name: str,
        sense: LpMaximize | LpMinimize = LpMaximize,  # pyright: ignore[reportInvalidTypeForm]  # pulp sense consts are ints, not types (fix in T30)
        objectives: list[LpAffineExpression] | None = None,
        objectives_weights: dict[str, float] | None = None,
    ) -> None:
        super().__init__(name, sense=sense)
        self._objectives = objectives if objectives is not None else []
        self._objectives_weights = (
            objectives_weights if objectives_weights is not None else {}
        )
        self._objectives_voter_groups: dict[str, list[str]] = {}

    @property
    def objectives(self) -> List[LpAffineExpression]:
        return self._objectives

    def set_objectives(self, objectives: List[LpAffineExpression]) -> None:
        self._objectives = objectives

    @property
    def objectives_weights(self) -> dict[str, float]:
        return self._objectives_weights

    def set_objectives_weights(
        self, objectives_weights: dict[str, float]
    ) -> None:
        self._objectives_weights = objectives_weights

    @property
    def objectives_voter_groups(self) -> dict[str, list[str]]:
        return self._objectives_voter_groups

    def set_objectives_voter_groups(
        self, objectives_voter_groups: dict[str, list[str]]
    ) -> None:
        self._objectives_voter_groups = objectives_voter_groups

    # TODO: Decide how to handle fixObjective and restoreObjective

    def __iadd__(self, other):
        """Append objective expressions to `objectives` instead of
        overwriting pulp's single scalar objective.

        `problem += expression` (or a bare variable) accumulates: repeated
        `+=` builds up the objective list, and `self.objective` is left
        untouched (no pulp "Overwriting previously set objective" warning).
        Constraints, `(constraint, name)` tuples and plain numbers keep
        pulp's behaviour and delegate to `LpProblem`.
        """
        candidate, name = other if isinstance(other, tuple) else (other, None)
        # LpConstraint subclasses LpAffineExpression - check it first.
        if isinstance(candidate, (LpConstraintVar, LpConstraint)):
            return super().__iadd__(other)
        if isinstance(candidate, LpVariable):
            candidate = LpAffineExpression(candidate)
        if isinstance(candidate, LpAffineExpression):
            if name is not None:
                candidate.name = name
            self._objectives.append(candidate)
            return self
        return super().__iadd__(other)

    def write_lp(self, filename, writeSOS=1, mip=1, max_length=100):
        super().writeLP(filename, writeSOS, mip, max_length)
        with open(filename, "a", encoding="utf-8") as file:
            file.write("OBJECTIVES:\n")
            for objective in self.objectives:
                file.write(expression_to_lp_format(objective))
            file.write("END_OBJECTIVES:\n")
            file.write("WEIGHTS:\n")
            for name, weight in self.objectives_weights.items():
                file.write(f"{name}: {weight}\n")
            file.write("END_WEIGHTS:\n")
        return
