import pytest

from collector.db import db
from collector.network import network
from data.academic_activity import AcademicActivity
from data.type import Type


@pytest.mark.skip(reason="Not implemented yet.")
def test_check_username_and_password():
    user = db.load_hard_coded_user_data()
    assert user, "Don't have user data to check."
    assert network.check_username_and_password(user), "Can't connect to the server."


@pytest.mark.skip(reason="Not implemented yet.")
def test_extract_all_courses():
    user = db.load_hard_coded_user_data()
    assert user, "Don't have user data to check."
    assert network.check_username_and_password(user), "Can't connect to the server."

    courses = network.extract_all_courses(user)
    assert courses, "Can't extract courses from the server."


@pytest.mark.skip(reason="Not implemented yet.")
def test_extract_campus_names():
    user = db.load_hard_coded_user_data()
    assert user, "Don't have user data to check."
    assert network.check_username_and_password(user), "Can't connect to the server."

    campus_names = network.extract_campus_names(user)
    assert campus_names, "Can't extract campus names from the server."
    assert "מכון לב" in campus_names, "Some campus names are missing."


@pytest.mark.skip(reason="Not implemented yet.")
def test_fill_academic_activities_data():
    user = db.load_hard_coded_user_data()
    assert user, "Don't have user data to check."
    assert network.check_username_and_password(user), "Can't connect to the server."

    campus_names = network.extract_campus_names(user)
    assert campus_names, "Can't extract campus names from the server."

    academic_activities = [AcademicActivity("חשבון אינפני' להנדסה 1", Type.LECTURE, True, "", 120131, 318, "")]
    network.fill_academic_activities_data(user, "מכון לב", academic_activities)
    meetings_values = academic_activities[0].days.values()

    assert any(meetings for meetings in meetings_values), "Can't extract academic activities from the server."
    assert academic_activities, "Can't extract academic activities from the server."
