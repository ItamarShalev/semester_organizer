from pathlib import Path
from typing import Set, Dict, Tuple

from functools import lru_cache
from collector.db.db import Database
from data.course_constraint import CourseConstraint
from data.degree import Degree
from data.language import Language

Name = str


class ConstraintCourses:
    CURRENT_DIR = Path(__file__).parent
    GENERATED_DATA_PATH = CURRENT_DIR / "generated_data"
    CONSTRAINT_COURSES_DATA_PATH = CURRENT_DIR / "constraint_courses_data.json"

    BLOCKED_COURSES_PATH = GENERATED_DATA_PATH / "are_blocked_by_courses.json"
    BLOCKS_COURSES_PATH = GENERATED_DATA_PATH / "blocks_courses.json"
    ALL_INFO_PATH = GENERATED_DATA_PATH / "all_courses_blocked_and_blocks_info.json"

    PERSONAL_PASSED_COURSES_PATH = GENERATED_DATA_PATH / "personal_passed_courses.json"
    PERSONAL_BLOCKED_COURSES_PATH = GENERATED_DATA_PATH / "personal_are_blocked_by.json"
    PERSONAL_BLOCKS_COURSES_PATH = GENERATED_DATA_PATH / "personal_blocks_courses.json"
    PERSONAL_ALL_INFO_PATH = GENERATED_DATA_PATH / "personal_all_courses_blocked_and_blocks_info.json"

    def __init__(self):
        self.database = Database()
        self.course_constraint = CourseConstraint()

    def export_data(self, are_blocked_by_result: Dict, blocks_courses_result: Dict,
                    file_path_blocked: Path, file_path_blocks: Path, file_path_all: Path):

        self.course_constraint.export(
            list(are_blocked_by_result.values()),
            include_blocked_by=True,
            include_blocks=False,
            file_path=file_path_blocked
        )
        self.course_constraint.export(
            list(blocks_courses_result.values()),
            include_blocked_by=False,
            include_blocks=True,
            file_path=file_path_blocks
        )
        self.course_constraint.export(
            list(blocks_courses_result.values()),
            include_blocked_by=True,
            include_blocks=True,
            file_path=file_path_all
        )

    @lru_cache(maxsize=128)
    def prepare_data(self) -> (Dict[Name, CourseConstraint], Dict[Name, Set[Name]], Dict[Name, Set[Name]]):
        all_courses_in_json = self.course_constraint.extract_courses_data(self.CONSTRAINT_COURSES_DATA_PATH)
        are_blocked_by_result = self.course_constraint.get_extended_blocked_by_courses(all_courses_in_json)
        blocks_courses_result = self.course_constraint.get_extended_blocks_courses(are_blocked_by_result)
        self.export_data(are_blocked_by_result, blocks_courses_result, self.BLOCKED_COURSES_PATH,
                         self.BLOCKS_COURSES_PATH, self.ALL_INFO_PATH)
        return all_courses_in_json, are_blocked_by_result, blocks_courses_result

    @lru_cache(maxsize=128)
    def prepare_personal_data(self):
        all_courses_in_json, are_blocked_by_result, blocks_courses_result = self.prepare_data()
        courses_already_done = self.database.load_courses_already_done(Language.HEBREW)
        courses_already_done = {course.course_number: course.name for course in courses_already_done}

        are_blocked_by_result = {object_id: course for object_id, course in are_blocked_by_result.items()
                                 if course.course_number not in courses_already_done}

        blocks_courses_result = {object_id: course for object_id, course in blocks_courses_result.items()
                                 if course.course_number not in courses_already_done}

        self.export_data(are_blocked_by_result, blocks_courses_result, self.PERSONAL_BLOCKED_COURSES_PATH,
                         self.PERSONAL_BLOCKS_COURSES_PATH, self.PERSONAL_ALL_INFO_PATH)

        return all_courses_in_json, are_blocked_by_result, blocks_courses_result

    @lru_cache(maxsize=128)
    def _get_course_do(self, can: bool) -> Set[Tuple[Name, int]]:
        _unused_courses, are_blocked_by_result, _unused_blocks_courses_result = self.prepare_data()
        are_blocked_by_result = {constraint_course.course_number: constraint_course
                                 for constraint_course in are_blocked_by_result.values()}

        degrees = {Degree.SOFTWARE_ENGINEERING, Degree.COMPUTER_SCIENCE}
        all_courses = self.database.load_courses(Language.HEBREW, degrees)
        courses_already_done = self.database.load_courses_already_done(Language.HEBREW)
        courses_already_done_numbers = {course.course_number for course in courses_already_done}
        result = set()
        for course in all_courses:
            all_needed_courses = {constraint_course.course_number
                                  for constraint_course in are_blocked_by_result[course.course_number].blocked_by}
            left_courses = all_needed_courses - courses_already_done_numbers
            if can ^ bool(left_courses):
                result.add((course.name, course.parent_course_number))
        return result

    def get_courses_cant_do(self) -> Set[Tuple[Name, int]]:
        """
        :return: set of courses that can't be done course name in hebrew and parent course number
        """
        return self._get_course_do(can=False)

    def get_courses_can_do(self) -> Set[Tuple[Name, int]]:
        return self._get_course_do(can=True)
