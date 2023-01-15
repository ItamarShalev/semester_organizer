from pathlib import Path
from typing import Set, Dict, Tuple

import utils
from collector.db.db import Database
from data.course_constraint import CourseConstraint
from data.degree import Degree
from data.language import Language

Name = str


class ConstraintCourses:
    CURRENT_DIR = Path(__file__).parent
    GENERATED_DATA_PATH = CURRENT_DIR / "generated_data"

    CONSTRAINT_COURSES_DATA_PATH = CURRENT_DIR / "constraint_courses_data.txt"
    BLOCKED_COURSES_PATH = GENERATED_DATA_PATH / "are_blocked_by.txt"
    BLOCKS_COURSES_PATH = GENERATED_DATA_PATH / "blocks_courses.txt"
    PERSONAL_PASSED_COURSES_PATH = GENERATED_DATA_PATH / "personal_passed_courses.txt"
    PERSONAL_BLOCKED_COURSES_PATH = GENERATED_DATA_PATH / "personal_are_blocked_by.txt"
    PERSONAL_BLOCKS_COURSES_PATH = GENERATED_DATA_PATH / "personal_blocks_courses.txt"

    def __init__(self):
        self.database = Database()

    def validate_courses_data(self, courses_names: Set[Name], all_courses: Set[Name]):
        not_exists_courses = courses_names - all_courses
        if not_exists_courses:
            raise ValueError(f"Course(s) {not_exists_courses} does not exist")

    def prepare_data(self) -> (Dict[Name, CourseConstraint], Dict[Name, Set[Name]], Dict[Name, Set[Name]]):
        degrees = {Degree.SOFTWARE_ENGINEERING, Degree.COMPUTER_SCIENCE}
        all_courses = self.database.load_courses(Language.HEBREW, degrees)
        all_courses = {course.name: course for course in all_courses}
        all_courses_in_txt = CourseConstraint.extract_courses_data(self.CONSTRAINT_COURSES_DATA_PATH, all_courses)
        self.validate_courses_data(all_courses_in_txt.keys(), all_courses_in_txt.keys())
        are_blocked_by_result = {name: course.get_extended_prerequisite_courses_names(all_courses_in_txt)
                                 for name, course in all_courses_in_txt.items()}
        are_blocked_by_result = utils.sort_dict_by_key(are_blocked_by_result)
        with open(self.BLOCKED_COURSES_PATH, "w", newline="\n", encoding=utils.ENCODING) as file:
            for name, extended_prerequisite_courses_names in are_blocked_by_result.items():
                file.write(f"{name}: {', '.join(extended_prerequisite_courses_names)}\n")

        blocks_courses_result = {name: set() for name in all_courses_in_txt}
        for name, extended_prerequisite_courses_names in are_blocked_by_result.items():
            for extended_prerequisite_course_name in extended_prerequisite_courses_names:
                blocks_courses_result[extended_prerequisite_course_name].add(name)

        blocks_courses_result = utils.sort_dict_by_key(blocks_courses_result)
        with open(self.BLOCKS_COURSES_PATH, "w", newline="\n", encoding=utils.ENCODING) as file:
            for name, blocks_courses_names in blocks_courses_result.items():
                file.write(f"{name}: {', '.join(blocks_courses_names)}\n")

        return all_courses_in_txt, are_blocked_by_result, blocks_courses_result

    def prepare_personal_data(self):
        all_courses_in_txt, are_blocked_by_result, blocks_courses_result = self.prepare_data()
        courses_already_done = {course.name for course in self.database.load_courses_already_done(Language.HEBREW)}

        are_blocked_by_result = {name: (courses - courses_already_done) for name, courses in
                                 are_blocked_by_result.items() if name not in courses_already_done}
        blocks_courses_result = {name: (courses - courses_already_done) for name, courses in
                                 blocks_courses_result.items() if name not in courses_already_done}

        self._write_personal_dict_data(self.PERSONAL_BLOCKED_COURSES_PATH, are_blocked_by_result)
        self._write_personal_dict_data(self.PERSONAL_BLOCKS_COURSES_PATH, blocks_courses_result)

        return all_courses_in_txt, are_blocked_by_result, blocks_courses_result

    def get_courses_cant_do(self) -> Set[Tuple[Name, int]]:
        """
        :return: set of courses that can't be done course name in hebrew and parent course number
        """
        _unused_courses, are_blocked_by_result, _unused_blocks_courses_result = self.prepare_personal_data()
        degrees = {Degree.SOFTWARE_ENGINEERING, Degree.COMPUTER_SCIENCE}
        all_courses = self.database.load_courses(Language.HEBREW, degrees)
        all_courses = {course.name: course for course in all_courses}
        courses_cant_do = {(name, all_courses[name].parent_course_number)
                           for name, block_courses in are_blocked_by_result.items() if block_courses}
        return courses_cant_do

    def get_courses_can_do(self):
        _unused_courses, are_blocked_by_result, _unused_blocks_courses_result = self.prepare_personal_data()
        degrees = {Degree.SOFTWARE_ENGINEERING, Degree.COMPUTER_SCIENCE}
        all_courses = self.database.load_courses(Language.HEBREW, degrees)
        all_courses = {course.name: course for course in all_courses}
        courses_already_done = {course.name for course in self.database.load_courses_already_done(Language.HEBREW)}
        courses_can_do = {(name, all_courses[name].parent_course_number)
                          for name, block_courses in are_blocked_by_result.items()
                          if not block_courses and name not in courses_already_done}
        return courses_can_do

    def _write_personal_dict_data(self, file_path: Path, dict_data: Dict[Name, Set[Name]]):
        dict_data = utils.sort_dict_by_key(dict_data)
        with open(file_path, "w", newline="\n", encoding=utils.ENCODING) as file:
            for name, courses in dict_data.items():
                file.write(f"{name}: {', '.join(courses)}\n")
