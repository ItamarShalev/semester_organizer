import os

import utils
from collector.db.db import Database
from conftest import TestClass
from data.academic_activity import AcademicActivity
from data.course import Course
from data.type import Type
from data.user import User


class TestDatabase(TestClass):

    def test_courses_data(self):
        database = Database()
        courses = [Course(f"Course {i}", i, i + 1000) for i in range(10)]
        database.clear_courses_data()
        database.save_courses_data(courses)
        loaded_courses = database.load_courses_data()
        assert set(courses) == set(loaded_courses)

        database.clear_courses_data()
        assert not database.load_courses_data()

    def test_campus_names(self):

        database = Database()
        campus_names = [f"Course {i}" for i in range(10)]
        database.clear_campus_names()
        database.save_campus_names(campus_names)
        loaded_campus_names = database.load_campus_names()
        assert campus_names == loaded_campus_names

        database.clear_campus_names()
        assert not database.load_campus_names()

    def test_academic_activities(self):

        database = Database()
        academic_activities = []
        campus_name = utils.get_campus_name_test()
        for i in range(10):
            academic_activities.append(
                AcademicActivity(f"Course {i}", Type.LECTURE, True, f"A {i}", i, i + 1000, "", activity_id=f"{i}"))
        courses = AcademicActivity.extract_courses_data(academic_activities)
        database.clear_academic_activities_data()
        database.save_academic_activities_data(campus_name, academic_activities)
        assert database.check_if_courses_data_exists(campus_name, courses)

        loaded_academic_activities = database.load_academic_activities_data(campus_name, courses)
        assert set(academic_activities) == set(loaded_academic_activities)

        database.clear_campus_names()
        assert not database.load_campus_names()

        database.save_academic_activities_data(campus_name, academic_activities)
        academic_activities[0].type = Type.LAB
        academic_activities.append(
            AcademicActivity(f"Course {30}", Type.LECTURE, True, f"A {30}", 30, 30 + 1000, "", activity_id=f"{30}"))
        database.save_academic_activities_data(campus_name, academic_activities)
        courses.clear()
        courses.append(Course(f"Course {30}", 30, 30 + 1000))
        courses.append(Course(f"Course {0}", 0, 0 + 1000))
        assert database.check_if_courses_data_exists(campus_name, courses)

        loaded_academic_activities = database.load_academic_activities_data(campus_name, courses)
        assert set(loaded_academic_activities).issubset(set(academic_activities))

        database.clear_academic_activities_data()
        assert not database.load_academic_activities_data(campus_name, courses)

    def test_load_hard_coded_user_data(self):
        database = Database()
        if database.load_hard_coded_user_data():
            utils.get_logging().debug("user data already defined, don't overwrite it.")
            return
        user = User("username", "password")
        with open(Database.USER_NAME_FILE_PATH, "w+") as file:
            file.write(f"{user.username}\n{user.password}")
        loaded_user = database.load_hard_coded_user_data()
        assert user == loaded_user

        os.remove(Database.USER_NAME_FILE_PATH)
        assert database.load_hard_coded_user_data() is None
