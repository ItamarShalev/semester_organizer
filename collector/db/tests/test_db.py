import os

import pytest

import utils
from collector.db.db import Database
from data.academic_activity import AcademicActivity
from data.course import Course
from data.type import Type
from data.user import User


@pytest.mark.skip(reason="Not implemented yet.")
def test_courses_data():
    database = Database()
    courses = [Course(f"Course {i}", i, i + 1000) for i in range(10)]

    database.clear_courses_data()
    database.save_courses_data(courses)
    loaded_courses = database.load_courses_data()
    assert courses == loaded_courses

    database.clear_courses_data()
    assert database.load_courses_data() == []


@pytest.mark.skip(reason="Not implemented yet.")
def test_campus_names():
    database = Database()
    campus_names = [f"Course {i}" for i in range(10)]

    database.clear_campus_names()
    database.save_campus_names(campus_names)
    loaded_campus_names = database.load_campus_names()
    assert campus_names == loaded_campus_names

    database.clear_campus_names()
    assert database.load_campus_names() == []


@pytest.mark.skip(reason="Not implemented yet.")
def test_academic_activities():
    database = Database()
    academic_activities = []
    for i in range(10):
        academic_activities.append(AcademicActivity(f"Course {i}", Type.LECTURE, True, f"A {i}", i, i + 1000, ""))

    courses = [activity.convert_to_course_object() for activity in academic_activities]

    database.clear_academic_activities_data()
    database.save_academic_activities_data(academic_activities)
    assert database.check_if_courses_data_exists(courses)

    loaded_academic_activities = database.load_academic_activities_data(courses)
    assert academic_activities == loaded_academic_activities

    database.clear_campus_names()
    assert database.load_campus_names() == []

    database.save_academic_activities_data(academic_activities)
    academic_activities[0].type = Type.LAB
    academic_activities.append(AcademicActivity(f"Course {30}", Type.LECTURE, True, f"A {30}", 30, 30 + 1000, ""))
    database.save_academic_activities_data(academic_activities)

    courses.clear()
    courses.append(Course(f"Course {30}", 30, 30 + 1000))
    courses.append(Course(f"Course {0}", 0, 0 + 1000))
    assert database.check_if_courses_data_exists(courses)

    loaded_academic_activities = database.load_academic_activities_data(courses)
    assert all(activity in academic_activities for activity in loaded_academic_activities)

    database.clear_academic_activities_data()
    assert database.load_academic_activities_data(courses) == []


def test_load_hard_coded_user_data():
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
