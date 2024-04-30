from dataclasses import dataclass
from typing import Set, Dict


@dataclass
class CourseChoice:
    name: str
    parent_course_number: int
    available_teachers_for_lecture: Set[str]
    available_teachers_for_practice: Set[str]
    attendance_required_for_lecture: bool = True
    attendance_required_for_practice: bool = True

    @staticmethod
    def from_json(data: Dict) -> 'CourseChoice':
        lectures = []
        practices = []

        for item in data['available_teachers_for_lecture']:
            lectures.extend(item.replace("\r\n", "\n").split("\n"))
        lectures = list(map(str.strip, lectures))

        for item in data['available_teachers_for_practice']:
            practices.extend(item.replace("\r\n", "\n").split("\n"))
        practices = list(map(str.strip, practices))

        course_choice = CourseChoice(
            name=data['name'],
            parent_course_number=data['parent_course_number'],
            available_teachers_for_lecture=set(lectures),
            available_teachers_for_practice=set(practices),
        )
        return course_choice

    def to_json(self) -> Dict:
        result = {
            'name': self.name,
            "parent_course_number": self.parent_course_number,
            "available_teachers_for_lecture": sorted(list(self.available_teachers_for_lecture or [])),
            "available_teachers_for_practice": sorted(list(self.available_teachers_for_practice or [])),
        }
        return result

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
