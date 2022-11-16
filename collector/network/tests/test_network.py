import pytest
import utils

from collector.db.db import Database
from collector.network.network import Network


@pytest.mark.network()
def test_connect():
    user = Database().load_hard_coded_user_data()
    network = Network(user)
    assert user, "Don't have user data to check."
    assert network.check_connection(), "Can't connect to the server."


@pytest.mark.skip(reason="Not implemented yet.")
@pytest.mark.network()
def test_extract_all_courses():
    user = Database().load_hard_coded_user_data()
    network = Network(user)
    campus_name = utils.get_campus_name_test()
    assert user, "Don't have user data to check."
    assert network.check_connection(), "Can't connect to the server."

    courses = network.extract_all_courses(campus_name)
    assert courses, "Can't extract courses from the server."


@pytest.mark.skip(reason="Not implemented yet.")
@pytest.mark.network()
def test_extract_campus_names():
    database = Database()
    user = database.load_hard_coded_user_data()
    network = Network(user)
    campus_name = utils.get_campus_name_test()
    assert user, "Don't have user data to check."
    assert network.check_connection(), "Can't connect to the server."

    campus_names = network.extract_campus_names()
    assert campus_names, "Can't extract campus names from the server."
    assert all(campus_name for campus_name in database.get_common_campuses_names()), "Some campuses names are missing."


@pytest.mark.skip(reason="Not implemented yet.")
@pytest.mark.network()
def test_fill_academic_activities_data():
    user = Database().load_hard_coded_user_data()
    network = Network(user)
    assert user, "Don't have user data to check."
    assert network.check_connection(), "Can't connect to the server."

    campus_names = network.extract_campus_names()
    assert campus_names, "Can't extract campus names from the server."

    course = utils.get_course_data_test()
    campus_name = utils.get_campus_name_test()

    academic_activities, missings = network.extract_academic_activities_data(campus_name, [course])
    missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)

    assert not missings, "The following courses don't have activities: " + ", ".join(missings)
    assert not missing_meetings_data and academic_activities, "Can't extract academic activities from the server."
