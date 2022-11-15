from data.activity import Activity
from data.course import Course
from data.type import Type


class AcademicActivity(Activity):

    def __init__(self, name: str, activity_type: Type, is_must: bool, lecturer_name: str, course_number: int,
                 parent_course_number: int, location: str):
        super().__init__(name, activity_type, is_must)
        self.lecturer_name = lecturer_name
        self.course_number = course_number
        self.parent_course_number = parent_course_number
        self.location = location

    def convert_to_course_object(self):
        course = Course(self.name, self.course_number, self.parent_course_number)
        course.set_attendance_required(self.type, self.attendance_required)
        return course

    def __eq__(self, other):
        is_equals = super().__eq__(other)
        is_equals = is_equals and self.lecturer_name == other.lecturer_name
        is_equals = is_equals and self.course_number == other.course_number
        is_equals = is_equals and self.parent_course_number == other.parent_course_number
        is_equals = is_equals and self.location == other.location
        return is_equals

    def __str__(self):
        return f"{super().__str__()} {self.name} {self.lecturer_name}"

    def __repr__(self):
        return str(self)
