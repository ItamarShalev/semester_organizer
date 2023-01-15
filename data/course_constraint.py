from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import utils
from data.course import Course


@dataclass
class PrerequisiteCourse:
    name: str
    course_data: Course
    can_be_taken_in_parallel: bool

    def __hash__(self):
        return hash(self.name)


class CourseConstraint:

    def __init__(self):
        self.name = None
        self.course_data = None
        self.prerequisite_courses = None

    @staticmethod
    def extract_courses_data(file_path: Path, all_courses: Dict[str, Course]):
        assert file_path.exists(), "File does not exist"
        courses = {}
        with open(file_path, "r", encoding=utils.ENCODING) as file:
            for line in file:
                line = line.strip()
                assert line, "Empty line"
                course = CourseConstraint()
                course.prerequisite_courses = set()
                course_data, prerequisite_courses = line.split(":")
                all_data = course_data.split("-")
                course.name = '-'.join(all_data[:-1])
                course_number = int(all_data[-1])
                assert course.name in all_courses, f"Course {course.name} is not in the courses data"
                course.course_data = all_courses[course.name]
                assert course.course_data.course_number == course_number, \
                    "Course number in file does not match course number in course data"
                if prerequisite_courses:
                    prerequisite_courses = prerequisite_courses.split(",")
                    for prerequisite_course in prerequisite_courses:
                        name = prerequisite_course.replace("^", "")
                        can_be_taken_in_parallel = "^" in prerequisite_course
                        if can_be_taken_in_parallel:
                            continue
                        assert name in all_courses, f"Course {name} is not in the courses data"
                        prerequisite_course = PrerequisiteCourse(name, all_courses[name], can_be_taken_in_parallel)
                        course.prerequisite_courses.add(prerequisite_course)
                courses[course.name] = course
        return courses

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def get_prerequisite_courses_names(self):
        return {prerequisite_course.name for prerequisite_course in self.prerequisite_courses}

    def get_extended_prerequisite_courses_names(self, all_courses: dict):
        if not self.prerequisite_courses:
            return set()
        queue = self.prerequisite_courses.copy()
        extended_prerequisite_courses_names = set()
        while queue:
            prerequisite_course = queue.pop()
            extended_prerequisite_courses_names.add(prerequisite_course.name)
            queue.update(all_courses[prerequisite_course.name].prerequisite_courses.copy())

        return extended_prerequisite_courses_names
