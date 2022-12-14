from dataclasses import dataclass
from typing import List


@dataclass
class CourseChoice:
    name: str
    available_teachers_for_lecture: List[str]
    available_teachers_for_practice: List[str]
    attendance_required_for_lecture: bool = True
    attendance_required_for_practice: bool = True

    def __hash__(self):
        return hash(self.name)
