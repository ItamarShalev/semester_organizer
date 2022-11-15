from typing import List

from data.activity import Activity
from data.course import Course
from data.type import Type


class AcademicActivity(Activity):

    def __init__(self, name: str = None, activity_type: Type = None, attendance_required: bool = None,
                 lecturer_name: str = None, course_number: int = None, parent_course_number: int = None,
                 location: str = None, activity_id: str = None):
        super().__init__(name, activity_type, attendance_required)
        self.lecturer_name = lecturer_name
        self.course_number = course_number
        self.parent_course_number = parent_course_number
        self.location = location
        self.activity_id = activity_id

    def convert_to_course_object(self):
        course = Course(self.name, self.course_number, self.parent_course_number, activity_id=self.activity_id)
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
        return self.name

    def __repr__(self):
        return str(self)

    def same_as_course(self, course: Course):
        is_same = self.name == course.name
        is_same = is_same and self.course_number == course.course_number
        is_same = is_same and self.parent_course_number == course.parent_course_number
        return is_same

    @staticmethod
    def union_attendance_required(academic_activities, courses: List[Course]):
        for activity in academic_activities:
            for course in courses:
                if activity.same_as_course(course):
                    activity.attendance_required = course.attendance_required[activity.type]
                    activity.activity_id = course.activity_id
                    break
