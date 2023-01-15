import os

import pytest
from pytest import fixture

import utils
from algorithms.constraint_courses import ConstraintCourses
from collector.db.db import Database
from data import translation
from data.degree import Degree
from data.language import Language


class TestConstraintCourses:

    def test_all_courses_constraints_in_txt_file_database(self):
        translation.config_language_text(Language.HEBREW)
        courses, _unused_are_blocked_by_result, _unused_blocks_courses_result = ConstraintCourses().prepare_data()
        degrees = {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}
        all_courses = Database().load_courses(Language.HEBREW, degrees)
        all_courses_names = {course.name for course in all_courses}
        courses_dont_exist = all_courses_names - courses.keys()
        assert not courses_dont_exist

    def test_validate_courses_data(self):
        constraint_courses = ConstraintCourses()
        courses_names = {"a", "b", "c"}
        all_courses = {"a", "b", "c"}
        constraint_courses.validate_courses_data(courses_names, all_courses)

        with pytest.raises(ValueError):
            constraint_courses.validate_courses_data({"a", "b", "c", "d"}, all_courses)

    def test_prepare_data(self, constraint_courses_mock):
        data = constraint_courses_mock.prepare_personal_data()
        all_courses_in_txt, are_blocked_by_result, blocks_courses_result = data
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
            PERSONAL_DATABASE_PATH = os.path.join(utils.get_database_path(), "test_personal_database.db")

        class ConstraintCoursesMock(ConstraintCourses):

            BLOCKED_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "are_blocked_by.txt"
            BLOCKS_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "blocks_courses.txt"
            PERSONAL_PASSED_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "personal_passed_courses.txt"
            PERSONAL_BLOCKED_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "personal_are_blocked_by.txt"
            PERSONAL_BLOCKS_COURSES_PATH = ConstraintCourses.GENERATED_DATA_PATH / "personal_blocks_courses.txt"

        database = DatabaseMock()
        database.clear_personal_database()
        database.init_personal_database_tables()
        course = utils.get_course_data_test()
        database.save_courses_already_done({course})
        constraint_courses = ConstraintCoursesMock()
        constraint_courses.database = database
        return constraint_courses
