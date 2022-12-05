from dataclasses import dataclass
from typing import List


@dataclass
class CourseChoice:
    name: str
    available_teachers_for_lecture: List[str]
    attendance_required_for_lecture: bool
    available_teachers_for_practice: List[str]
    attendance_required_for_practice: bool
