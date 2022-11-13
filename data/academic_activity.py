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
        return Course(self.name, self.course_number, self.parent_course_number)
