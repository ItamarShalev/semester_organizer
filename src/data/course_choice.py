from dataclasses import dataclass
from typing import Set


@dataclass
class CourseChoice:
    name: str
    parent_course_number: int
    available_teachers_for_lecture: Set[str]
    available_teachers_for_practice: Set[str]
    attendance_required_for_lecture: bool = True
    attendance_required_for_practice: bool = True

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
