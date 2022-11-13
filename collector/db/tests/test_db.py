import pytest

from collector.db import db
from data.academic_activity import AcademicActivity
from data.course import Course
from data.type import Type


@pytest.mark.skip(reason="Not implemented yet.")
def test_courses_data():
    courses = [Course(f"Course {i}", i, i + 1000) for i in range(10)]

    db.clear_courses_data()
    db.save_courses_data(courses)
    loaded_courses = db.load_courses_data()
    assert courses == loaded_courses

    db.clear_courses_data()
    assert db.load_courses_data() == []


@pytest.mark.skip(reason="Not implemented yet.")
def test_campus_names():
    campus_names = [f"Course {i}" for i in range(10)]

    db.clear_campus_names()
    db.save_campus_names(campus_names)
    loaded_campus_names = db.load_campus_names()
    assert campus_names == loaded_campus_names

    db.clear_campus_names()
    assert db.load_campus_names() == []


@pytest.mark.skip(reason="Not implemented yet.")
def test_academic_activities():
    academic_activities = []
    for i in range(10):
        academic_activities.append(AcademicActivity(f"Course {i}", Type.LECTURE, True, f"A {i}", i, i + 1000, ""))

    courses = [activity.convert_to_course_object() for activity in academic_activities]

    db.clear_academic_activities_data()
    db.save_academic_activities_data(academic_activities)
    assert db.check_if_courses_data_exists(courses)

    loaded_academic_activities = db.load_academic_activities_data(courses)
    assert academic_activities == loaded_academic_activities

    db.clear_campus_names()
    assert db.load_campus_names() == []

    db.save_academic_activities_data(academic_activities)
    academic_activities[0].type = Type.LAB
    academic_activities.append(AcademicActivity(f"Course {30}", Type.LECTURE, True, f"A {30}", 30, 30 + 1000, ""))
    db.save_academic_activities_data(academic_activities)

    courses.clear()
    courses.append(Course(f"Course {30}", 30, 30 + 1000))
    courses.append(Course(f"Course {0}", 0, 0 + 1000))
    assert db.check_if_courses_data_exists(courses)

    loaded_academic_activities = db.load_academic_activities_data(courses)
    assert all(activity in academic_activities for activity in loaded_academic_activities)

    db.clear_academic_activities_data()
    assert db.load_academic_activities_data(courses) == []
