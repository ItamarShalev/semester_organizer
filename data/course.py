from typing import Union, Set

from data.degree import Degree
from data.semester import Semester
from data.type import Type


class Course:

    def __init__(self, name: str, course_number: int, parent_course_number: int,
                 semesters: Union[Semester, Set[Semester], None] = None,
                 degrees: Union[Degree, Set[Degree], None] = None,
                 mandatory_degrees: Union[Degree, Set[Degree], None] = None):
        self.name = name
        self.course_number = course_number
        self.parent_course_number = parent_course_number
        self.attendance_required_for_lecture = True
        self.attendance_required_for_practice = True
        if isinstance(semesters, Semester):
            semesters = {semesters}
        self.semesters = semesters or set()

        if isinstance(degrees, Degree):
            degrees = {degrees}

        if isinstance(mandatory_degrees, Degree):
            mandatory_degrees = {mandatory_degrees}

        self.degrees = degrees or set()
        self.mandatory_degrees = mandatory_degrees or set()

    def add_semesters(self, semesters: Union[Semester, Set[Semester]]):
        if isinstance(semesters, Semester):
            semesters = {semesters}
        self.semesters.update(semesters)

    def add_degrees(self, degrees: Union[Degree, Set[Degree]]):
        if isinstance(degrees, Degree):
            degrees = {degrees}
        self.degrees.update(degrees)

    def add_mandatory(self, degrees: Union[Degree, Set[Degree]]):
        if isinstance(degrees, Degree):
            degrees = {degrees}
        self.mandatory_degrees.update(degrees)

    @property
    def optional_degrees(self) -> Set[Degree]:
        return self.degrees - self.mandatory_degrees

    def __eq__(self, other):
        is_equals = self.name == other.name
        is_equals = is_equals and self.course_number == other.course_number
        is_equals = is_equals and self.parent_course_number == other.parent_course_number
        return is_equals

    def __hash__(self):
        return hash((self.name, self.course_number, self.parent_course_number))

    def set_attendance_required(self, course_type: Type, required: bool):
        if course_type.is_lecture():
            self.attendance_required_for_lecture = required
        elif course_type.is_exercise():
            self.attendance_required_for_practice = required

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter((self.name, self.course_number, self.parent_course_number))

    def is_attendance_required(self, course_type: Type):
        attendance_required = True

        if course_type.is_lecture():
            attendance_required = self.attendance_required_for_lecture

        elif course_type.is_exercise():
            attendance_required = self.attendance_required_for_practice

        return attendance_required
