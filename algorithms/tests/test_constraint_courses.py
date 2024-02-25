import warnings

from pytest import fixture

import utils
from algorithms.constraint_courses import ConstraintCourses
from collector.db.db import Database
from data import translation
from data.degree import Degree
from data.language import Language


class TestConstraintCourses:

    def test_export_generated_json_data(self):
        translation.config_language_text(Language.HEBREW)
        ConstraintCourses().export_generated_json_data()

    def test_new_course_exist_in_levnet_but_not_in_constraint(self):
        translation.config_language_text(Language.HEBREW)
        courses, *_ = ConstraintCourses().prepare_data()
        degrees = {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}
        all_courses = Database().load_courses(Language.HEBREW, degrees)
        all_courses_id_name = {course.course_number: course.name for course in all_courses if course.is_active}
        courses_doesnt_exist = set(all_courses_id_name.keys()) - {course.course_number for course in courses.values()}
        list_doesnt_exist = {course_number: all_courses_id_name[course_number]
                             for course_number in courses_doesnt_exist}
        str_courses_names = '\n'.join(f"Course id: '{course_number}',Course name: '{course_name}'"
                                      for course_number, course_name in list_doesnt_exist.items())
        assert not courses_doesnt_exist, f"ERROR: There are more new courses\n" \
                                         f"Please add them.\n" \
                                         f"Courses:\n{str_courses_names}."

    def test_deprecated_course_exist_in_constraint_but_not_in_levnet(self):

        translation.config_language_text(Language.HEBREW)
        courses, *_ = ConstraintCourses().prepare_data()
        degrees = {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}
        all_courses = Database().load_courses(Language.HEBREW, degrees)
        all_levnet_courses_ids = {course.course_number for course in all_courses}
        constraint_courses_ids_names = {course.course_number: course.name for course in courses.values()}
        courses_doesnt_exist = set(constraint_courses_ids_names.keys()) - all_levnet_courses_ids

        list_doesnt_exist = {course_number: constraint_courses_ids_names[course_number]
                             for course_number in courses_doesnt_exist}
        str_courses_names = '\n'.join(f"Course id: '{course_number}',Course name: '{course_name}'"
                                      for course_number, course_name in list_doesnt_exist.items())
        if list_doesnt_exist:
            warnings.simplefilter("always")
            warning_message = f"WARNING: There can be more deprecated courses.\n" \
                              f"Check if it's because it's exist this semester or really deprecated." \
                              f"Please remove them if needed or add 'deprecated' = true in the json data file.\n" \
                              f"Courses:\n{str_courses_names}."
            print(warning_message)
            warnings.warn(warning_message, UserWarning)

    def test_prepare_data(self, constraint_courses_mock):
        all_courses_in_txt, are_blocked_by_result, blocks_courses_result = constraint_courses_mock.prepare_data()
        assert all_courses_in_txt
        assert are_blocked_by_result
        assert blocks_courses_result

    def test_prepare_personal_data(self, constraint_courses_mock):
        data = constraint_courses_mock.prepare_personal_data()
        all_courses_in_txt, are_blocked_by_result, blocks_courses_result = data
        assert all_courses_in_txt
        assert are_blocked_by_result
        assert blocks_courses_result

    def test_get_courses_cant_do(self, constraint_courses_mock):
        courses_cant_do = constraint_courses_mock.get_courses_cant_do()
        assert courses_cant_do

    def test_get_courses_can_do(self, constraint_courses_mock):
        courses_can_do = constraint_courses_mock.get_courses_can_do()
        assert courses_can_do

    @fixture
    def constraint_courses_mock(self):
        translation.config_language_text(Language.HEBREW)

        class DatabaseMock(Database):
            def __init__(self):
                super().__init__("test_database")

        class ConstraintCoursesMock(ConstraintCourses):
            _ALL_COURSES_FILE_NAME = "all_courses_blocked_and_blocks_info.json"
            _ALL_COURSES_FILE_NAME_PERSONAL = "personal_all_courses_blocked_and_blocks_info.json"

            BLOCKED_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "are_blocked_by_courses.json"
            BLOCKS_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "blocks_courses.json"
            ALL_INFO_PATH = ConstraintCourses.GENERATED_DATA_PATH / _ALL_COURSES_FILE_NAME
            PERSONAL_PASSED_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "personal_passed_courses.json"
            PERSONAL_BLOCKED_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "personal_are_blocked_by.json"
            PERSONAL_BLOCKS_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "personal_blocks_courses.json"
            PERSONAL_ALL_INFO_PATH = ConstraintCourses.GENERATED_DATA_PATH / _ALL_COURSES_FILE_NAME_PERSONAL

        database = DatabaseMock()
        database.clear_personal_database()
        database.init_personal_database_tables()
        course = utils.get_course_data_test()
        database.save_courses_already_done({course})
        constraint_courses = ConstraintCoursesMock()
        constraint_courses.database = database
        return constraint_courses
