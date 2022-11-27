import pytest
import utils

from collector.db.db import Database
from collector.network.network import NetworkHttp
from csp import csp


@pytest.mark.network()
@pytest.mark.network_http()
class TestController:

    run_in_background = True

    def test_flow_without_gui_without_database(self):

        campus_name = utils.get_campus_name_test()
        user = Database().load_hard_coded_user_data()
        network = NetworkHttp(user)
        assert user, "Don't have user data to check."

        assert network.check_connection(), "Can't connect to the server."

        campus_names = network.extract_campus_names()
        assert campus_names, "Can't extract campus names from the server."

        assert campus_name in campus_names, "Some campus names are missing."

        courses = network.extract_all_courses(campus_name)
        assert courses, "Can't extract courses from the server."

        course = utils.get_course_data_test()
        assert course in courses, "Some courses are missing."

        academic_activities, missing_courses_names = network.extract_academic_activities_data(campus_name, [course])
        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)
        assert not missing_courses_names, "The following courses don't have activities: " + ", ".join(
            missing_courses_names)

        assert not missing_meetings_data, "Can't extract academic activities from the server."
        schedules = csp.extract_schedules(academic_activities)
        assert schedules, "At least one schedule should be extracted."

    def test_flow_without_gui_with_database(self):

        database = Database()
        campus_name = "מכון לב"
        user = database.load_hard_coded_user_data()
        network = NetworkHttp(user)
        assert user, "Don't have user data to check."

        assert network.check_connection(), "Can't connect to the server."

        campus_names = database.load_campus_names()
        if not campus_names:
            campus_names = network.extract_campus_names()
            assert campus_names, "Can't extract campus names from the server."
            assert campus_name in campus_names, "Some campus names are missing."
            database.save_campus_names(campus_names)

        courses = database.load_courses_data()
        course = utils.get_course_data_test()
        campus_name = utils.get_campus_name_test()
        if not courses:
            courses = network.extract_all_courses(campus_name)

            assert courses, "Can't extract courses from the server."
            assert course in courses, "Some courses are missing."
            database.save_courses_data(courses)

        academic_activities = database.load_academic_activities_data(campus_name, [course])

        if not academic_activities:
            academic_activities, missings = network.extract_academic_activities_data(campus_name, [course])
            assert not missings, "The following courses don't have activities: " + ", ".join(missings)

        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)
        assert not missing_meetings_data, "Can't extract academic activities from the server."

        schedules = csp.extract_schedules(academic_activities)
        assert schedules, "At least one schedule should be extracted."

        assert campus_names, "Don't have campus names to check."

        assert campus_name in campus_names, "Some campus names are missing."
