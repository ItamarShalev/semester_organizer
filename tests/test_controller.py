import pytest

from collector.db.db import Database
from collector.network import network
from convertor import convert_helper
from csp import csp
from data.academic_activity import AcademicActivity
from data.course import Course
from data.output_format import OutputFormat
from data.type import Type


@pytest.mark.skip(reason="Not implemented yet.")
def test_flow_without_gui_without_database():
    database = Database()
    user = database.load_hard_coded_user_data()
    assert user, "Don't have user data to check."
    assert network.check_username_and_password(user), "Can't connect to the server."

    campus_names = network.extract_campus_names(user)
    assert campus_names, "Can't extract campus names from the server."
    assert "מכון לב" in campus_names, "Some campus names are missing."
    database.save_campus_names(campus_names)

    courses = network.extract_all_courses(user)
    assert courses, "Can't extract courses from the server."
    course = Course("חשבון אינפני' להנדסה 1", 120131, 318)
    assert course in courses, "Some courses are missing."
    database.save_courses_data(courses)

    academic_activities = [AcademicActivity("חשבון אינפני' להנדסה 1", Type.LECTURE, True, "", 120131, 318, "")]
    network.fill_academic_activities_data(user, "מכון לב", academic_activities)
    meetings_values = academic_activities[0].days.values()

    assert any(meetings for meetings in meetings_values), "Can't extract academic activities from the server."
    assert academic_activities, "Can't extract academic activities from the server."

    formats = list(OutputFormat)
    schedules = csp.extract_schedules(academic_activities)
    assert schedules, "At least one schedule should be extracted."
    convert_helper.convert_activities(schedules, "results", formats)


@pytest.mark.skip(reason="Not implemented yet.")
def test_flow_without_gui_with_database():
    database = Database()
    user = database.load_hard_coded_user_data()
    assert user, "Don't have user data to check."
    assert network.check_username_and_password(user), "Can't connect to the server."

    campus_names = database.load_campus_names()
    if not campus_names:
        campus_names = network.extract_campus_names(user)
        assert campus_names, "Can't extract campus names from the server."
        assert "מכון לב" in campus_names, "Some campus names are missing."
        database.save_campus_names(campus_names)

    courses = database.load_courses_data()
    course = Course("חשבון אינפני' להנדסה 1", 120131, 318)
    if not courses:
        courses = network.extract_all_courses(user)
        assert courses, "Can't extract courses from the server."
        assert course in courses, "Some courses are missing."
        database.save_courses_data(courses)

    academic_activities = database.load_academic_activities_data([course])
    if not academic_activities:
        academic_activities = [AcademicActivity("חשבון אינפני' להנדסה 1", Type.LECTURE, True, "", 120131, 318, "")]
        network.fill_academic_activities_data(user, "מכון לב", academic_activities)

    meetings_values = academic_activities[0].days.values()

    assert any(meetings for meetings in meetings_values), "Can't extract academic activities from the server."
    assert academic_activities, "Can't extract academic activities from the server."

    formats = list(OutputFormat)
    schedules = csp.extract_schedules(academic_activities)
    assert schedules, "At least one schedule should be extracted."
    convert_helper.convert_activities(schedules, "results", formats)
    assert campus_names, "Don't have campus names to check."
    assert "מכון לב" in campus_names, "Some campus names are missing."
