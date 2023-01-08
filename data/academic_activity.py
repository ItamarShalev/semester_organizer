from typing import List

from data.activity import Activity
from data.course import Course
from data.type import Type


class AcademicActivity(Activity):

    UNLIMITED_CAPACITY = 10000000
    DEFAULT_ACTUAL_COURSE_NUMBER = -1

    def __init__(self, name: str = None, activity_type: Type = None, attendance_required: bool = None,
                 lecturer_name: str = None, course_number: int = None, parent_course_number: int = None,
                 location: str = None, activity_id: str = None, description: str = None, current_capacity: int = None,
                 max_capacity: int = None, actual_course_number: int = None):
        super().__init__(name, activity_type, attendance_required)
        self.lecturer_name = lecturer_name
        self.course_number = course_number
        self.parent_course_number = parent_course_number
        self.location = location
        self.activity_id = activity_id
        self.description = description or ""
        self.current_capacity = current_capacity or 0
        self.max_capacity = max_capacity or AcademicActivity.UNLIMITED_CAPACITY
        self.actual_course_number = actual_course_number or AcademicActivity.DEFAULT_ACTUAL_COURSE_NUMBER

    def set_capacity(self, current_capacity: int, max_capacity: int):
        """
        :param current_capacity: the current number of students registered to the course
        :param max_capacity: the maximum number of students allowed to register to the course
        :param current_capacity:
        """
        self.current_capacity = current_capacity
        self.max_capacity = max_capacity

    def is_have_free_places(self) -> bool:
        return self.current_capacity < self.max_capacity

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

    def __hash__(self):
        return hash((self.name, self.course_number, self.parent_course_number, self.activity_id))

    def same_as_course(self, course: Course):
        is_same = self.name == course.name
        is_same = is_same and self.course_number == course.course_number
        is_same = is_same and self.parent_course_number == course.parent_course_number
        return is_same

    @staticmethod
    def extract_courses_data(academic_activities) -> List[Course]:
        return [activity.convert_to_course_object() for activity in academic_activities]

    @staticmethod
    def union_courses(academic_activities, courses: List[Course]):
        for activity in academic_activities:
            for course in courses:
                if activity.same_as_course(course):
                    activity.attendance_required = course.is_attendance_required(activity.type)
                    activity.activity_id = activity.activity_id or course.activity_id
                    break
