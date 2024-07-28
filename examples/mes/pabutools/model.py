from typing import Optional, List

from pabutools.election import Project, Profile
from pydantic import BaseModel, ConfigDict


class EnhancedProject(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    project: Project
    district: Optional[str]
    costs: List[int] = []

    def __eq__(self, other) -> bool:
        if isinstance(other, EnhancedProject):
            return self.project.name == other.project.name
        if isinstance(other, str):
            return self.project.name == other
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, EnhancedProject):
            return self.project.name.__le__(other.project.name)
        if isinstance(other, str):
            return self.project.name.__le__(other)

    def __lt__(self, other) -> bool:
        if isinstance(other, EnhancedProject):
            return self.project.name.__lt__(other.project.name)
        if isinstance(other, str):
            return self.project.name.__lt__(other)

    def __hash__(self) -> int:
        return hash(self.project.name)


class EnhancedProfile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    profile: Profile
    district: Optional[str]
